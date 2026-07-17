#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lemonade-Sec · one-shot benchmark on a REAL AMD GPU
# Paste into a terminal in an AMD AI Notebook (notebooks.amd.com, MI300X/Radeon).
# Robust to PEP-668 (externally-managed Python) and self-diagnosing: if a step
# can't complete it prints exactly what it found so the CLI can be pinned. Copy the
# whole output back.
# ─────────────────────────────────────────────────────────────────────────────
set +e
MODEL="${MODEL:-}"                                  # empty → let the script discover one
PORT="${PORT:-8000}"
BASE="http://localhost:${PORT}/api/v1"
WORK="${WORK:-$HOME/lemonade-bench}"
PIP="python3 -m pip install --break-system-packages -q"   # PEP-668 override (root container)

echo "════════ [0] environment / GPU ════════"
python3 --version
(command -v rocm-smi >/dev/null && rocm-smi --showproductname) || echo "no rocm-smi"
export BENCH_GPU="$(rocm-smi --showproductname 2>/dev/null | grep -i 'Card Series' | head -1 | cut -d: -f2- | xargs)"
echo "detected GPU: ${BENCH_GPU:-unknown}"

echo "════════ [1] install Lemonade + matplotlib (PEP-668 override) ════════"
$PIP --upgrade pip 2>&1 | tail -1
$PIP lemonade-sdk matplotlib 2>&1 | tail -6
hash -r 2>/dev/null
# resolve the server entrypoint across possible names
SERVE=""
for c in lemonade-server lemonade-server-dev; do command -v "$c" >/dev/null && SERVE="$c" && break; done
[ -z "$SERVE" ] && python3 -c "import lemonade_server" 2>/dev/null && SERVE="python3 -m lemonade_server"
echo "server entrypoint: ${SERVE:-NOT FOUND}"
if [ -z "$SERVE" ]; then
  echo "── DIAGNOSTICS (paste this back) ──"
  pip show lemonade-sdk 2>/dev/null | grep -E 'Name|Version|Location'
  python3 - <<'PY'
import importlib,glob,sys
for m in ("lemonade","lemonade_server","lemonade_sdk"):
    try: importlib.import_module(m); print("import OK:", m)
    except Exception as e: print("import FAIL:", m, "-", type(e).__name__)
import site,os
for d in set(site.getsitepackages()+[site.getusersitepackages()]):
    b=os.path.join(os.path.dirname(os.path.dirname(d)),"bin")
    hits=[x for x in glob.glob(b+"/*") if "lemon" in x.lower()]
    if hits: print("bin:",hits)
PY
  echo "⛔ Lemonade server not found after install — send the diagnostics above."
  exit 1
fi
echo "── lemonade help / available models (for pinning the CLI) ──"
$SERVE --help 2>&1 | head -25
$SERVE list 2>&1 | head -30

echo "════════ [2] clone / update Lemonade-Sec ════════"
mkdir -p "$WORK" && cd "$WORK"
[ -d lemonade-sec ] || git clone -q https://github.com/SRKRZ23/lemonade-sec.git
git -C lemonade-sec pull -q 2>/dev/null
cd lemonade-sec && echo "at $(pwd)"

echo "════════ [3] pull model + start server ════════"
# pick a model: use $MODEL if set, else the first from `list`, else a common coder GGUF
if [ -z "$MODEL" ]; then
  MODEL="$($SERVE list 2>/dev/null | grep -ioE '[A-Za-z0-9._-]*(Qwen|Coder|Llama|Instruct)[A-Za-z0-9._-]*' | head -1)"
fi
MODEL="${MODEL:-Qwen2.5-Coder-7B-Instruct-GGUF}"
echo "using MODEL=$MODEL"
$SERVE pull "$MODEL" 2>&1 | tail -6
nohup $SERVE serve --port "$PORT" > "$WORK/lemonade.log" 2>&1 &
[ $? -ne 0 ] && nohup $SERVE serve > "$WORK/lemonade.log" 2>&1 &
echo "waiting for $BASE/models (up to 180s) ..."
UP=""
for i in $(seq 1 90); do
  curl -s "$BASE/models" >/dev/null 2>&1 && { UP=1; echo "server up after $((i*2))s"; break; }
  sleep 2
done
if [ -z "$UP" ]; then
  echo "⛔ server did not come up — last log lines (paste back):"; tail -25 "$WORK/lemonade.log"; exit 1
fi
curl -s "$BASE/models" | head -c 400; echo

echo "════════ [4] REAL triage report (credibility screenshot) ════════"
python3 lemonade_sec.py samples --triage --lemonade-url "$BASE" --model "$MODEL" \
  --out "$WORK/amd_triage_report.md" --json "$WORK/amd_findings.json"
grep -A3 "AI triage" "$WORK/amd_triage_report.md" | head -8

echo "════════ [5] BENCHMARK (throughput / latency / scan) ════════"
python3 benchmark/amd_bench.py --url "$BASE" --model "$MODEL" --samples samples \
  --out "$WORK/amd_bench_results.json" --chart

echo ""; echo "════════ DONE ════════"
echo "Artifacts in $WORK: amd_triage_report.md · amd_bench_results.json · amd_bench_results.png"
echo "📸 Screenshot the triage report + chart, and paste amd_bench_results.json back."
