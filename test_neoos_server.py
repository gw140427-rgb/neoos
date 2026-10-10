"""Tests for the NeoOS server API, dashboard, and bounded Docker controls."""
import json
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from threading import Thread

import server.neoos_server as app


class ServerTests(unittest.TestCase):
    def test_system_status_has_expected_fields(self):
        with patch.object(app.shutil, "disk_usage", return_value=type("Usage", (), {"total": 100, "used": 40, "free": 60})()):
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
    def test_container_listing_exposes_only_safe_fields(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = json.dumps({"ID": "a" * 64, "Names": "demo", "Image": "alpine", "State": "running", "Status": "Up 2 minutes", "Ports": "hidden", "Mounts": "/host:/container"}) + "\n"
        data = app.docker_containers()
        self.assertTrue(data["available"])
        self.assertEqual(data["containers"][0]["name"], "demo")
        self.assertNotIn("Mounts", data["containers"][0])
        self.assertNotIn("Ports", data["containers"][0])
        self.assertIn("--no-trunc", run.call_args.args[0])

    @patch.object(app, "docker_containers", return_value={"available": True, "containers": [{"id": "a" * 64}]})
    @patch.object(app.subprocess, "run")
    def test_docker_action_is_allowlisted_and_targets_listed_id(self, run, listing):
        run.return_value.returncode = 0
        result = app.docker_container_action("a" * 64, "stop")
        self.assertTrue(result["ok"])
        self.assertEqual(run.call_args.args[0], ["docker", "stop", "a" * 64])
        run.reset_mock()
        self.assertEqual(app.docker_container_action("a" * 64, "exec")["error"], "unsupported_action")
        run.assert_not_called()
        self.assertEqual(app.docker_container_action("not-an-id", "stop")["error"], "invalid_container_id")

    @patch.object(app, "docker_containers", return_value={"available": True, "containers": [{"id": "b" * 64}]})
    @patch.object(app.subprocess, "run")
    def test_docker_action_rejects_unlisted_container(self, run, listing):
        result = app.docker_container_action("a" * 64, "stop")
        self.assertEqual(result["error"], "container_not_found")
        run.assert_not_called()

    def test_http_auth_dashboard_and_action_confirmation(self):
        previous = app.TOKEN
        app.TOKEN = "t" * 32
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(base + "/") as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"NeoOS Server", response.read())
            with self.assertRaises(HTTPError) as err:
                urlopen(base + "/api/status")
            self.assertEqual(err.exception.code, 401)
            req = Request(base + "/api/status", headers={"Authorization": "Bearer " + app.TOKEN})
            with patch.object(app, "system_status", return_value={"ok": True}):
                with urlopen(req) as response:
                    self.assertEqual(json.loads(response.read()), {"ok": True})
            req = Request(base + "/api/container-action", data=json.dumps({"container_id": "a" * 64, "action": "stop"}).encode(), headers={"Authorization": "Bearer " + app.TOKEN}, method="POST")
            with self.assertRaises(HTTPError) as err2:
                urlopen(req)
            self.assertEqual(err2.exception.code, 400)
            req = Request(base + "/api/status", data=b"{}", method="POST")
            with self.assertRaises(HTTPError) as err3:
                urlopen(req)
            self.assertEqual(err3.exception.code, 405)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            app.TOKEN = previous


    @patch.object(app, "docker_containers", return_value={"available": True, "containers": []})
    @patch.object(app.subprocess, "run")
    def test_server_create_uses_only_builtin_template_and_limits(self, run, listing):
        run.return_value.returncode = 0
        run.return_value.stdout = "c" * 64 + "\\n"
        result = app.docker_server_create("demo-web", "nginx")
        self.assertTrue(result["ok"])
        command = run.call_args.args[0]
        self.assertEqual(command[:3], ["docker", "run", "-d"])
        self.assertIn("--memory=256m", command)
        self.assertIn("--cpus=0.5", command)
        self.assertNotIn("-p", command)
        self.assertNotIn("-v", command)
        self.assertEqual(command[-3:], ["nginx", "-g", "daemon off;"])

    @patch.object(app.subprocess, "run")
    def test_server_create_rejects_invalid_name_or_template(self, run):
        self.assertEqual(app.docker_server_create("bad name", "nginx")["error"], "invalid_server_name")
        self.assertEqual(app.docker_server_create("valid-name", "arbitrary-image")["error"], "unsupported_template")
        run.assert_not_called()

    @patch.object(app, "docker_containers", return_value={"available": True, "containers": [{"id": "d" * 64, "name": "demo", "state": "running"}]})
    @patch.object(app.subprocess, "run")
    def test_server_delete_refuses_running_container(self, run, listing):
        result = app.docker_server_delete("d" * 64)
        self.assertEqual(result["error"], "stop_server_before_delete")
        run.assert_not_called()

    @patch.object(app, "docker_containers", return_value={"available": True, "containers": [{"id": "e" * 64, "name": "demo", "state": "exited"}]})
    @patch.object(app.subprocess, "run")
    def test_server_delete_only_removes_stopped_container(self, run, listing):
        run.return_value.returncode = 0
        result = app.docker_server_delete("e" * 64)
        self.assertTrue(result["ok"])
        self.assertEqual(run.call_args.args[0], ["docker", "rm", "e" * 64])


if __name__ == "__main__":
    unittest.main()
