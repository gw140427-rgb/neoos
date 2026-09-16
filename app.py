from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
import os
from typing import Dict

app = FastAPI(title="Mock VPS Service")

# In-memory store
vps_store: Dict[str, dict] = {}

class CreateVPSRequest(BaseModel):
    name: str
    ram: int  # MB or GB, free form
    cpu: int  # cores

@app.get("/")
def health_check():
    return {"status": "ok", "service": "mock VPS service", "vps_count": len(vps_store)}

@app.post("/vps/create")
def create_vps(req: CreateVPSRequest):
    vps_id = str(uuid.uuid4())[:8]
    vps = {
        "id": vps_id,
        "name": req.name,
        "ram": req.ram,
        "cpu": req.cpu,
        "status": "stopped"
    }
    vps_store[vps_id] = vps
    return vps

@app.get("/vps/list")
def list_vps():
    return list(vps_store.values())

@app.post("/vps/{vps_id}/start")
def start_vps(vps_id: str):
    vps = vps_store.get(vps_id)
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    vps["status"] = "running"
    return vps

@app.post("/vps/{vps_id}/stop")
def stop_vps(vps_id: str):
    vps = vps_store.get(vps_id)
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    vps["status"] = "stopped"
    return vps

@app.delete("/vps/{vps_id}")
def delete_vps(vps_id: str):
    vps = vps_store.pop(vps_id, None)
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    return {"detail": f"VPS {vps_id} deleted", "vps": vps}

class InstallRequest(BaseModel):
    os: str  # e.g. ubuntu-22.04, debian-12, windows-2022

@app.post("/vps/{vps_id}/install")
def install_os(vps_id: str, req: InstallRequest):
    vps = vps_store.get(vps_id)
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    allowed = ["ubuntu-22.04", "ubuntu-24.04", "debian-12", "centos-9", "windows-2022"]
    if req.os not in allowed:
        raise HTTPException(status_code=400, detail=f"OS not supported. Choose from {allowed}")
    vps["os"] = req.os
    vps["status"] = "installing"
    vps["ssh"] = f"ssh root@{vps_id}.mock-vps.local -p 2222"
    vps["ip"] = f"10.0.{int(vps_id[:2],16)%255}.{int(vps_id[2:4],16)%255}"
    # simulate instant install for demo
    vps["status"] = "running"
    return {"detail": f"Linux {req.os} installed", "vps": vps}

@app.get("/vps/{vps_id}")
def get_vps(vps_id: str):
    vps = vps_store.get(vps_id)
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    return vps

# Serve dashboard at /dashboard (keep / for API health check)
if os.path.isdir("static") or os.path.isdir("/root/vps_service/static"):
    static_dir = "static" if os.path.isdir("static") else "/root/vps_service/static"
    try:
        app.mount("/dashboard", StaticFiles(directory=static_dir, html=True), name="static")
    except: pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
