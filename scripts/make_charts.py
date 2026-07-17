#!/usr/bin/env python3
"""Generate Lemonade-Sec branded charts (lemon-amber identity) for the README/deck.
Numbers are MEASURED (rule counts from rules.py; demo scan of samples/) or clearly
MODELED (economics). Output → ../assets/*.png"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rules import RULES  # measured: the real rule set

# ---- Lemonade-Sec design tokens (lemon 🍋 amber identity) ----
AMBER, INK = "#F5A700", "#0A0A0A"
GREEN, RED = "#1a9e5a", "#d64545"          # local/private win · cloud-risk / critical
G1, G2, G3, LINE, TINT = "#3a3a3a", "#6a6a6a", "#b8b8b8", "#e6e6e6", "#fff6e0"

# One typeface across charts / deck / video: same Inter TTFs used by the Remotion
# video (deck/fonts/), registered directly rather than hoping a system font matches.
_FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "deck", "fonts")
for _f in ("Inter-400.ttf", "Inter-500.ttf", "Inter-700.ttf", "Inter-900.ttf"):
    _p = os.path.join(_FONTS_DIR, _f)
    if os.path.exists(_p):
        font_manager.fontManager.addfont(_p)
plt.rcParams["font.family"] = "Inter Variable"
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white",
                     "savefig.facecolor": "white", "axes.edgecolor": LINE, "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": G1, "ytick.color": G2})
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT, exist_ok=True)


def style(ax, tag, sub):
    ax.set_title(sub, fontsize=14.5, fontweight="bold", color=INK, loc="left", pad=2)
    ax.text(0, 1.13, tag, transform=ax.transAxes, fontsize=10, fontweight="bold", color=AMBER)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(LINE); ax.spines["bottom"].set_color(LINE)
    ax.tick_params(length=0); ax.set_axisbelow(True); ax.yaxis.grid(True, color=LINE, lw=1)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight", pad_inches=0.28)
    plt.close(fig); print("wrote", name)


# 1) DATA EGRESS — the killer chart (architectural fact)
fig, ax = plt.subplots(figsize=(6.8, 4))
labels = ["Cloud AI\ncode review", "Lemonade-Sec\n(local)"]
vals = [100, 0]
bars = ax.bar(labels, vals, color=[RED, GREEN], width=0.58, zorder=3)
ax.text(0, 104, "your whole\ncodebase uploaded", ha="center", fontsize=10, color=RED, fontweight="bold")
ax.text(1, 6, "0 bytes\nleave the machine", ha="center", fontsize=11, color=GREEN, fontweight="bold")
ax.set_ylabel("% of source sent to a third party / scan", fontsize=10.5)
ax.set_ylim(0, 125)
style(ax, "ARCHITECTURAL FACT · WHERE YOUR CODE GOES",
      "Private by design: source never leaves the machine")
save(fig, "chart_egress.png")

# 2) RULE COVERAGE — measured donut from rules.py
cat = {"SEC": "Secrets", "INJ": "Injection", "SSRF": "Web/SSRF/XSS", "PATH": "Web/SSRF/XSS",
       "XSS": "Web/SSRF/XSS", "WEB": "Web/SSRF/XSS", "JS": "Web/SSRF/XSS", "CRY": "Crypto/Config",
       "CFG": "Crypto/Config", "AUTH": "Crypto/Config", "SOL": "Web3 / Solidity"}
def bucket(rid):
    for k in sorted(cat, key=len, reverse=True):
        if rid.startswith(k):
            return cat[k]
    return "Other"
counts = Counter(bucket(r["id"]) for r in RULES)
order = ["Secrets", "Injection", "Web/SSRF/XSS", "Crypto/Config", "Web3 / Solidity"]
sizes = [counts.get(o, 0) for o in order]
cols = [AMBER, "#f5c451", "#e8913a", GREEN, INK]
fig, ax = plt.subplots(figsize=(5.6, 4.6))
w, _ = ax.pie(sizes, colors=cols, startangle=90, counterclock=False,
              wedgeprops=dict(width=0.42, edgecolor="white", linewidth=3))
ax.text(0, 0.12, str(len(RULES)), ha="center", fontsize=34, fontweight="bold", color=INK)
ax.text(0, -0.24, "rules", ha="center", fontsize=12, color=G1, fontweight="bold")
ax.legend(w, [f"{o} ({c})" for o, c in zip(order, sizes)], loc="lower center",
          bbox_to_anchor=(0.5, -0.30), fontsize=9, frameon=False, handlelength=1.1, labelspacing=0.6)
ax.set_title("Coverage across web2 + web3 in one pass", fontsize=12.5, fontweight="bold",
             color=INK, y=1.05)
save(fig, "chart_coverage.png")

# 3) DEMO SCAN — measured findings on the bundled sample
fig, ax = plt.subplots(figsize=(6.6, 4))
sev = ["Critical", "High", "Medium"]
vals = [1, 6, 7]
cols = [RED, "#e8913a", AMBER]
bars = ax.bar(sev, vals, color=cols, width=0.6, zorder=3)
for b, v in zip(bars, vals):
    ax.text(b.get_x()+b.get_width()/2, v+0.15, str(v), ha="center", fontsize=14, fontweight="bold", color=INK)
ax.set_ylabel("candidate findings", fontsize=11)
ax.set_ylim(0, 8.4)
style(ax, "MEASURED · `python3 lemonade_sec.py samples --triage`",
      "14 findings on the demo sample, each AI-triaged locally")
save(fig, "chart_demo.png")

# 4) ANNUAL COST — modeled economics, 20-dev team
fig, ax = plt.subplots(figsize=(7.4, 4))
labels = ["GitHub Advanced\nSecurity", "Snyk Team", "Cloud LLM PR\nreview (est.)", "Lemonade-Sec\n(local, MIT)"]
vals = [11760, 6000, 4200, 0]
cols = [G2, G3, "#e8913a", GREEN]
bars = ax.barh(labels[::-1], vals[::-1], color=cols[::-1], height=0.62, zorder=3)
for b, v in zip(bars, vals[::-1]):
    ax.text(v+120, b.get_y()+b.get_height()/2, ("$0 + local compute" if v == 0 else f"${v:,}"),
            va="center", fontsize=11, fontweight="bold", color=(GREEN if v == 0 else INK))
ax.set_xlabel("$ / year · 20-developer team (list-price estimates)", fontsize=10.5)
ax.set_xlim(0, 13800)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color(LINE); ax.spines["bottom"].set_color(LINE); ax.tick_params(length=0)
ax.set_axisbelow(True); ax.xaxis.grid(True, color=LINE, lw=1)
ax.set_title("The open-core core is free; incumbents charge per seat", fontsize=13,
             fontweight="bold", color=INK, loc="left", pad=2)
ax.text(0, 1.1, "MODELED · public list-price estimates (2026) — directional, not a quote",
        transform=ax.transAxes, fontsize=9.5, fontweight="bold", color=AMBER)
save(fig, "chart_cost.png")

print(f"\n✅ 4 charts in {os.path.abspath(OUT)}  ·  {len(RULES)} rules across {len(set(bucket(r['id']) for r in RULES))} classes")
