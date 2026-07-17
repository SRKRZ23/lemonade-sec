#!/usr/bin/env python3
"""Render the MEASURED MI300X benchmark as a branded KPI chart → ../assets/chart_mi300x.png.
Reads benchmark/results/mi300x_qwen2.5-coder-1.5b.json (measured, dated)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

AMBER, INK, GREEN, G1, G2, LINE = "#F5A700", "#0A0A0A", "#1a9e5a", "#3a3a3a", "#6a6a6a", "#e6e6e6"
for fam in ("Helvetica Neue", "Helvetica", "Arial"):
    if any(fam.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = fam; break

HERE = os.path.dirname(__file__)
data = json.load(open(os.path.join(HERE, "results", "mi300x_qwen2.5-coder-1.5b.json")))
t = data["throughput"]
tiles = [
    (f"{t['token_generation_tok_per_sec']:.1f}", "tokens/sec", "generation (decode)"),
    (f"{t['prefill_tok_per_sec']:,.0f}", "tokens/sec", "prefill (prompt)"),
    (f"{t['time_to_first_token_sec']*1000:.0f}", "ms", "time to first token"),
]

fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
for ax, (num, unit, label) in zip(axes, tiles):
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0.03, 0.08), 0.94, 0.84, transform=ax.transAxes,
                 facecolor="#fff6e0", edgecolor="#f2dfae", lw=1.5, zorder=0))
    ax.text(0.5, 0.62, num, ha="center", va="center", fontsize=40, fontweight="bold", color=INK)
    ax.text(0.5, 0.40, unit, ha="center", va="center", fontsize=14, color=AMBER, fontweight="bold")
    ax.text(0.5, 0.22, label, ha="center", va="center", fontsize=13, color=G1, fontweight="bold")

fig.text(0.012, 0.955, "MEASURED · AMD Instinct MI300X (gfx942) · torch 2.9.1+rocm6.3 · fp16",
         fontsize=11, fontweight="bold", color=AMBER)
fig.text(0.012, 0.90, f"Lemonade-Sec local-AI triage running {data['model']} on real AMD hardware",
         fontsize=13.5, fontweight="bold", color=INK)
fig.text(0.012, 0.03, "HuggingFace eager backend (unoptimized) on an MI300X VF — a real pipeline "
         "measurement, not a hardware peak; vLLM / llama.cpp-ROCm would be higher.",
         fontsize=9, color=G2)
fig.subplots_adjust(left=0.01, right=0.99, top=0.84, bottom=0.14, wspace=0.08)
out = os.path.join(HERE, "..", "assets", "chart_mi300x.png")
fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.25, facecolor="white")
print("wrote", os.path.abspath(out))
