# NeoOS Server MVP

NeoOS Server is a small, self-hosted system dashboard and bounded Docker controller. It does **not** create a cloud VPS or provide compute, a public IP, or guaranteed uptime.

## Features
- Mobile-friendly web dashboard at `/` and `/dashboard`.
- System platform, architecture, uptime, root-disk usage, and memory metrics.
- Docker daemon availability/version and container list.
- Bearer-token authentication for all API routes except the basic health check and static dashboard shell.
- Explicit-confirmation Docker start, stop, and restart for container IDs currently listed by Docker.
- Loopback bind by default; no arbitrary command execution, browser terminal, image pulls, volume management, or container creation/deletion.

The dashboard itself is public on the local listener but does not return system data without a token. Do not expose the service publicly. Use HTTPS or an SSH tunnel; the default loopback binding is intentional.

## SSH access
Use the host operating system's OpenSSH server. This project does not implement its own SSH protocol or browser terminal. From a client, tunnel the API/dashboard port:

```sh
ssh -L 8765:127.0.0.1:8765 USER@YOUR_SERVER
```

Then open `http://127.0.0.1:8765/` on the client. Keep the API bound to loopback and do not forward port 8765 directly to the public internet.

## Run
Python 3.10+; Docker is optional.

```sh
export NEOOS_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python3 -m server.neoos_server
```

Environment:
- `NEOOS_SERVER_HOST`: defaults to `127.0.0.1`; avoid public binding.
- `NEOOS_SERVER_PORT`: defaults to `8765`.
- `NEOOS_SERVER_TOKEN`: required, at least 24 characters.

Routes:
- `GET /health`: basic health only.
- `GET /` or `GET /dashboard`: dashboard UI.
- `GET /api/status`, `/api/docker`, `/api/containers`: authenticated read endpoints.
- `POST /api/container-action`: authenticated action; JSON must include `container_id`, `action` (`start`, `stop`, or `restart`), and `confirm: true`.

Docker actions use fixed argument arrays (no shell), validate the container ID, and require that the ID appears in a fresh container listing. The API token is powerful: someone who can control this server's Docker daemon may be able to affect the host. Only run it on a machine you control and never share the token. This MVP has not been independently security-audited.

## Test
```sh
python3 -m unittest test_neoos_server -v
```

Software is free; host resources and provider availability are separate. This project does not promise a free VPS or 24/7 operation.
