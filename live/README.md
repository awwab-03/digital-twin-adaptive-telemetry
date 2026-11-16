# Live testbed: devices → Mosquitto → ingestion → SQLite twin

Real end-to-end check of the schemes evaluated in `../framework`.

* 50 simulated devices, one MQTT connection each, replay 60 s segments (3,000 samples) of Cricket, Wafer, WindSpeed, Pressure and SPX at 50 Hz (`common.make_devices`, seed 7, segments in `results/devices.json`).
* Mosquitto 2.0.18 broker (fresh instance per run); broker counters read from `$SYS`.
* `ingest.py` decodes every message and commits it to SQLite (WAL, one transaction per message); latency = database commit time − sampling instant.
* Schemes: FR, DB, A, DB+B (D = 0.64 s), A+B (D = 0.64 s), MP (Mix-Piece W = 32, payloads from `../framework` step 2). Three repeats each.

## Run
```bash
sudo apt-get install mosquitto          # 2.0.18 used in the paper
pip install paho-mqtt psutil numpy pandas zstandard
# needs ../framework/data/*.npy (created by run_all.py) and the Mix-Piece payloads (mp/) – edit paths in common.py
./run_all_live.sh                        # ≈25 min, writes res/
python3 analyze_live.py                  # live_runs.csv, live_summary.csv (first 2 s excluded from latency)
python3 fig_live.py
```
Message and byte counts are deterministic and identical across repeats; latency and CPU vary slightly with the host.
