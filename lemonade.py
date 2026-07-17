"""Lemonade server client — the local, private AI backend for Lemonade-Sec.

Lemonade (https://lemonade-server.ai) runs an OpenAI-compatible server on your own
machine (llama.cpp / ONNX Runtime / ROCm / Vulkan backends). Because inference is
LOCAL, your source code is never uploaded to a cloud provider during triage.

This module only does discovery + health — the actual chat call lives in triage.py
(both speak the same OpenAI `/chat/completions` schema).

Default base URL follows Lemonade's server docs: http://localhost:8000/api/v1
Override with --lemonade-url or the LEMONADE_BASE_URL env var if you changed the port.
Stdlib only — no SDK, no keys.
"""
import json, os, urllib.request, urllib.error

DEFAULT_BASE = os.environ.get("LEMONADE_BASE_URL", "http://localhost:8000/api/v1")


def _get(url, timeout=4):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _candidates(base_url):
    """The given base first, then common Lemonade/OpenAI path variants so a slightly
    wrong --lemonade-url still connects (/api/v1 vs /v1, with/without trailing path)."""
    base = base_url.rstrip("/")
    root = base
    for suf in ("/api/v1", "/v1", "/api", ""):
        if root.endswith(suf) and suf:
            root = root[: -len(suf)]
            break
    seen, out = set(), []
    for cand in (base, root + "/api/v1", root + "/v1", root):
        c = cand.rstrip("/")
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _pick_model(models):
    """Prefer a coder/instruct model for security reasoning if present."""
    for pref in ("coder", "qwen", "instruct", "llama"):
        for m in models:
            if pref in m.lower():
                return m
    return models[0] if models else None


def discover(base_url=DEFAULT_BASE, timeout=4):
    """Probe a running Lemonade server across path variants. Returns dict:
    {up: bool, models: [ids], picked: id|None, base: url, error: str|None}.
    Never raises — a down server just yields up=False so the caller can fall
    back to the fully-offline heuristic (Lemonade-Sec still produces a report)."""
    last = None
    for base in _candidates(base_url):
        try:
            data = _get(base + "/models", timeout=timeout)
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            return dict(up=True, models=models, picked=_pick_model(models), base=base, error=None)
        except Exception as e:  # try the next candidate path
            last = getattr(e, "reason", None) or f"{type(e).__name__}: {e}"
    return dict(up=False, models=[], picked=None, base=base_url.rstrip("/"),
                error=f"cannot reach a Lemonade server near {base_url} ({last}). "
                      f"Start it with `lemonade-server serve`, or run with --offline.")


def banner(info):
    """Human-readable one-liner about where triage will run."""
    if info["up"]:
        return (f"🔒 Lemonade LOCAL AI online at {info['base']} — model '{info['picked']}'. "
                f"Your source code stays on this machine.")
    return (f"⚠️  Lemonade not reachable — {info['error']}\n"
            f"    Falling back to the OFFLINE heuristic (still 100% local, no network).")


if __name__ == "__main__":  # quick manual check: `python3 lemonade.py`
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    info = discover(base)
    print(banner(info))
    if info["models"]:
        print("models:", ", ".join(info["models"]))
