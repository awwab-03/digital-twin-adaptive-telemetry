"""Edge telemetry policies and a trace-driven edge->cloud digital-twin emulator.

Every policy consumes a sampled signal x[0..n-1] (one sample per tick) and emits
*updates*. Each update carries (tick, value[, slope]). Updates are packed into
*messages* (one per update, or several when micro-batching is enabled). The twin
applies a message when it arrives and, between messages, predicts the state with
the model of the last applied update (zero-order hold or linear extrapolation).
"""
import numpy as np
from numba import njit

# ---- wire format (bytes) --------------------------------------------------
TS_B, VAL_B, SLOPE_B, FLAG_B = 4, 4, 4, 1   # timestamp, float32 value, float32 slope, model flag
CNT_B = 2                                  # entry count in a batched message
MQTT_OVH = 19   # MQTT 3.1.1 PUBLISH QoS0: 2B fixed header + 2B topic length + 15B topic "dt/dev01/sensor"

@njit(cache=True)
def deadband_zoh(x, eps, hb):
    """Fixed send-on-delta (deadband) with zero-order hold + heartbeat every hb ticks.
    returns update ticks, values, slopes(=0), model(0)"""
    n = x.shape[0]
    t = np.empty(n, np.int64); v = np.empty(n); s = np.zeros(n); m = np.zeros(n, np.int8)
    k = 0; last = x[0]; lt = 0
    t[0] = 0; v[0] = x[0]; k = 1
    for i in range(1, n):
        if abs(x[i] - last) > eps or i - lt >= hb:
            last = x[i]; lt = i; t[k] = i; v[k] = x[i]; k += 1
    return t[:k], v[:k], s[:k], m[:k]

@njit(cache=True)
def _ls_slope(x, i, w):
    # least-squares slope over x[i-w+1..i]
    a = i - w + 1
    if a < 0:
        a = 0
    L = i - a + 1
    if L < 2:
        return 0.0
    mt = (L - 1) / 2.0
    mx = 0.0
    for j in range(L):
        mx += x[a + j]
    mx /= L
    num = 0.0; den = 0.0
    for j in range(L):
        num += (j - mt) * (x[a + j] - mx); den += (j - mt) * (j - mt)
    return num / den

@njit(cache=True)
def adaptive_predictive(x, eps, hb, w):
    """Component A: adaptive dual-prediction deadband.
    Edge and twin share a predictor. At each update the edge selects the model
    (0 = hold, 1 = linear with LS slope over the last w samples) whose back-cast over
    the last w samples has the smaller maximum residual; the twin extrapolates with it.
    A new update is sent only when |x - prediction| > eps (or heartbeat)."""
    n = x.shape[0]
    t = np.empty(n, np.int64); v = np.empty(n); s = np.empty(n); m = np.empty(n, np.int8)
    k = 0
    def_choose = 0
    # first update: hold
    t[0] = 0; v[0] = x[0]; s[0] = 0.0; m[0] = 0; k = 1
    bv = x[0]; bs = 0.0; bt = 0
    for i in range(1, n):
        pred = bv + bs * (i - bt)
        if abs(x[i] - pred) > eps or i - bt >= hb:
            sl = _ls_slope(x, i, w)
            a = i - w + 1
            if a < 0:
                a = 0
            r0 = 0.0; r1 = 0.0
            for j in range(a, i + 1):
                e0 = abs(x[j] - x[i]); e1 = abs(x[j] - (x[i] + sl * (j - i)))
                if e0 > r0: r0 = e0
                if e1 > r1: r1 = e1
            if r1 < r0:
                bs = sl; mm = 1
            else:
                bs = 0.0; mm = 0
            bv = x[i]; bt = i
            t[k] = i; v[k] = x[i]; s[k] = bs; m[k] = mm; k += 1
    return t[:k], v[:k], s[:k], m[:k]

@njit(cache=True)
def entry_bytes(m, with_flag):
    # value + timestamp (+ flag byte and slope when the adaptive model is used)
    b = TS_B + VAL_B
    if with_flag:
        b += FLAG_B
        if m == 1:
            b += SLOPE_B
    return b

@njit(cache=True)
def pack(t, m, D, with_flag, max_payload):
    """Component B: deadline-bounded micro-batching.
    Updates are buffered; the buffer is flushed when the oldest buffered update
    reaches age D ticks (strict freshness bound) or the payload would exceed max_payload.
    D = 0 -> every update is its own message. Returns per-update arrival tick and
    message payload sizes."""
    k = t.shape[0]
    arr = np.empty(k, np.int64)
    sizes = np.empty(k, np.int64); nm = 0
    if D == 0:
        for i in range(k):
            arr[i] = t[i]; sizes[nm] = entry_bytes(m[i], with_flag); nm += 1
        return arr, sizes[:nm]
    start = 0; first_t = t[0]; pay = CNT_B + entry_bytes(m[0], with_flag)
    for i in range(1, k + 1):
        flush_time = first_t + D
        if i == k or t[i] >= flush_time or pay + entry_bytes(m[i], with_flag) > max_payload:
            # flush at deadline, or right when the next update would overflow the buffer
            if i < k and t[i] < flush_time:
                ft = t[i]
            else:
                ft = flush_time
            for j in range(start, i):
                arr[j] = ft
            sizes[nm] = pay; nm += 1
            if i < k:
                start = i; first_t = t[i]; pay = CNT_B + entry_bytes(m[i], with_flag)
        else:
            pay += entry_bytes(m[i], with_flag)
    return arr, sizes[:nm]

