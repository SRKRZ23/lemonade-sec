#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lemonade-Sec · NATIVE benchmark for `lemonade` v9.x (turnkeyml tools CLI) on AMD
# Correct syntax (learned from the CLI): tools are POSITIONAL (no --tools), e.g.
#   lemonade -i <ckpt> huggingface-load --device cuda huggingface-bench -p 256 ...
# huggingface-load needs torch; the notebook's torch+ROCm lives in a conda env, so
# we locate that Python and run lemonade from it. Falls back to llama.cpp (no torch).
# Paste the WHOLE output back.
# ─────────────────────────────────────────────────────────────────────────────
set +e
MODEL="${MODEL:-Qwen/Qwen2.5-Coder-1.5B-Instruct}"
WORK="${WORK:-$HOME/lemonade-bench}"; mkdir -p "$WORK"

echo "════════ [0] GPU ════════"
rocm-smi --showproductname 2>/dev/null | grep -i 'Card Series'

echo "════════ [1] find a Python with torch + GPU (ROCm) ════════"
CANDS="$(command -v python3) $(command -v python) /opt/conda/bin/python"
for p in /opt/conda/envs/*/bin/python /opt/*/bin/python /usr/local/bin/python3; do CANDS="$CANDS $p"; done
TORCH_PY=""
for py in $CANDS; do
  [ -x "$py" ] || continue
  info=$("$py" -c 'import torch;print(torch.__version__, torch.cuda.is_available(), getattr(torch.version,"hip","no"))' 2>/dev/null)
  [ -n "$info" ] && echo "  $py -> torch $info"
  if [ -z "$TORCH_PY" ] && echo "$info" | grep -q " True "; then TORCH_PY="$py"; fi
done
echo "chosen torch+GPU python: ${TORCH_PY:-NONE}"

if [ -z "$TORCH_PY" ]; then
  echo "⚠️ no torch+GPU python found — envs present:"
  ls -d /opt/conda/envs/* 2>/dev/null; conda env list 2>/dev/null | head
  echo "──── FALLBACK: llama.cpp bench (GGUF, no torch) ────"
  lemonade -i "$MODEL" llamacpp-load llamacpp-bench 2>&1 | tee "$WORK/native_bench.txt" | tail -40
  echo "DONE (fallback). Paste output; if llamacpp needs a GGUF path I'll pin it."
  exit 0
fi

# use / install lemonade in that env
LM="$(dirname "$TORCH_PY")/lemonade"
if [ ! -x "$LM" ]; then
  echo "installing lemonade-sdk into the torch env ..."
  "$TORCH_PY" -m pip install -q lemonade-sdk 2>&1 | tail -4
fi
[ -x "$LM" ] || LM="lemonade"
echo "using lemonade: $LM"

echo "════════ [2] REAL throughput benchmark on MI300X (float16, --device cuda) ════════"
echo "model: $MODEL"
"$LM" -i "$MODEL" \
  huggingface-load --device cuda --dtype float16 \
  huggingface-bench --prompts 256 --output-tokens 128 --iterations 5 --warmup-iterations 2 \
  2>&1 | tee "$WORK/native_bench.txt" | tail -50

echo "════════ [3] REAL security-triage prompt (credibility artifact) ════════"
"$LM" -i "$MODEL" \
  huggingface-load --device cuda --dtype float16 \
  llm-prompt -t -m 220 --prompt 'You are a security triage assistant. A SAST scanner flagged this Python line as a hardcoded Stripe live secret key (CWE-798): API_KEY = "sk_live_EXAMPLEonlyNOTaRealKey". In two sentences: is this a true positive, and what is the first safe verification step?' \
  2>&1 | tee "$WORK/native_triage.txt" | tail -30

echo ""; echo "════════ DONE ════════"
echo "Artifacts: $WORK/native_bench.txt · $WORK/native_triage.txt"
echo "📸 Paste the [2] tokens/sec stats + the [3] model answer back."
