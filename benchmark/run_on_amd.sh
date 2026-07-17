#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lemonade-Sec · benchmark on a REAL AMD GPU (MI300X / Radeon)
# Paste into a terminal in an AMD AI Notebook. Handles PEP-668, uses the real
# Lemonade CLI (`lemonade`, port 13305, ROCm backend) and is self-diagnosing:
# it prints `lemonade --help` so the exact serve/pull syntax is visible even if
# a step fails. Copy the WHOLE output back.
# ─────────────────────────────────────────────────────────────────────────────
set +e
PORT="${PORT:-13305}"                                # Lemonade default
BASE="http://localhost:${PORT}/api/v1"
MODEL="${MODEL:-Qwen3.5-4B-GGUF}"                     # small GGUF from the Lemonade registry
WORK="${WORK:-$HOME/lemonade-bench}"
PIP="python3 -m pip install --break-system-packages -q"

echo "════════ [0] environment / GPU ════════"
python3 --version
rocm-smi --showproductname 2>/dev/null | grep -i 'Card Series' || echo "no rocm-smi"
export BENCH_GPU="$(rocm-smi --showproductname 2>/dev/null | grep -i 'Card Series' | head -1 | cut -d: -f2- | xargs)"
echo "detected GPU: ${BENCH_GPU:-unknown}"

echo "════════ [1] install lemonade-sdk + matplotlib (PEP-668 override) ════════"
$PIP --upgrade pip 2>&1 | tail -1
$PIP lemonade-sdk matplotlib 2>&1 | tail -8
hash -r 2>/dev/null
echo "lemonade on PATH? -> $(command -v lemonade || echo NO)"
echo "── lemonade --help (subcommands; paste back) ──"
lemonade --help 2>&1 | head -40
echo "── lemonade --version ──"; lemonade --version 2>&1 | head -2

echo "════════ [2] install ROCm llama.cpp backend (for gfx942) ════════"
timeout 420 lemonade backends install llamacpp:rocm --force 2>&1 | tail -12
echo "── available models (lemonade list) ──"
lemonade list 2>&1 | head -30

echo "════════ [3] clone / update Lemonade-Sec ════════"
mkdir -p "$WORK" && cd "$WORK"
[ -d lemonade-sec ] || git clone -q https://github.com/SRKRZ23/lemonade-sec.git
git -C lemonade-sec pull -q 2>/dev/null
cd lemonade-sec && echo "at $(pwd)"

echo "════════ [4] start the server (port $PORT) ════════"
echo "── lemonade serve --help (paste back if serve fails) ──"
lemonade serve --help 2>&1 | head -20
# start in background; try `lemonade serve`, fall back to `lemonade-server serve`
( lemonade serve --port "$PORT" >"$WORK/lemonade.log" 2>&1 || \
  lemonade-server serve --port "$PORT" >>"$WORK/lemonade.log" 2>&1 ) &
echo "waiting for $BASE/models (up to 240s; first model load can be slow) ..."
UP=""
for i in $(seq 1 120); do
  curl -s "$BASE/models" >/dev/null 2>&1 && { UP=1; echo "server up after $((i*2))s"; break; }
  sleep 2
done
if [ -z "$UP" ]; then
  echo "⛔ server not up on $PORT — log tail (paste back):"; tail -30 "$WORK/lemonade.log"
  echo "   (also paste the 'lemonade --help' + 'lemonade serve --help' above so I can pin the syntax.)"
  exit 1
fi
echo "── /models says: ──"; curl -s "$BASE/models" | head -c 500; echo

echo "════════ [5] REAL triage report (credibility screenshot) ════════"
python3 lemonade_sec.py samples --triage --lemonade-url "$BASE" \
  --out "$WORK/amd_triage_report.md" --json "$WORK/amd_findings.json"
grep -A3 "AI triage" "$WORK/amd_triage_report.md" | head -8

echo "════════ [6] BENCHMARK (throughput / latency / scan) ════════"
python3 benchmark/amd_bench.py --url "$BASE" --samples samples \
  --out "$WORK/amd_bench_results.json" --chart

echo ""; echo "════════ DONE ════════"
echo "Artifacts in $WORK: amd_triage_report.md · amd_bench_results.json · amd_bench_results.png"
echo "📸 Screenshot the triage report + chart, paste amd_bench_results.json back."