@njit(cache=True)
def twin_view(x, t, v, s, arr):
    """Real-time twin state y[tau] using only updates that have arrived by tick tau.
    Updates are applied in order at their arrival tick; between them the twin extrapolates
    with the latest applied update's model. Also returns the retrospective reconstruction
    (all updates known), used to check the error bound."""
    n = x.shape[0]; k = t.shape[0]
    y = np.empty(n); r = np.empty(n)
    j = 0   # next update to apply (real time)
    cv = v[0]; cs = 0.0; ct = 0
    started = False
    for tau in range(n):
        while j < k and arr[j] <= tau:
            cv = v[j]; cs = s[j]; ct = t[j]; j += 1; started = True
        y[tau] = cv + cs * (tau - ct) if started else v[0]
    # retrospective
    j = 0
    for tau in range(n):
        while j + 1 < k and t[j + 1] <= tau:
            j += 1
        r[tau] = v[j] + s[j] * (tau - t[j])
    return y, r

@njit(cache=True)
def adaptive_shadow(x, eps, hb, w, alpha):
    """Component A (final): adaptive dual-prediction deadband with shadow-model selection.
    After every update the edge launches two *shadow* predictors from the same point:
    model 0 = hold, model 1 = linear (LS slope over the last w samples). It tracks how many
    ticks each shadow stays within eps. Their lifetimes (censored at the next update) feed an
    EWMA per model (weight alpha). At each update the edge picks the model with the larger
    expected lifetime per transmitted byte; the twin extrapolates with the chosen model."""
    n = x.shape[0]
    t = np.empty(n, np.int64); v = np.empty(n); s = np.empty(n); m = np.empty(n, np.int8)
    b0 = float(TS_B + VAL_B + FLAG_B); b1 = b0 + SLOPE_B
    life0 = 1.0; life1 = 1.0
    t[0] = 0; v[0] = x[0]; s[0] = 0.0; m[0] = 0; k = 1
    bv = x[0]; bs = 0.0; bt = 0
    sh_sl = 0.0; a0 = True; a1 = True
    for i in range(1, n):
        el = i - bt
        if a0 and abs(x[i] - bv) > eps:
            a0 = False; life0 = (1 - alpha) * life0 + alpha * el
        if a1 and abs(x[i] - (bv + sh_sl * el)) > eps:
            a1 = False; life1 = (1 - alpha) * life1 + alpha * el
        pred = bv + bs * el
        if abs(x[i] - pred) > eps or el >= hb:
            # censor shadows still alive (their lifetime is at least el)
            if a0:
                life0 = (1 - alpha) * life0 + alpha * el
            if a1:
                life1 = (1 - alpha) * life1 + alpha * el
            sl = _ls_slope(x, i, w)
            if life1 / b1 > life0 / b0:
                bs = sl; mm = 1
            else:
                bs = 0.0; mm = 0
            bv = x[i]; bt = i; sh_sl = sl; a0 = True; a1 = True
            t[k] = i; v[k] = x[i]; s[k] = bs; m[k] = mm; k += 1
    return t[:k], v[:k], s[:k], m[:k]

# ---- final components (used in the article) -------------------------------
@njit(cache=True)
def varint_len(u):
    b = 1
    while u >= 128:
        u >>= 7; b += 1
    return b

@njit(cache=True)
def zigzag(z):
    return (z << 1) if z >= 0 else ((-z) << 1) - 1

@njit(cache=True)
def deadband_quantized(x, eps, q, hb):
    """Component A: error-budget-split quantized delta deadband (QDD).
    The error budget eps is split between the trigger threshold (eps - q/2) and value
    quantisation (q/2), so |x - twin| <= eps always holds. A triggered value is snapped to the
    grid q*Z and sent as a zig-zag varint of the grid-index difference plus a varint tick delta.
    Heartbeats (every hb ticks) and the first update are sent in absolute form (4B tick + 4B value)
    so a receiver can resynchronise. Returns ticks, values, slopes(0), per-update entry bytes."""
    n = x.shape[0]
    thr = eps - q / 2.0
    t = np.empty(n, np.int64); v = np.empty(n); eb = np.empty(n, np.int64)
    qi = np.int64(np.round(x[0] / q)); last = qi * q
    t[0] = 0; v[0] = last; eb[0] = TS_B + VAL_B + FLAG_B; k = 1; lt = 0
    for i in range(1, n):
        hbeat = (i - lt) >= hb
        if abs(x[i] - last) > thr or hbeat:
            ni = np.int64(np.round(x[i] / q))
            if hbeat:
                eb[k] = TS_B + VAL_B + FLAG_B
            else:
                eb[k] = varint_len(zigzag(ni - qi)) + varint_len(i - lt)
            qi = ni; last = qi * q; lt = i
            t[k] = i; v[k] = last; k += 1
    return t[:k], v[:k], np.zeros(k), eb[:k]

@njit(cache=True)
def pack_sizes(t, eb, D, max_payload):
    """Component B: deadline-bounded micro-batching on per-update entry sizes eb.
    Flush when the oldest buffered update reaches age D ticks or the payload cap is hit.
    D == 0: one message per update (no count header)."""
    k = t.shape[0]
    arr = np.empty(k, np.int64); sizes = np.empty(k, np.int64); nm = 0
    if D == 0:
        for i in range(k):
            arr[i] = t[i]; sizes[nm] = eb[i]; nm += 1
        return arr, sizes[:nm]
    start = 0; first_t = t[0]; pay = CNT_B + eb[0]
    for i in range(1, k + 1):
        flush_time = first_t + D
        if i == k or t[i] >= flush_time or pay + eb[i] > max_payload:
            ft = t[i] if (i < k and t[i] < flush_time) else flush_time
            for j in range(start, i):
                arr[j] = ft
            sizes[nm] = pay; nm += 1
            if i < k:
                start = i; first_t = t[i]; pay = CNT_B + eb[i]
        else:
            pay += eb[i]
    return arr, sizes[:nm]
