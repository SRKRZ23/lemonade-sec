"""Triage a candidate finding — grounded in a built-in attack playbook.

Two modes:
  triage()            -> asks a LOCAL Lemonade model (OpenAI-compatible) to rate the
                         finding and draft a class-specific PoC. Source stays local.
  heuristic_triage()  -> OFFLINE, no server needed: rates + drafts a PoC idea from the
                         built-in PLAYBOOK for that vuln class.

Both inject the playbook entry as context so PoC ideas are real and class-specific.
Stdlib urllib only — no paid SDK, no API key required for a local Lemonade server.
"""
import json, os, urllib.request

SYS = ("You are a precise application-security triage assistant for AUTHORIZED review of "
       "code the operator owns or is explicitly permitted to test. Given a candidate finding, "
       "its code context, and the relevant attack playbook, decide if it is a true positive, "
       "how exploitable it is, and a concrete, class-specific verification/PoC approach. Be "
       "conservative: mark false_positive when the pattern is not reachable by untrusted input. "
       "Reply STRICT JSON: "
       '{"verdict":"true_positive|false_positive|uncertain","confidence":0..1,'
       '"reasoning":"1-2 sentences","poc_idea":"1-2 concrete steps"}')

CONF = {"critical": 0.6, "high": 0.5, "medium": 0.4, "low": 0.25, "info": 0.2}

# Small, generic, publishable playbook keyed by rule-id prefix. Grounds triage without
# needing any private knowledge base. Extend freely.
PLAYBOOK = {
    "SEC":  ("Leaked secret", "Confirm the credential is live (authenticate then immediately "
             "deauthenticate — do NOT exercise functionality); if valid, it is a true positive.",
             "Grep VCS history for the same value; check whether it reaches production config."),
    "INJ-CMD": ("OS command injection", "Trace the argument to an untrusted source (HTTP param, "
                "CLI arg, filename); inject `; id` / `$(id)` in a controlled test.",
                "shell=True or os.system with concatenation is the classic sink."),
    "INJ-SQL": ("SQL injection", "Send `' OR '1'='1` / a UNION probe to the parameter that reaches "
                "the concatenated query; look for boolean/error/time differences.",
                "String-built queries without parameterization."),
    "INJ-EVAL": ("Dynamic eval/exec", "Check if any user-controlled string reaches eval/exec; a "
                 "payload like `__import__('os').system('id')` proves RCE.", ""),
    "INJ-DESERIAL": ("Unsafe deserialization", "If untrusted bytes reach pickle/yaml.load, craft a "
                     "__reduce__ gadget in a lab to prove code execution.", ""),
    "SSRF": ("SSRF", "Point the request at http://169.254.169.254/ (cloud metadata) or an internal "
             "host you control; a response/callback proves server-side fetch of attacker URLs.", ""),
    "PATH-TRAVERSAL": ("Path traversal", "Request `../../etc/passwd` (or a repo-relative sentinel) "
                       "through the parameter that builds the path.", ""),
    "XSS": ("DOM/stored XSS", "Inject `<img src=x onerror=alert(1)>` into the value that reaches the "
            "sink; confirm script execution in a victim context.", ""),
    "AUTH-JWT": ("JWT auth bypass", "Forge a token with alg=none or an unverified signature and see "
                 "if it is accepted for a protected action.", ""),
    "WEB-JWT": ("JWT not verified", "If decode runs with verify=False, submit a self-signed/edited "
                "token and confirm it is trusted.", ""),
    "WEB-SSTI": ("SSTI", "Inject `{{7*7}}` (or engine-specific) and look for `49` in the response; "
                 "escalate to RCE via the engine's sandbox escape.", ""),
    "WEB-IDOR": ("IDOR", "Authenticate as user A, then request object ids belonging to user B; "
                 "success without an ownership check confirms it.", ""),
    "CRY": ("Weak crypto/RNG", "Show the weak primitive guards a security decision (password hash, "
            "token, signature) — otherwise it is informational.", ""),
    "CFG-TLS": ("TLS verification disabled", "Confirm the client talks to an attacker-controllable "
                "host; a MITM proxy demonstrates interception.", ""),
    "SOL-REENTRANCY": ("Reentrancy", "In a Foundry fork test, re-enter the value-sending function "
                       "from a malicious receiver before state updates; drain > deposited.", ""),
    "SOL-ARBDELEGATE": ("Arbitrary delegatecall", "If the delegatecall target is user-controlled, "
                        "point it at a contract that rewrites owner/implementation storage.", ""),
    "SOL-TXORIGIN": ("tx.origin auth", "Deploy an intermediary contract that a victim calls; it "
                     "relays to the target so tx.origin == victim bypasses the check.", ""),
    "SOL": ("Solidity issue", "Reproduce in a Foundry/Hardhat fork test at the deployed state.", ""),
}


