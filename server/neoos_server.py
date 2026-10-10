#!/usr/bin/env python3
"""Minimal, read-only NeoOS server control API.

Security model: loopback-only by default, bearer-token auth for API routes,
fixed Docker commands only, and no arbitrary shell/terminal endpoint.
Use SSH port forwarding for remote access rather than exposing this service.
"""
from __future__ import annotations

import hmac
import json
import os
import platform
import shutil
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

STARTED_AT = time.monotonic()
HOST = os.environ.get("NEOOS_SERVER_HOST", "127.0.0.1")
PORT = int(os.environ.get("NEOOS_SERVER_PORT", "8765"))
TOKEN = os.environ.get("NEOOS_SERVER_TOKEN", "")


def _read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    try:
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                key, _, rest = line.partition(":")
                fields = rest.split()
                if fields and fields[0].isdigit():
                    values[key] = int(fields[0]) * (1024 if len(fields) > 1 and fields[1] == "kB" else 1)
    except OSError:
        pass
    return values


def system_status() -> dict[str, Any]:
    usage = shutil.disk_usage("/")
    memory = _read_meminfo()
    return {
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "uptime_seconds": int(time.monotonic() - STARTED_AT),
        "disk_root": {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free},
        "memory": {
            "total_bytes": memory.get("MemTotal"),
            "available_bytes": memory.get("MemAvailable"),
        },
    }


def docker_status() -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True, text=True, timeout=4, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"available": False, "reason": "Docker CLI unavailable or timed out"}
    if result.returncode != 0:
        return {"available": False, "reason": "Docker daemon unavailable"}
    return {"available": True, "server_version": result.stdout.strip()}


def docker_containers() -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["docker", "ps", "--all", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"available": False, "reason": "Docker CLI unavailable or timed out", "containers": []}
    if result.returncode != 0:
        return {"available": False, "reason": "Docker daemon unavailable", "containers": []}
    containers = []
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Only expose common, non-secret display fields.
        containers.append({
            "id": item.get("ID", ""),
            "name": item.get("Names", ""),
            "image": item.get("Image", ""),
            "state": item.get("State", ""),
            "status": item.get("Status", ""),
        })
    return {"available": True, "containers": containers}


class Handler(BaseHTTPRequestHandler):
    server_version = "NeoOS-Server/0.1"

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"ok": True, "service": "neoos-server"})
            return
        if self.path not in ("/api/status", "/api/docker", "/api/containers"):
            self._send(404, {"error": "not_found"})
            return
        supplied = self.headers.get("Authorization", "")
        expected = "Bearer " + TOKEN if TOKEN else ""
        if not TOKEN or not hmac.compare_digest(supplied, expected):
            self._send(401, {"error": "unauthorized"})
            return
        if self.path == "/api/status":
            self._send(200, system_status())
        elif self.path == "/api/docker":
            self._send(200, docker_status())
        else:
            self._send(200, docker_containers())

    def do_POST(self) -> None:  # noqa: N802
        # Mutating endpoints and arbitrary command execution are intentionally absent.
        self._send(405, {"error": "method_not_allowed", "message": "Read-only MVP"})

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep logs concise; do not log request headers or tokens.
        print("NeoOS Server:", fmt % args)


def main() -> None:
    if not TOKEN or len(TOKEN) < 24:
        raise SystemExit("Set NEOOS_SERVER_TOKEN to a random value of at least 24 characters.")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"NeoOS Server listening on {HOST}:{PORT}; read-only API enabled.")
    print("Remote access: use SSH port forwarding; do not expose this port publicly.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
