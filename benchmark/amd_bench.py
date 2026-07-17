#!/usr/bin/env python3
"""Lemonade-Sec benchmark — measure the LOCAL-AI triage pipeline on real hardware.

Point it at a running Lemonade server (OpenAI-compatible). It measures, on THIS machine:
  1) model throughput   — tokens/sec generating a fixed completion
  2) triage latency     — seconds per finding for the real local-LLM security triage
  3) scan speed         — SAST files/sec + findings
Writes a MEASURED results JSON (+ an optional chart) and prints a summary table.

Designed to run inside an AMD AI Notebook (notebooks.amd.com → AAI Developer Zone / ROCm)
against Lemonade on a Radeon/Instinct GPU — but works against any OpenAI-compatible local
server (Ollama, LM Studio) too. Stdlib + optional matplotlib.

Usage:
  python3 amd_bench.py --url http://localhost:8000/api/v1 --samples ../samples --out amd_bench_results.json --chart
"""
import argparse, json, os, sys, time, urllib.request, statistics as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import lemonade as lem            # discovery
import triage as tri             # the real triage call
import lemonade_sec as core      # scanner (scan_file / iter_files / dedupe)

PROMPT = ("Explain, in about 200 words, why running an AI security code reviewer locally "
          "(so source code never leaves the machine) matters for regulated organizations.")


