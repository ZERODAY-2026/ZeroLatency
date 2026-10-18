"""A tiny loopback HTTP stand-in for Ollama's API, used by tests.

It is NOT a model. It lets the real OllamaClient/requests code path run (tags, ps, version,
generate/keep_alive unload, chat) with scripted replies. Results using it are labelled
"stub" everywhere and are never presented as real Gemma results.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class StubOllama:
    def __init__(self, installed=("gemma3n:e2b",), responder=None, too_big=()):
        self.installed = list(installed)
        self.loaded: list[str] = []
        self.responder = responder or (lambda model, system, user: "{}")
        self.too_big = set(too_big)
        self.requests: list[tuple[str, str, dict]] = []  # (method, path, body)
        self.delay = 0.0
        self.raw_reply: str | None = None  # force a malformed reply
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # keep test output (and any document text) quiet
                pass

            def _send(self, status, payload):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _body(self):
                length = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(length) or b"{}") if length else {}

            def do_GET(self):
                stub.requests.append(("GET", self.path, {}))
                if self.path == "/api/tags":
                    return self._send(200, {"models": [{"name": n} for n in stub.installed]})
                if self.path == "/api/ps":
                    return self._send(200, {"models": [{"name": n, "size": 1, "size_vram": 0} for n in stub.loaded]})
                if self.path == "/api/version":
                    return self._send(200, {"version": "stub-0.0"})
                self._send(404, {"error": "not found"})

            def do_POST(self):
                body = self._body()
                stub.requests.append(("POST", self.path, body))
                model = body.get("model")
                if self.path == "/api/generate":
                    if body.get("keep_alive") == 0 and model in stub.loaded:
                        stub.loaded.remove(model)
                    return self._send(200, {"done": True})
                if self.path == "/api/show":
                    return self._send(200, {"details": {"quantization_level": "stub"}})
                if self.path == "/api/chat":
                    if model not in stub.installed:
                        return self._send(404, {"error": f"model '{model}' not found"})
                    if model in stub.too_big:
                        return self._send(500, {"error": "model requires more system memory (9.0 GiB) than is available (5.0 GiB)"})
                    if stub.delay:
                        import time

                        time.sleep(stub.delay)
                    if model not in stub.loaded:
                        stub.loaded.append(model)
                    msgs = body["messages"]
                    content = stub.raw_reply if stub.raw_reply is not None else stub.responder(model, msgs[0]["content"], msgs[1]["content"])
                    return self._send(200, {"message": {"role": "assistant", "content": content}})
                self._send(404, {"error": "not found"})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()

    def chat_models_used(self) -> list[str]:
        return [body["model"] for method, path, body in self.requests if path == "/api/chat"]
