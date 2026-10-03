"""Minimal internal bridge for NeoOS -> isolated Linux container.

The bridge is intentionally reachable only on the private Compose network.
It never mounts the Docker socket or host filesystem.
"""

import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8081"))
MAX_COMMAND = 1000
MAX_OUTPUT = 12000
TIMEOUT = 8


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"ok": True, "service": "neoos-linux"})
        else:
            self._json(404, {"ok": False, "error": "Not Found"})

    def do_POST(self):
        if self.path != "/exec":
            return self._json(404, {"ok": False, "error": "Not Found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16 * 1024:
                return self._json(400, {"ok": False, "error": "잘못된 요청입니다."})
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            cmd = data.get("command", "")
            if not isinstance(cmd, str) or not cmd.strip():
                return self._json(400, {"ok": False, "error": "명령어가 없습니다."})
            if len(cmd) > MAX_COMMAND:
                return self._json(413, {"ok": False, "error": "명령어는 1000자 이하입니다."})

            result = subprocess.run(
                ["/bin/bash", "-lc", cmd],
                cwd="/home/neoos",
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=TIMEOUT,
                check=False,
                env={
                    "HOME": "/home/neoos",
                    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                    "LANG": "C.UTF-8",
                    "TERM": "xterm-256color",
                },
            )
            output = result.stdout[-MAX_OUTPUT:]
            if result.returncode:
                output += f"\n[종료 코드: {result.returncode}]"
            return self._json(200, {"ok": True, "output": output})
        except subprocess.TimeoutExpired as exc:
            raw = exc.stdout or ""
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            return self._json(200, {"ok": True, "output": str(raw)[-MAX_OUTPUT:] + "\n[시간 제한: 8초]"})
        except Exception as exc:
            return self._json(500, {"ok": False, "error": f"Linux 실행 오류: {type(exc).__name__}"})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
