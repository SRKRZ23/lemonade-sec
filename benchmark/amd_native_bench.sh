#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Lemonade-Sec · NATIVE benchmark for `lemonade` v9.x (turnkeyml tools CLI)
# The pip `lemonade-sdk` ships the tools-style CLI (no `serve`/`list`/`backends`);
# it has huggingface-load / huggingface-bench / llm-prompt. The AMD notebook already
# has PyTorch+ROCm, so we benchmark a real model on the MI300X directly.
#
# Prints each tool's -h first (so exact flags are visible), then runs a REAL
# throughput benchmark + a REAL security-triage prompt. Paste the WHOLE output back.
# ─────────────────────────────────────────────────────────────────────────────
set +e
MODEL="${MODEL:-Qwen/Qwen2.5-Coder-1.5B-Instruct}"     # small real coder model
WORK="${WORK:-$HOME/lemonade-bench}"; mkdir -p "$WORK"

echo "════════ [0] GPU + torch + lemonade ════════"
rocm-smi --showproductname 2>/dev/null | grep -i 'Card Series'
python3 - <<'PY'
try:
    import torch
    print("torch", torch.__version__, "| gpu avail:", torch.cuda.is_available(),
          "| device:", (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU only"))
except Exception as e:
    print("torch import failed:", e)
PY
lemonade -i x --tools system-info 2>&1 | grep -iE 'device|gpu|rocm|torch|processor' | head -12

echo "════════ [1] tool help — exact flags (paste back) ════════"
for t in huggingface-load huggingface-bench llm-prompt; do
  echo "──────── lemonade $t -h ────────"
  lemonade "$t" -h 2>&1 | head -30
done

echo "════════ [2] REAL throughput benchmark on MI300X ════════"
echo "model: $MODEL"
lemonade -i "$MODEL" --tools huggingface-load huggingface-bench 2>&1 | tee "$WORK/native_bench.txt" | tail -45

echo "════════ [3] REAL security-triage prompt (credibility artifact) ════════"
PROMPT='You are a security triage assistant. A SAST scanner flagged this Python line as a hardcoded Stripe live secret key (CWE-798): API_KEY = "sk_live_EXAMPLEonlyNOTaRealKey". In 2 sentences: is this a true positive, and what is the first verification step?'
lemonade -i "$MODEL" --tools huggingface-load llm-prompt --prompt "$PROMPT" 2>&1 | tee "$WORK/native_triage.txt" | tail -30
# if --prompt is the wrong flag, the -h above shows the right one; retry hint:
grep -qi 'unrecognized\|error' "$WORK/native_triage.txt" && \
  echo "↳ (llm-prompt flag differs — see its -h in section [1]; I'll pin it next.)"

echo ""; echo "════════ DONE ════════"
echo "Artifacts: $WORK/native_bench.txt (throughput) · $WORK/native_triage.txt (triage answer)"
echo "📸 Paste the [2] benchmark stats + the [3] triage answer back — those are the real MI300X numbers + credibility artifact."
