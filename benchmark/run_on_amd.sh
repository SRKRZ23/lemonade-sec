#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lemonade-Sec · one-shot benchmark on a REAL AMD GPU
# Paste this whole thing into a cell/terminal in an AMD AI Notebook
# (notebooks.amd.com → "AAI Developer Zone" or "ROCm Certification", Radeon/Instinct GPU).
#
# It: probes the GPU → installs Lemonade → pulls a small coder model → starts the
# local server → clones Lemonade-Sec → runs a REAL local-LLM triage + measures
# throughput / latency / scan speed → drops a MEASURED results JSON + chart + report.
#
# If a step fails, copy the output back — the model name / serve flags vary by
# Lemonade version and are easy to adjust (see the CONFIG block).
# ─────────────────────────────────────────────────────────────────────────────
set +e
# ── CONFIG (adjust if your Lemonade version differs) ─────────────────────────
MODEL="${MODEL:-Qwen2.5-Coder-7B-Instruct-GGUF}"   # `lemonade-server list` to see options
PORT="${PORT:-8000}"
BASE="http://localhost:${PORT}/api/v1"
WORK="${WORK:-$HOME/lemonade-bench}"

echo "════════ [0] environment / GPU ════════"
python3 --version
(command -v rocm-smi >/dev/null && rocm-smi --showproductname) || \
(command -v rocminfo >/dev/null && rocminfo | grep -m1 -i "Marketing Name") || echo "no rocm-smi/rocminfo on PATH"
export BENCH_GPU="$(rocm-smi --showproductname 2>/dev/null | grep -i 'Card Series' | head -1 | cut -d: -f2- | xargs)"
echo "detected GPU: ${BENCH_GPU:-unknown}"

echo "════════ [1] install Lemonade + matplotlib ════════"
pip install -q --upgrade lemonade-sdk matplotlib 2>&1 | tail -3
command -v lemonade-server >/dev/null && echo "lemonade-server OK" || \
  echo "⚠️ lemonade-server not on PATH — check the 'Run Lemonade' docs at lemonade-server.ai/docs"

echo "════════ [2] clone Lemonade-Sec ════════"
mkdir -p "$WORK" && cd "$WORK"
[ -d lemonade-sec ] || git clone -q https://github.com/SRKRZ23/lemonade-sec.git
cd lemonade-sec && echo "at $(pwd)"

echo "════════ [3] pull model + start server ════════"
lemonade-server pull "$MODEL" 2>&1 | tail -4
# start the server in the background
nohup lemonade-server serve --port "$PORT" > "$WORK/lemonade.log" 2>&1 &
echo "waiting for $BASE/models ..."
for i in $(seq 1 60); do
  curl -s "$BASE/models" >/dev/null 2>&1 && { echo "server up after ${i}s"; break; }
  sleep 2
done
curl -s "$BASE/models" | head -c 300; echo

echo "════════ [4] REAL triage report (credibility screenshot) ════════"
python3 lemonade_sec.py samples --triage --lemonade-url "$BASE" --model "$MODEL" \
  --out "$WORK/amd_triage_report.md" --json "$WORK/amd_findings.json"
echo "---- first finding with a REAL local-model verdict ----"
grep -A3 "AI triage" "$WORK/amd_triage_report.md" | head -8

echo "════════ [5] BENCHMARK (throughput / latency / scan) ════════"
python3 benchmark/amd_bench.py --url "$BASE" --model "$MODEL" --samples samples \
  --out "$WORK/amd_bench_results.json" --chart

echo ""
echo "════════ DONE ════════"
echo "Artifacts in $WORK:"
echo "  • amd_triage_report.md    (report with source: lemonade:$MODEL  ← the screenshot)"
echo "  • amd_bench_results.json  (MEASURED throughput/latency/scan)"
echo "  • amd_bench_results.png   (MEASURED chart)"
echo "📸 Screenshot the triage report + the chart, and paste amd_bench_results.json back."