def playbook_for(rule_id):
    """Longest-prefix match into PLAYBOOK; returns (name, verify, notes) or None."""
    best = None
    for key in PLAYBOOK:
        if rule_id.startswith(key) and (best is None or len(key) > len(best)):
            best = key
    return PLAYBOOK.get(best) if best else None


def _context(finding, radius=6):
    try:
        with open(finding["file"], errors="ignore") as f:
            lines = f.readlines()
    except OSError:
        return finding.get("code", "")
    i = finding["line"] - 1
    return "".join(lines[max(0, i - radius):min(len(lines), i + radius + 1)])


def _brain_block(pb):
    if not pb:
        return "(no playbook for this class yet)"
    name, verify, notes = pb
    b = [f"PLAYBOOK: {name}", "verify: " + verify]
    if notes:
        b.append("notes: " + notes)
    return "\n".join(b)


def heuristic_triage(finding):
    """Offline verdict + PoC idea drawn from the built-in playbook. No network."""
    sev = finding.get("severity", "medium")
    high_signal = finding["rule_id"].split(":")[0] in {
        "SEC-AWS", "SEC-PRIVKEY", "SEC-GOOGLE", "SEC-STRIPE", "SEC-GITHUB",
        "SOL-REENTRANCY", "AUTH-JWT-NONE", "WEB-JWT-NOVERIFY", "SOL-ARBDELEGATE"}
    conf = CONF.get(sev, 0.35) + (0.15 if high_signal else 0)
    verdict = "true_positive" if high_signal else "uncertain"
    pb = playbook_for(finding["rule_id"])
    poc = pb[1] if pb else "Trace data flow from an untrusted source to this sink; build a minimal PoC."
    reason = (f"{finding['name']} pattern; class={pb[0] if pb else '?'}. "
              f"Confirm reachability by untrusted input.")
    return dict(verdict=verdict, confidence=round(min(conf, 0.9), 2), reasoning=reason,
                poc_idea=poc, source="offline-heuristic")


def triage(finding, base_url, model, timeout=90):
    """Ask a LOCAL Lemonade model. Falls back to the offline heuristic on any error."""
    if not base_url or not model:
        return heuristic_triage(finding)
    pb = playbook_for(finding["rule_id"])
    user = (f"FINDING: {finding['name']} ({finding['rule_id']}, {finding['cwe']}, sev={finding['severity']})\n"
            f"FILE: {os.path.relpath(finding['file'])}:{finding['line']}\nWHY: {finding['desc']}\n\n"
            f"CODE CONTEXT:\n```\n{_context(finding)}\n```\n\n"
            f"ATTACK PLAYBOOK:\n{_brain_block(pb)}\n\nReturn the JSON verdict.")
    body = json.dumps({"model": model, "temperature": 0,
                       "messages": [{"role": "system", "content": SYS},
                                    {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer local-no-key"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        txt = data["choices"][0]["message"]["content"]
        s, e = txt.find("{"), txt.rfind("}")
        out = json.loads(txt[s:e + 1]) if s >= 0 else {"verdict": "uncertain", "reasoning": txt[:200]}
        out["source"] = f"lemonade:{model}"
        return out
    except Exception as ex:
        h = heuristic_triage(finding)
        h["reasoning"] = f"[lemonade unreachable: {ex}] " + h["reasoning"]
        return h
