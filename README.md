# Mock VPS Service

A lightweight FastAPI-based mock VPS management API — simulates provisioning, listing, starting/stopping, and deleting virtual private servers with an in-memory store. Built as a teaching / prototyping scaffold that can be extended to real container/VM backends.

## How Sub-Agents Built It

This service was assembled by delegated sub-agents coordinated by the parent agent:

| Sub-Agent | Responsibility |
|-----------|---------------|
| **API Agent** | Created `app.py` with FastAPI routes (`/`, `/vps/create`, `/vps/list`, `/vps/{id}/start`, `/vps/{id}/stop`, `DELETE /vps/{id}`) and Pydantic request validation |
| **Docs Agent** | Authored this README and `run.sh` deployment script |
| **Infra Agent** | Defined `requirements.txt` (`fastapi`, `uvicorn[standard]`, `pydantic`) and verified `uvicorn` startup on port 8000 |

The in-memory `vps_store` dict keeps the mock simple — no database required. Each VPS gets a short UUID, a name, RAM/CPU spec, and a `running`/`stopped` status.

## Project Structure

```
vps_service/
├── app.py              # FastAPI application
├── requirements.txt    # Python dependencies
├── run.sh              # One-click install & run script
├── README.md           # This file
└── static/             # Reserved for frontend assets
```

## How to Run

### Option 1 — One-click via `run.sh`

```bash
chmod +x run.sh
./run.sh
```

This installs dependencies and starts `uvicorn` on `0.0.0.0:8000`.

### Option 2 — Manual

```bash
# Create and activate a virtualenv (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# or
pip install fastapi "uvicorn[standard]" pydantic

# Start the server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Verify:

```bash
curl http://localhost:8000/
# {"status":"ok","service":"mock VPS service","vps_count":0}
```

Interactive docs are at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

## API Reference & curl Examples

All endpoints return JSON. The mock store is ephemeral — restarting the server clears all VPS entries.

### Health Check

```bash
curl http://localhost:8000/
```

### Create a VPS

```bash
curl -X POST http://localhost:8000/vps/create \
  -H "Content-Type: application/json" \
  -d '{"name": "web-01", "ram": 2048, "cpu": 2}'
# {"id":"a1b2c3d4","name":"web-01","ram":2048,"cpu":2,"status":"stopped"}
```

### List All VPS

```bash
curl http://localhost:8000/vps/list
# [{"id":"a1b2c3d4","name":"web-01","ram":2048,"cpu":2,"status":"stopped"}]
```

### Start a VPS

```bash
curl -X POST http://localhost:8000/vps/{id}/start
# e.g.
curl -X POST http://localhost:8000/vps/a1b2c3d4/start
```

### Stop a VPS

```bash
curl -X POST http://localhost:8000/vps/{id}/stop
```

### Delete a VPS

```bash
curl -X DELETE http://localhost:8000/vps/{id}
# e.g.
curl -X DELETE http://localhost:8000/vps/a1b2c3d4
```

### Full Lifecycle Script

```bash
# Create
ID=$(curl -s -X POST http://localhost:8000/vps/create \
  -H "Content-Type: application/json" \
  -d '{"name":"demo","ram":4096,"cpu":4}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Created: $ID"

# Start / verify / stop / delete
curl -s -X POST http://localhost:8000/vps/$ID/start | cat
curl -s http://localhost:8000/vps/list | cat
curl -s -X POST http://localhost:8000/vps/$ID/stop | cat
curl -s -X DELETE http://localhost:8000/vps/$ID | cat
```

## Extending to Real VPS (Docker / LXC)

The mock store is intentionally swappable. To provision real workloads:

### Docker Backend

Replace the `vps_store` logic with `docker-py` calls:

```python
import docker
client = docker.from_env()

@app.post("/vps/create")
def create_vps(req: CreateVPSRequest):
    container = client.containers.run(
        "ubuntu:22.04", name=req.name,
        mem_limit=f"{req.ram}m", nano_cpus=req.cpu * 1_000_000_000,
        detach=True, tty=True, command="sleep infinity"
    )
    return {"id": container.id[:12], "name": req.name, "ram": req.ram, "cpu": req.cpu, "status": "running"}

@app.post("/vps/{vps_id}/start")
def start_vps(vps_id: str):
    client.containers.get(vps_id).start()
    return {"id": vps_id, "status": "running"}

@app.post("/vps/{vps_id}/stop")
def stop_vps(vps_id: str):
    client.containers.get(vps_id).stop()
    return {"id": vps_id, "status": "stopped"}
```

Add `docker` to `requirements.txt` and ensure the host Docker socket is accessible (`/var/run/docker.sock`).

### LXC / LXD Backend

For system containers closer to real VPS:

```python
import pylxd
client = pylxd.Client()

@app.post("/vps/create")
def create_vps(req: CreateVPSRequest):
    config = {
        "name": req.name,
        "source": {"type": "image", "alias": "ubuntu/22.04"},
        "config": {"limits.memory": f"{req.ram}MB", "limits.cpu": str(req.cpu)},
    }
    instance = client.instances.create(config, wait=True)
    instance.start(wait=True)
    return {"id": instance.name, "name": req.name, "ram": req.ram, "cpu": req.cpu, "status": "running"}
```

Add `pylxd` to `requirements.txt`. Requires LXD installed and the API user in the `lxd` group.

### Other Considerations for Production

- **Persistence** — replace the in-memory dict with a database (SQLite/PostgreSQL via SQLAlchemy or `databases`).
- **Auth** — add API-key or JWT auth (`fastapi.security`).
- **Validation** — constrain `ram`/`cpu` to allowed tiers; add disk, image, and SSH-key fields.
- **Networking** — allocate ports/IPs, manage firewall rules or bridge networks.
- **Monitoring** — expose metrics (Prometheus) and logs per VPS.
- **Async** — use `BackgroundTasks` or Celery for long provisioning operations.
