# Adaptive Telemetry for Cloud-Hosted IoT Digital Twins

Cloud Computing 100-Day Research Assignment — Group 21
Muhammad Awwab Aamir (22i-0971) · Rayyan Khan (22i-1002)

**Research question:** Under a fixed twin-freshness and fidelity budget, can latency-aware adaptive (deadband-based) telemetry at the edge reduce cloud ingestion bytes, message count and p95 ingestion latency compared with fixed-rate streaming and windowed state-of-the-art compression, while keeping digital-twin RMSE within budget?

## Repository layout
| Path | Contents |
|---|---|
| `reproduction/` | Reproduction of the base article (Mix-Piece, VLDB Journal 2024) and the batching-window / deadband gap experiment — code, raw results, figures. See `reproduction/README.md`. |
| `framework/` | Proposed framework (components A and B), trace-driven edge→cloud emulator, baselines, ablation, results and figures. See `framework/README.md`. |
| `live/` | Live testbed (50 MQTT devices → Mosquitto → ingestion → SQLite twin) used to validate the emulator. See `live/README.md`. |
| `reports/` | Submitted reports (base-article reproduction and research-gap report). |

## Base article
X. Kitsios, P. Liakos, K. Papakonstantinopoulou, Y. Kotidis, "Flexible grouping of linear segments for highly accurate lossy compression of time series data," *The VLDB Journal*, 33(5), 2024. Official code: https://github.com/xkitsios/Sim-Piece (Apache-2.0). Datasets are those bundled in the official repository.

## License
MIT for code in this repository. The base article's code is not redistributed here; it is cloned from the official repository at build time.
