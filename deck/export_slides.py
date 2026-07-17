#!/usr/bin/env python3
"""Split Lemonade-Sec_deck.html into 5 standalone single-slide HTML files and
screenshot each via headless Chrome at 2x scale (2560x1440) → png/slide-0N.png.
Re-uses the deck's own <head> (fonts + styles) so every export matches exactly."""
import os, re, subprocess, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Lemonade-Sec_deck.html")
TMP = os.path.join(HERE, "_slide_tmp")
OUT = os.path.join(HERE, "png")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if not os.path.exists(CHROME):
    sys.exit(f"Chrome not found at {CHROME} — edit the CHROME path in this script.")

html = open(SRC, encoding="utf-8").read()
head_match = re.search(r"<head>.*?</head>", html, re.S)
head = head_match.group(0)
slides = re.findall(r'<section class="slide">.*?</section>', html, re.S)
print(f"found {len(slides)} slides")

os.makedirs(TMP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

OVERRIDE = "<style>html,body{background:#fff!important}.slide{margin:0!important}</style>"

for i, slide in enumerate(slides, 1):
    page = f"<!doctype html><html><head><base href=\"file://{HERE}/\">{head}{OVERRIDE}</head><body>{slide}</body></html>"
    tmp_path = os.path.join(TMP, f"slide-{i:02d}.html")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(page)
    out_path = os.path.join(OUT, f"slide-{i:02d}.png")
    subprocess.run([
        CHROME, "--headless", "--disable-gpu",
        "--run-all-compositor-stages-before-draw", "--virtual-time-budget=4000",
        "--window-size=1280,720", "--force-device-scale-factor=2",
        f"--screenshot={out_path}", f"file://{tmp_path}",
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sz = os.path.getsize(out_path)
    print(f"  slide-{i:02d}.png  {sz/1024:.0f} KB")

shutil.rmtree(TMP)
print(f"\n✅ {len(slides)} PNGs → {OUT}")
