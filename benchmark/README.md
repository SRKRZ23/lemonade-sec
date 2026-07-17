# Lemonade-Sec · benchmarks on real AMD hardware

Measured performance of the local-AI triage pipeline on an **AMD GPU**, via a running
[Lemonade](https://lemonade-server.ai) server.

## What it measures (all MEASURED, on-device)
| Metric | Meaning |
|---|---|
| **Throughput** | tokens/sec the triage model generates on the GPU |
| **Triage latency** | seconds per finding for the real local-LLM security triage |
| **Scan speed** | SAST files/sec + findings (no network) |

## Run it on a free AMD GPU (AMD AI Notebooks)

1. Go to **[notebooks.amd.com](https://notebooks.amd.com)** → open **AAI Developer Zone**
   or **ROCm Certification** (Radeon/Instinct GPU). (Requires AMD Developer Program.)
2. In a terminal / notebook cell, paste and run:
   ```bash
   bash <(curl -s https://raw.githubusercontent.com/SRKRZ23/lemonade-sec/main/benchmark/run_on_amd.sh)
   ```
   or clone first and run `bash benchmark/run_on_amd.sh`.
3. It installs Lemonade, pulls a coder model, starts the server, runs a **real** triage
   report + the benchmark, and writes `amd_bench_results.json` + `amd_bench_results.png`.

> Model name / serve flags vary by Lemonade version — adjust the `CONFIG` block at the top
> of `run_on_amd.sh` (`lemonade-server list` shows available models).

## Test the harness without a GPU (mock)

```bash
python3 benchmark/mock_lemonade.py 8000 &                 # canned OpenAI-compatible server
python3 benchmark/amd_bench.py --url http://localhost:8000/api/v1 --samples ../samples --chart
```
The mock returns fake tokens/verdicts so you can verify the harness end-to-end — the
numbers are **not** real (the GPU field will say MOCK). Real numbers come from a real
Lemonade server on real hardware.

## Output

`amd_bench_results.json` (example shape):
```json
{ "measured": true, "model": "...", "hardware": {"gpu": "AMD Radeon ..."},
  "throughput": {"tok_per_sec": 0.0}, "triage": {"sec_per_finding": 0.0}, "scan": {...} }
```
Paste that JSON back and the numbers get recorded (measured, dated) — never modeled.
