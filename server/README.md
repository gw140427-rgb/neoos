# NeoOS Server MVP (read-only)

This is the first server-management slice for NeoOS. It does **not** create a cloud VPS. It provides a small local HTTP API to inspect the machine on which it runs.

## Features in this MVP

- System platform, architecture, uptime, root-disk usage, and available memory.
- Docker daemon availability and server version.
- Read-only listing of containers (ID, name, image, state, status).
- Bearer-token authentication for API routes.
- Loopback bind by default; no arbitrary command execution or mutating Docker endpoints.

## SSH and terminal

Use the operating system's OpenSSH server for remote shell access. This project does not implement its own SSH protocol or expose a browser shell. For remote API access, use an SSH tunnel from your client:

```sh
ssh -L 8765:127.0.0.1:8765 USER@YOUR_SERVER
```

Then open `http://127.0.0.1:8765/health` locally. Keep the API bound to loopback. Do not forward port 8765 directly to the public internet.

## Run

Python 3.10+; Docker is optional (Docker endpoints report unavailable if the CLI/daemon is absent).

```sh
export NEOOS_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python3 -m server.neoos_server
```

Environment:
- `NEOOS_SERVER_HOST`: defaults to `127.0.0.1`. Avoid public binding.
- `NEOOS_SERVER_PORT`: defaults to `8765`.
- `NEOOS_SERVER_TOKEN`: required, at least 24 characters.

Routes:
- `GET /health`: basic health only.
- `GET /api/status`: authenticated system metrics.
- `GET /api/docker`: authenticated Docker availability/version.
- `GET /api/containers`: authenticated read-only container list.

All POST requests return 405. Docker start/stop/restart, arbitrary terminal commands, user management, and provisioning VMs are deliberately out of scope until a proper permission model and threat review exist.

## Test

```sh
python3 -m unittest test_neoos_server -v
```

## Limits and cost

The software is free, but it does not supply compute, a public IP, or 24/7 uptime. Those depend on the host or provider. This MVP has not been security-audited and should not be exposed publicly or used for sensitive production workloads.
