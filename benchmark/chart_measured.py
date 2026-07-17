#!/usr/bin/env python3
"""Render the MEASURED MI300X benchmark (1.5B vs 7B) as a branded comparison chart
→ ../assets/chart_mi300x.png. Reads the results/*.json (measured, dated)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

AMBER, INK, DK, G1, G2, LINE = "#F5A700", "#0A0A0A", "#c47f00", "#3a3a3a", "#6a6a6a", "#e6e6e6"
for fam in ("Helvetica Neue", "Helvetica", "Arial"):
    if any(fam.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = fam; break

HERE = os.path.dirname(__file__)
def load(n): return json.load(open(os.path.join(HERE, "results", n)))
m15, m7 = load("mi300x_qwen2.5-coder-1.5b.json"), load("mi300x_qwen2.5-coder-7b.json")
labels = ["1.5B", "7B"]
cols = [AMBER, DK]

panels = [
    ("Generation (decode)", "tokens/sec",
     [m15["throughput"]["token_generation_tok_per_sec"], m7["throughput"]["token_generation_tok_per_sec"]], "{:.1f}"),
    ("Prefill (prompt)", "tokens/sec",
     [m15["throughput"]["prefill_tok_per_sec"], m7["throughput"]["prefill_tok_per_sec"]], "{:,.0f}"),
    ("Time to first token", "milliseconds",
     [m15["throughput"]["time_to_first_token_sec"]*1000, m7["throughput"]["time_to_first_token_sec"]*1000], "{:.0f}"),
]

fig, axes = plt.subplots(1, 3, figsize=(11.5, 4))
for ax, (title, unit, vals, fmt) in zip(axes, panels):
    bars = ax.bar(labels, vals, color=cols, width=0.62, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v, fmt.format(v), ha="center", va="bottom",
                fontsize=13, fontweight="bold", color=INK)
    ax.set_title(title, fontsize=12.5, fontweight="bold", color=INK, loc="left", pad=2)
    ax.set_ylabel(unit, fontsize=10.5)
    ax.set_ylim(0, max(vals)*1.22 or 1)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(LINE); ax.spines["bottom"].set_color(LINE)
    ax.tick_params(length=0); ax.set_axisbelow(True); ax.yaxis.grid(True, color=LINE, lw=1)

fig.text(0.012, 0.965, "MEASURED · AMD Instinct MI300X (gfx942) · torch 2.9.1+rocm6.3 · fp16 · Qwen2.5-Coder",
         fontsize=11, fontweight="bold", color=AMBER)
fig.text(0.012, 0.915, "Decode holds ~62–64 tok/s from 1.5B to 7B — framework-bound (HF eager), not compute-bound",
         fontsize=13, fontweight="bold", color=INK)
fig.text(0.012, 0.02, "MI300X VF · HuggingFace eager backend — a real pipeline measurement, not a hardware peak; "
         "the GPU is far from saturated, so vLLM / llama.cpp-ROCm would be substantially higher.",
         fontsize=9, color=G2)
fig.subplots_adjust(left=0.06, right=0.985, top=0.80, bottom=0.14, wspace=0.28)
out = os.path.join(HERE, "..", "assets", "chart_mi300x.png")
fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.25, facecolor="white")
print("wrote", os.path.abspath(out))
