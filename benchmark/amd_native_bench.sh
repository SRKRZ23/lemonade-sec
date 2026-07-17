#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lemonade-Sec · REAL MI300X benchmark via lemonade v9 + ROCm PyTorch
# The container ships no torch, so we install a ROCm torch wheel (matched to the
# node's ROCm) into lemonade's Python, then run huggingface-bench on the GPU
# (--device cuda; ROCm presents as cuda). Falls back to llama.cpp GGUF (CPU) if
# the GPU path is unavailable. Paste the WHOLE output back.
# ─────────────────────────────────────────────────────────────────────────────
set +e
MODEL="${MODEL:-Qwen/Qwen2.5-Coder-1.5B-Instruct}"
GGUF="${GGUF:-Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_0}"
WORK="${WORK:-$HOME/lemonade-bench}"; mkdir -p "$WORK"
PIP="python3 -m pip install --break-system-packages -q"

echo "════════ [0] GPU + ROCm version ════════"
rocm-smi --showproductname 2>/dev/null | grep -i 'Card Series'
ROCM_VER="$(cat /opt/rocm/.info/version 2>/dev/null | grep -oE '^[0-9]+\.[0-9]+' | head -1)"
[ -z "$ROCM_VER" ] && ROCM_VER="$(ls -d /opt/rocm-*/ 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)"
[ -z "$ROCM_VER" ] && ROCM_VER="$(hipconfig --version 2>/dev/null | grep -oE '^[0-9]+\.[0-9]+')"
echo "ROCm detected: ${ROCM_VER:-unknown}"
case "$ROCM_VER" in
  6.0|6.1) CH=rocm6.1;; 6.2) CH=rocm6.2;; 6.3) CH=rocm6.3;; 6.4|6.5|6.6) CH=rocm6.4;; *) CH=rocm6.3;;
esac
echo "torch wheel channel: $CH"

echo "════════ [1] install ROCm PyTorch + transformers (into lemonade's python) ════════"
$PIP --index-url "https://download.pytorch.org/whl/$CH" torch 2>&1 | tail -5
$PIP transformers accelerate huggingface_hub 2>&1 | tail -3
python3 -c 'import torch;print("torch",torch.__version__,"| gpu avail:",torch.cuda.is_available(),"| hip:",getattr(torch.version,"hip","no"),"| dev:",(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"))' 2>&1 | tail -2
GPU_OK=$(python3 -c 'import torch;print(1 if torch.cuda.is_available() else 0)' 2>/dev/null)

if [ "$GPU_OK" = "1" ]; then
  echo "════════ [2] REAL throughput benchmark on MI300X (huggingface, --device cuda, fp16) ════════"
  echo "model: $MODEL"
  lemonade -i "$MODEL" \
    huggingface-load --device cuda --dtype float16 \
    huggingface-bench --prompts 256 --output-tokens 128 --iterations 5 --warmup-iterations 2 \
    2>&1 | tee "$WORK/native_bench.txt" | tail -50
  echo "════════ [3] REAL security-triage prompt (credibility artifact) ════════"
  lemonade -i "$MODEL" \
    huggingface-load --device cuda --dtype float16 \
    llm-prompt -t -m 220 --prompt 'You are a security triage assistant. A SAST scanner flagged this Python line as a hardcoded Stripe live secret key (CWE-798): API_KEY = "sk_live_EXAMPLEonlyNOTaRealKey". In two sentences: is this a true positive, and what is the first safe verification step?' \
    2>&1 | tee "$WORK/native_triage.txt" | tail -30
else
  echo "⚠️ torch GPU not available after install — using llama.cpp GGUF fallback (may be CPU):"
  lemonade -i "$GGUF" llamacpp-load llamacpp-bench 2>&1 | tee "$WORK/native_bench.txt" | tail -45
fi

echo ""; echo "════════ DONE ════════"
echo "Artifacts: $WORK/native_bench.txt · $WORK/native_triage.txt"
echo "📸 Paste the [2] tokens/sec + [3] model answer back (or the fallback output)."
