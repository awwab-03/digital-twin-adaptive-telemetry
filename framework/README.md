# Freshness-bounded telemetry for cloud digital twins (proposed framework)

Trace-driven edge→cloud emulator and the proposed telemetry framework:

* **Component A – error-budget-split quantized delta deadband** (`edge.deadband_quantized`): trigger at ε−q/2, snap to grid q, send zig-zag varint deltas; guarantees |x − twin| ≤ ε.
* **Component B – deadline-bounded micro-batching** (`edge.pack_sizes`): flush when the oldest buffered update reaches age D (or 5 KB cap); guarantees update delay ≤ D.
* Baselines: fixed-rate streaming, send-on-delta deadband, windowed **Mix-Piece** (base article, VLDB J. 2024), and a dual-prediction variant (negative result).

## Reproduce (≈15 min on 2 vCPUs)
```bash
# 1. base-article code, pinned to the commit used in the paper
git clone https://github.com/xkitsios/Sim-Piece.git && git -C Sim-Piece checkout f4e875c
mkdir -p build data mp && cp Sim-Piece/src/test/resources/*.gz data/
javac -d build $(find ../reproduction/shim Sim-Piece/src/main Sim-Piece/src/test/java/io/github/xkitsios/util -name "*.java") java/WinRun.java
# 2. windowed Mix-Piece payloads (base article under a freshness budget)
java -Xmx5g -cp build WinRun data mp Cricket,FaceFour,Lightning,MoteStrain,Wafer,WindSpeed,WindDirection 1,2.5,5 32,128,512
java -Xmx5g -cp build WinRun data mp Pressure,BTCUSD,ETHUSD,SPX,STOXX50E 0.1,0.25,0.5 32,128,512
# 3. all schemes, ablation, sensitivity (writes results_all.csv)
pip install -r requirements.txt
python3 run_all.py data mp results/results_all.csv
python3 analyze.py   # summary tables + bootstrap CIs (run inside results/ or adjust paths)
python3 figs.py      # figures used in the article
```
All algorithms are deterministic, so step 3 reproduces `results/results_all.csv` exactly (edge timing columns vary with hardware).
`../reproduction/shim` replaces zstd-jni (Maven Central was unreachable); `run_all.py` applies real zstd level 3 to the exact payloads.
