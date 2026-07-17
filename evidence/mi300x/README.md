# MI300X benchmark evidence

Raw, unedited output collected directly on the AMD notebook (`notebooks.amd.com`, AAI
DevZone → "Unsloth on AMD Instinct MI300X") while running the benchmark in
[`benchmark/amd_native_bench.sh`](../../benchmark/amd_native_bench.sh). This backs the
numbers quoted in the [README](../../README.md) and [deck](../../deck/).

## Contents

| Bundle | Collected (UTC) | What it captures |
|---|---|---|
| `evidence_mi300x_20260717T144656Z/` | 2026-07-17 14:46:56 | Full run: GPU/ROCm/env details + the actual `huggingface-bench` output (64.285 tok/s, 13,779 tok/s prefill, 19ms TTFT on Qwen2.5-Coder-1.5B) + the local-model triage answer |
| `evidence_mi300x_20260717T145314Z/` | 2026-07-17 14:53:14 | A live GPU telemetry snapshot (rocm-smi concise: 49.0°C, 149W, 0% util at idle) taken a few minutes later, same node |

Each folder also has a `.tar.gz` of itself alongside it (as originally downloaded from the
node) for archival/integrity purposes.

## Files inside each bundle

- `00_PROVENANCE.txt` — UTC/local timestamp, hostname, kernel, source, repo commit
- `01_rocm-smi.txt`, `02_gpu_details.txt`, `03_rocminfo_head.txt`, `04_rocm_version.txt` — hardware identification (confirms **AMD Instinct MI300X VF**, gfx942)
- `05_env.txt` — Python/torch/lemonade-sdk/transformers versions
- `10_benchmark_throughput.txt` — raw `lemonade huggingface-bench` output (only in the first bundle)
- `11_triage_answer.txt` — raw local-model response to the security-triage prompt (only in the first bundle)
- `99_SHA256SUMS.txt` — checksums of the other files in the same bundle, generated on the node before download (the checksum-manifest's own line always shows as "FAILED" when re-verifying — a file can't contain a hash of itself, that's expected, not a tamper signal)

## Verify

```bash
cd evidence_mi300x_20260717T144656Z && sha256sum -c 99_SHA256SUMS.txt
```
All entries except the manifest's own line should read `OK`.
