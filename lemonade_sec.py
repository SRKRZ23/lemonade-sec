#!/usr/bin/env python3
"""
Lemonade-Sec 🍋🔒 — a private-by-design AI security code reviewer.

It scans code you own (or are authorized to test), flags candidate vulnerabilities by
class with a regex SAST core (web2 + web3), and then asks a LOCAL Lemonade model to
triage each finding — verdict, exploitability, and a concrete PoC idea. Because the LLM
runs on your own machine via Lemonade, YOUR SOURCE CODE NEVER LEAVES THE MACHINE.

  authorization first
    - Findings are CANDIDATES for human verification — confirm before acting.
    - For bug bounty / client work, pass --scope scope.json and only scan authorized paths.

Usage
    # 1) start Lemonade (see README):  lemonade-server serve
    # 2) scan the bundled demo with local-AI triage:
    python3 lemonade_sec.py samples --triage
    # scan your own repo, force fully-offline triage (no server):
    python3 lemonade_sec.py ./myrepo --triage --offline --out report.md --json findings.json

Stdlib only. No cloud, no API key.
"""
import argparse, json, os, re, sys
from collections import Counter
from rules import RULES
import lemonade as lem
import triage as tri

EXT_LANG = {".py": "Python", ".js": "JS", ".ts": "TS", ".jsx": "JS", ".tsx": "TS",
            ".php": "PHP", ".rb": "Ruby", ".go": "Go", ".java": "Java",
            ".sol": "Solidity", ".html": "HTML", ".c": "C", ".cpp": "C++"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", "vendor"}
SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
COMPILED = [(r, re.compile(r["pattern"], re.IGNORECASE)) for r in RULES]


def load_scope(path):
    if not path or not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def in_scope(target_abs, scope):
    """Authorization gate: target must sit under an authorized_paths root."""
    if scope is None:
        return True
    roots = [os.path.abspath(os.path.expanduser(p)) for p in scope.get("authorized_paths", [])]
    if not roots:
        return True
    return any(target_abs == r or target_abs.startswith(r + os.sep) for r in roots)


def iter_files(root):
    if os.path.isfile(root):
        yield root
        return
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in EXT_LANG:
                yield os.path.join(dp, fn)


def scan_file(path):
    ext = os.path.splitext(path)[1].lower()
    out = []
    try:
        with open(path, "r", errors="ignore") as f:
            lines = f.readlines()
    except OSError:
        return out
    for i, line in enumerate(lines, 1):
        if len(line) > 4000:
            continue
        stripped = line.strip()
        if stripped.startswith(("#", "//", "*")):
            continue
        for rule, rx in COMPILED:
            if "*" not in rule["langs"] and ext not in rule["langs"]:
                continue
            if rx.search(line):
                out.append(dict(rule_id=rule["id"], name=rule["name"], severity=rule["severity"],
                                cwe=rule["cwe"], file=path, line=i, code=stripped[:240],
                                desc=rule["desc"], fix=rule["fix"]))
    return out


def dedupe(findings):
    seen, out = set(), []
    for f in findings:
        k = (f["rule_id"], f["file"], f["line"])
        if k not in seen:
            seen.add(k)
            out.append(f)
    out.sort(key=lambda f: (SEV_ORDER.get(f["severity"], 9), f["file"], f["line"]))
    return out


def make_report(findings, target, ai_line):
    c = Counter(f["severity"] for f in findings)
    L = [f"# Lemonade-Sec Audit — `{target}`\n",
         f"> {ai_line}\n",
         "> Automated findings are **candidates** requiring human verification before any "
         "action. Only scan assets you own or are authorized to test.\n",
         "## Summary\n", "| Severity | Count |\n|---|---|"]
    for sev in ["critical", "high", "medium", "low", "info"]:
        if c.get(sev):
            L.append(f"| {sev.upper()} | {c[sev]} |")
    L.append(f"\n**Total candidates:** {len(findings)}\n")
    if not findings:
        L.append("_No candidate findings for the current rule set._\n")
    cur = None
    for f in findings:
        if f["severity"] != cur:
            cur = f["severity"]
            L.append(f"\n## {cur.upper()}\n")
        L.append(f"### {f['name']}  ·  `{f['rule_id']}` · {f['cwe']}")
        L.append(f"- **Location:** `{os.path.relpath(f['file'])}:{f['line']}`")
        L.append(f"- **Evidence:** `{f['code']}`")
        L.append(f"- **Why it matters:** {f['desc']}")
        L.append(f"- **Remediation:** {f['fix']}")
        if f.get("triage"):
            v = f["triage"]
            L.append(f"- **AI triage** ({v.get('source','?')}): `{v.get('verdict','?')}` "
                     f"(conf {v.get('confidence','?')}) — {v.get('reasoning','')}")
            if v.get("poc_idea"):
                L.append(f"  - **PoC idea:** {v['poc_idea']}")
        L.append("- **Verification:** confirm reachability with untrusted input + build a PoC "
                 "before reporting.\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Lemonade-Sec — private-by-design AI security code reviewer")
    ap.add_argument("target", help="file or directory to audit")
    ap.add_argument("--scope", help="scope.json listing authorized_paths (for bug bounty / client work)")
    ap.add_argument("--out", default="lemonade_sec_report.md", help="markdown report output")
    ap.add_argument("--json", dest="jsonout", help="also write findings JSON")
    ap.add_argument("--triage", action="store_true", help="triage findings (local Lemonade LLM, else offline heuristic)")
    ap.add_argument("--lemonade-url", default=lem.DEFAULT_BASE, help="Lemonade OpenAI-compatible base URL")
    ap.add_argument("--model", help="model id (default: auto-pick from Lemonade /models)")
    ap.add_argument("--offline", action="store_true", help="skip the server; use the offline heuristic only")
    args = ap.parse_args()

    target = os.path.abspath(os.path.expanduser(args.target))
    if not os.path.exists(target):
        sys.exit(f"target not found: {target}")

    scope = load_scope(args.scope)
    if scope is None and args.scope:
        sys.exit(f"scope file not found: {args.scope}")
    if scope is None:
        print("⚠️  no --scope: treating as local/own-code review. For bug bounty, add a scope.json "
              "with authorized_paths and only scan what a program authorizes.", file=sys.stderr)
    elif not in_scope(target, scope):
        sys.exit("⛔ REFUSED: target is OUTSIDE authorized_paths in your scope file.")

    findings = []
    n = 0
    for path in iter_files(target):
        n += 1
        findings.extend(scan_file(path))
    findings = dedupe(findings)

    # Triage: local Lemonade model if reachable, else the fully-offline heuristic.
    ai_line = "Triage skipped (run with --triage)."
    if args.triage:
        base, model = None, None
        if not args.offline:
            info = lem.discover(args.lemonade_url)
            print(lem.banner(info), file=sys.stderr)
            if info["up"]:
                base, model = info["base"], (args.model or info["picked"])
        else:
            print("🔒 --offline: using the built-in heuristic (no network at all).", file=sys.stderr)
        ai_line = (f"AI triage: **local Lemonade** model `{model}` — source never left this machine."
                   if base else "AI triage: **offline heuristic** (no model server; still 100% local).")
        for f in findings:
            f["triage"] = tri.triage(f, base, model) if base else tri.heuristic_triage(f)

    report = make_report(findings, os.path.relpath(target), ai_line)
    with open(args.out, "w") as f:
        f.write(report)
    if args.jsonout:
        with open(args.jsonout, "w") as f:
            json.dump(findings, f, indent=2)

    c = Counter(f["severity"] for f in findings)
    print(f"Lemonade-Sec: scanned {n} files → {len(findings)} candidates "
          f"({c.get('critical',0)} crit, {c.get('high',0)} high, {c.get('medium',0)} med, "
          f"{c.get('low',0)} low)")
    print(f"report → {args.out}" + (f"  ·  json → {args.jsonout}" if args.jsonout else ""))


if __name__ == "__main__":
    main()
