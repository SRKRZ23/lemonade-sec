#!/usr/bin/env python3
"""Tiny OpenAI-compatible MOCK server — lets you test the benchmark harness / the tool
WITHOUT a GPU or a real model. It is NOT a model: it returns a canned triage verdict and
fake token usage so `amd_bench.py` and `lemonade_sec.py --triage` run end-to-end.

Use it only to validate the harness locally; real numbers come from a real Lemonade server.
  python3 mock_lemonade.py 8000      # then point --url http://localhost:8000/api/v1
"""
import json, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERDICT = {"verdict": "true_positive", "confidence": 0.82,
           "reasoning": "MOCK verdict — canned response for harness testing, not a real model.",
           "poc_idea": "MOCK — replace with a real Lemonade server for genuine triage."}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            self._json({"object": "list", "data": [{"id": "mock-qwen-coder", "object": "model"}]})
        else:
            self._json({"status": "ok"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        _ = self.rfile.read(n)
        time.sleep(0.05)  # simulate a little latency
        content = json.dumps(VERDICT)
        self._json({"id": "mock", "object": "chat.completion", "model": "mock-qwen-coder",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                                 "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 120, "completion_tokens": 200, "total_tokens": 320}})

    def _json(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"MOCK Lemonade (OpenAI-compatible) on http://localhost:{port}/api/v1  — Ctrl-C to stop")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
