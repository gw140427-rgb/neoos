from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid, os, subprocess, json
from typing import Dict, Optional

app = FastAPI(title="VPS Service (Docker-ready)")

vps_store: Dict[str, dict] = {}

def docker_available():
    try:
        subprocess.run(["docker","--version"], capture_output=True, timeout=3)
        return True
    except: return False

HAS_DOCKER = docker_available()

class CreateVPSRequest(BaseModel):
    name: str
    ram: int
    cpu: int
    os: str = "ubuntu-22.04"

class InstallRequest(BaseModel):
    os: str

class ExecRequest(BaseModel):
    cmd: str

@app.get("/")
def health():
    return {"status":"ok","service":"VPS service (docker-ready)","vps_count":len(vps_store),"docker":HAS_DOCKER}

@app.post("/vps/create")
def create_vps(req: CreateVPSRequest):
    vid = str(uuid.uuid4())[:8]
    vps = {"id":vid,"name":req.name,"ram":req.ram,"cpu":req.cpu,"os":req.os,"status":"stopped","mode":"mock"}
    if HAS_DOCKER:
        try:
            # try to run detached ubuntu container
            subprocess.run(["docker","run","-d","--name",f"vps-{vid}","--memory",f"{req.ram}m","--cpus",str(req.cpu),"ubuntu:22.04","sleep","infinity"], capture_output=True, timeout=30)
            vps["status"]="running"
            vps["mode"]="docker"
            vps["container"]=f"vps-{vid}"
        except Exception as e:
            vps["error"]=str(e)
    vps_store[vid]=vps
    return vps

@app.post("/vps/{vid}/install")
def install(vid:str, req: InstallRequest):
    vps=vps_store.get(vid)
    if not vps: raise HTTPException(404,"VPS not found")
    allowed=["ubuntu-22.04","ubuntu-24.04","debian-12","centos-9"]
    if req.os not in allowed: raise HTTPException(400,f"Choose from {allowed}")
    vps["os"]=req.os
    vps["ip"]=f"10.0.{int(vid[:2],16)%255}.{int(vid[2:4],16)%255}"
    vps["ssh"]=f"ssh root@{vid}.mock-vps.local -p 2222"
    if HAS_DOCKER and vps.get("mode")=="docker":
        # in real docker, we would pull different image; for demo just update label
        vps["status"]="running"
    else:
        vps["status"]="running"
    return {"detail":f"{req.os} installed","vps":vps}

@app.post("/vps/{vid}/start")
def start(vid:str):
    v=vps_store.get(vid)
    if not v: raise HTTPException(404,"VPS not found")
    if HAS_DOCKER and v.get("container"):
        subprocess.run(["docker","start",v["container"]], capture_output=True)
    v["status"]="running"
    return v

@app.post("/vps/{vid}/stop")
def stop(vid:str):
    v=vps_store.get(vid)
    if not v: raise HTTPException(404,"VPS not found")
    if HAS_DOCKER and v.get("container"):
        subprocess.run(["docker","stop",v["container"]], capture_output=True)
    v["status"]="stopped"
    return v

@app.delete("/vps/{vid}")
def delete(vid:str):
    v=vps_store.pop(vid,None)
    if not v: raise HTTPException(404,"VPS not found")
    if HAS_DOCKER and v.get("container"):
        subprocess.run(["docker","rm","-f",v["container"]], capture_output=True)
    return {"detail":f"VPS {vid} deleted","vps":v}

@app.post("/vps/{vid}/exec")
def exec_cmd(vid:str, req: ExecRequest):
    v=vps_store.get(vid)
    if not v: raise HTTPException(404,"VPS not found")
    if v["status"]!="running": raise HTTPException(400,"VPS not running")
    if HAS_DOCKER and v.get("mode")=="docker":
        try:
            r=subprocess.run(["docker","exec",v["container"],"bash","-c",req.cmd], capture_output=True, text=True, timeout=10)
            return {"output":r.stdout + r.stderr, "exit_code":r.returncode}
        except Exception as e: raise HTTPException(500,str(e))
    else:
        # mock exec for demo without docker
        mock = f"[mock {v['os']} {vid}] $ {req.cmd}\n"
        if req.cmd.strip()=="ls": mock+="-rw-r--r-- 1 root root  0 Jan 1 00:00 file.txt\n"
        elif req.cmd.startswith("echo"): mock+=req.cmd[5:]+"\n"
        elif req.cmd=="uname -a": mock+="Linux "+vid+" 5.15.0-mock #1 SMP x86_64 GNU/Linux\n"
        elif req.cmd=="pwd": mock+="/root\n"
        else: mock+="(mock output - deploy to GratisVPS with Docker for real output)\n"
        return {"output":mock,"exit_code":0,"mock":True}

@app.get("/vps/list")
def list_vps(): return list(vps_store.values())

@app.get("/vps/{vid}")
def get(vid:str):
    v=vps_store.get(vid)
    if not v: raise HTTPException(404,"VPS not found")
    return v

# dashboard
import os as _os
if _os.path.isdir("static") or _os.path.isdir("/root/vps_service/static"):
    sd="static" if _os.path.isdir("static") else "/root/vps_service/static"
    try: app.mount("/dashboard", StaticFiles(directory=sd, html=True), name="static")
    except: pass

if __name__=="__main__":
    import uvicorn; uvicorn.run(app,host="0.0.0.0",port=8000)
