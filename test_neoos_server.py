"""Tests for the safe, read-only NeoOS server MVP."""
import json
import os
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from threading import Thread

import server.neoos_server as app


class ServerTests(unittest.TestCase):
    def test_system_status_has_expected_fields(self):
        with patch.object(app.shutil, "disk_usage", return_value=type("Usage", (), {
            "total": 100, "used": 40, "free": 60
        })()):
            data = app.system_status()
        self.assertIn("architecture", data)
        self.assertIn("disk_root", data)
        self.assertEqual(data["disk_root"]["free_bytes"], 60)

    @patch.object(app.subprocess, "run")
    def test_docker_status_uses_fixed_command(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = "27.0.0\n"
        self.assertEqual(app.docker_status(), {"available": True, "server_version": "27.0.0"})
        self.assertEqual(run.call_args.args[0], ["docker", "info", "--format", "{{.ServerVersion}}"])

    @patch.object(app.subprocess, "run")
    def test_container_listing_parses_safe_fields(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = json.dumps({
            "ID": "abc", "Names": "demo", "Image": "alpine", "State": "running",
            "Status": "Up 2 minutes", "Ports": "secret-ish", "Mounts": "/host:/container"
        }) + "\n"
        data = app.docker_containers()
        self.assertTrue(data["available"])
        self.assertEqual(data["containers"][0]["name"], "demo")
        self.assertNotIn("Mounts", data["containers"][0])
        self.assertNotIn("Ports", data["containers"][0])

    def test_http_auth_and_read_only_routes(self):
        previous = app.TOKEN
        app.TOKEN = "t" * 32
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with self.assertRaises(HTTPError) as err:
                urlopen(base + "/api/status")
            self.assertEqual(err.exception.code, 401)
            req = Request(base + "/api/status", headers={"Authorization": "Bearer " + app.TOKEN})
            with patch.object(app, "system_status", return_value={"ok": True}):
                with urlopen(req) as response:
                    self.assertEqual(json.loads(response.read()), {"ok": True})
            req = Request(base + "/api/status", data=b"{}", method="POST")
            with self.assertRaises(HTTPError) as err2:
                urlopen(req)
            self.assertEqual(err2.exception.code, 405)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            app.TOKEN = previous


if __name__ == "__main__":
    unittest.main()