def _post(url, body, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer local-no-key"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def bench_throughput(base, model, max_tokens=256, runs=3):
    """tokens/sec for a fixed generation. Uses server-reported completion_tokens when present."""
    url = base.rstrip("/") + "/chat/completions"
    rates, toks, secs = [], [], []
    for i in range(runs):
        body = {"model": model, "temperature": 0, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": PROMPT}]}
        t0 = time.perf_counter()
        data = _post(url, body)
        dt = time.perf_counter() - t0
        ct = (data.get("usage") or {}).get("completion_tokens")
        if not ct:  # estimate if server omits usage
            ct = int(len((data["choices"][0]["message"]["content"] or "").split()) * 1.3)
        rates.append(ct / dt if dt else 0); toks.append(ct); secs.append(dt)
    return dict(tok_per_sec=round(st.median(rates), 1), completion_tokens=int(st.median(toks)),
                seconds=round(st.median(secs), 2), runs=runs, max_tokens=max_tokens)


def bench_triage(base, model, findings):
    """Seconds per finding for the REAL local-LLM triage; also reports verdict mix."""
    lats, verdicts, src = [], {}, None
    for f in findings:
        t0 = time.perf_counter()
        v = tri.triage(f, base, model)
        lats.append(time.perf_counter() - t0)
        verdicts[v.get("verdict", "?")] = verdicts.get(v.get("verdict", "?"), 0) + 1
        src = v.get("source", src)
    return dict(n=len(findings), sec_per_finding=round(st.median(lats), 2),
                total_sec=round(sum(lats), 2), verdicts=verdicts, source=src)


def bench_scan(samples):
    """SAST throughput (no network)."""
    t0 = time.perf_counter()
    files, findings = 0, []
    for p in core.iter_files(os.path.abspath(samples)):
        files += 1
        findings.extend(core.scan_file(p))
    findings = core.dedupe(findings)
    dt = time.perf_counter() - t0
    return dict(files=files, findings=len(findings),
                files_per_sec=round(files / dt, 1) if dt else None, seconds=round(dt, 4)), findings


def make_chart(res, out_png):
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except Exception:
        print("(matplotlib not available — skipping chart)"); return
    AMBER, INK, GREEN, LINE = "#F5A700", "#0A0A0A", "#1a9e5a", "#e6e6e6"
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    tp = res["throughput"]["tok_per_sec"]
    a1.bar(["Lemonade\non "+res["hardware"]["gpu_short"]], [tp], color=AMBER, width=0.5, zorder=3)
    a1.text(0, tp, f"{tp:.0f}", ha="center", va="bottom", fontsize=16, fontweight="bold", color=INK)
    a1.set_ylabel("tokens / sec", fontsize=11); a1.set_ylim(0, tp*1.25 or 1)
    a1.set_title("MEASURED · model throughput", loc="left", fontsize=12, fontweight="bold", color=INK)
    tl = res["triage"]["sec_per_finding"]
    a2.bar(["per finding"], [tl], color=GREEN, width=0.5, zorder=3)
    a2.text(0, tl, f"{tl:.2f}s", ha="center", va="bottom", fontsize=16, fontweight="bold", color=INK)
    a2.set_ylabel("seconds", fontsize=11); a2.set_ylim(0, tl*1.3 or 1)
    a2.set_title("MEASURED · local triage latency", loc="left", fontsize=12, fontweight="bold", color=INK)
    for ax in (a1, a2):
        for s in ("top", "right"): ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(LINE); ax.spines["bottom"].set_color(LINE)
        ax.tick_params(length=0); ax.set_axisbelow(True); ax.yaxis.grid(True, color=LINE, lw=1)
    fig.suptitle(f"Lemonade-Sec on {res['hardware']['gpu']} · model {res['model']}",
                 x=0.01, ha="left", fontsize=10, fontweight="bold", color=AMBER)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(out_png, dpi=200, bbox_inches="tight")
    print("chart →", out_png)


def detect_hw():
    """Best-effort AMD GPU name via rocm-smi; falls back to 'unknown'."""
    gpu = os.environ.get("BENCH_GPU", "")
    if not gpu:
        for cmd in ("rocm-smi --showproductname", "rocminfo"):
            try:
                import subprocess
                o = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=20).stdout
                for line in o.splitlines():
                    if "Card Series" in line or "Marketing Name" in line or "Card model" in line:
                        gpu = line.split(":")[-1].strip(); break
                if gpu: break
            except Exception:
                pass
    gpu = gpu or "unknown-GPU"
    short = gpu.replace("AMD ", "").replace("Radeon ", "R").split("[")[0].strip()[:18]
    return dict(gpu=gpu, gpu_short=short)


def main():
    ap = argparse.ArgumentParser(description="Lemonade-Sec hardware benchmark (measured)")
    ap.add_argument("--url", default=lem.DEFAULT_BASE)
    ap.add_argument("--model", help="model id (default: auto-pick from /models)")
    ap.add_argument("--samples", default=os.path.join(os.path.dirname(__file__), "..", "samples"))
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", default="amd_bench_results.json")
    ap.add_argument("--chart", action="store_true")
    args = ap.parse_args()

    info = lem.discover(args.url)
    if not info["up"]:
        sys.exit(f"⛔ No Lemonade server: {info['error']}\n"
                 f"   Start it first (`lemonade-server serve`) then re-run.")
    base, model = info["base"], (args.model or info["picked"])
    hw = detect_hw()
    print(f"🍋 Benchmarking Lemonade-Sec · model '{model}' · {hw['gpu']} · endpoint {base}\n")

    scan, findings = bench_scan(args.samples)
    print(f"[1/3] scan     : {scan['files']} files, {scan['findings']} findings, {scan['files_per_sec']} files/s")
    tp = bench_throughput(base, model, args.max_tokens, args.runs)
    print(f"[2/3] throughput: {tp['tok_per_sec']} tok/s  ({tp['completion_tokens']} tok in {tp['seconds']}s, median of {tp['runs']})")
    tg = bench_triage(base, model, findings)
    print(f"[3/3] triage   : {tg['sec_per_finding']}s/finding, {tg['total_sec']}s total, verdicts={tg['verdicts']}")

    res = dict(tool="lemonade-sec", measured=True, endpoint=base, model=model, hardware=hw,
               scan=scan, throughput=tp, triage=tg)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(f"\n✅ MEASURED results → {args.out}")
    if args.chart:
        make_chart(res, os.path.splitext(args.out)[0] + ".png")


if __name__ == "__main__":
    main()
