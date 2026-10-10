#!/usr/bin/env python3
"""Small NeoOS server API with a local dashboard and bounded Docker controls."""
from __future__ import annotations
import hmac, json, os, platform, re, shutil, subprocess, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

STARTED_AT=time.monotonic()
HOST=os.environ.get("NEOOS_SERVER_HOST","127.0.0.1")
PORT=int(os.environ.get("NEOOS_SERVER_PORT","8765"))
TOKEN=os.environ.get("NEOOS_SERVER_TOKEN","")
DASHBOARD_PATH=Path(__file__).with_name("dashboard.html")
ALLOWED_DOCKER_ACTIONS={"start","stop","restart"}
CONTAINER_ID_RE=re.compile(r"^[a-fA-F0-9]{4,64}$")
SERVER_NAME_RE=re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]{0,31}$")
SERVER_TEMPLATES={
    "nginx":{"image":"nginx:alpine","command":["nginx","-g","daemon off;"]},
    "alpine":{"image":"alpine:3.22","command":["sleep","365d"]},
    "python":{"image":"python:3.13-alpine","command":["python","-m","http.server","8080","--bind","0.0.0.0"]},
}

def _read_meminfo()->dict[str,int]:
    values={}
    try:
        with open("/proc/meminfo",encoding="utf-8") as handle:
            for line in handle:
                key,_,rest=line.partition(":"); fields=rest.split()
                if fields and fields[0].isdigit(): values[key]=int(fields[0])*(1024 if len(fields)>1 and fields[1]=="kB" else 1)
    except OSError: pass
    return values

def system_status()->dict[str,Any]:
    usage=shutil.disk_usage("/"); memory=_read_meminfo()
    return {"platform":platform.platform(),"architecture":platform.machine(),"python":platform.python_version(),
      "uptime_seconds":int(time.monotonic()-STARTED_AT),
      "disk_root":{"total_bytes":usage.total,"used_bytes":usage.used,"free_bytes":usage.free},
      "memory":{"total_bytes":memory.get("MemTotal"),"available_bytes":memory.get("MemAvailable")}}

def docker_status()->dict[str,Any]:
    try: result=subprocess.run(["docker","info","--format","{{.ServerVersion}}"],capture_output=True,text=True,timeout=4,check=False)
    except (FileNotFoundError,subprocess.TimeoutExpired): return {"available":False,"reason":"Docker CLI unavailable or timed out"}
    if result.returncode!=0: return {"available":False,"reason":"Docker daemon unavailable"}
    return {"available":True,"server_version":result.stdout.strip()}

def docker_containers()->dict[str,Any]:
    try: result=subprocess.run(["docker","ps","--all","--no-trunc","--format","{{json .}}"],capture_output=True,text=True,timeout=5,check=False)
    except (FileNotFoundError,subprocess.TimeoutExpired): return {"available":False,"reason":"Docker CLI unavailable or timed out","containers":[]}
    if result.returncode!=0: return {"available":False,"reason":"Docker daemon unavailable","containers":[]}
    containers=[]
    for line in result.stdout.splitlines():
        try: item=json.loads(line)
        except json.JSONDecodeError: continue
        containers.append({"id":item.get("ID",""),"name":item.get("Names",""),"image":item.get("Image",""),"state":item.get("State",""),"status":item.get("Status","")})
    return {"available":True,"containers":containers}

def docker_container_action(container_id:str,action:str)->dict[str,Any]:
    """Run only an allowlisted Docker action on a currently listed container ID."""
    if action not in ALLOWED_DOCKER_ACTIONS: return {"ok":False,"error":"unsupported_action"}
    if not CONTAINER_ID_RE.fullmatch(container_id): return {"ok":False,"error":"invalid_container_id"}
    listing=docker_containers()
    if not listing["available"]: return {"ok":False,"error":"docker_unavailable"}
    match=next((c for c in listing["containers"] if c["id"]==container_id),None)
    if match is None: return {"ok":False,"error":"container_not_found"}
    try: result=subprocess.run(["docker",action,match["id"]],capture_output=True,text=True,timeout=15,check=False)
    except (FileNotFoundError,subprocess.TimeoutExpired): return {"ok":False,"error":"docker_cli_unavailable_or_timed_out"}
    if result.returncode!=0: return {"ok":False,"error":"docker_action_failed"}
    return {"ok":True,"action":action,"container_id":match["id"]}

def docker_server_create(name:str,template:str)->dict[str,Any]:
    """Create a constrained Docker container from a built-in template only."""
    if not isinstance(name,str) or not SERVER_NAME_RE.fullmatch(name):
        return {"ok":False,"error":"invalid_server_name"}
    if template not in SERVER_TEMPLATES:
        return {"ok":False,"error":"unsupported_template"}
    listing=docker_containers()
    if not listing["available"]:
        return {"ok":False,"error":"docker_unavailable"}
    if any(c["name"].lstrip("/") == name for c in listing["containers"]):
        return {"ok":False,"error":"server_name_exists"}
    spec=SERVER_TEMPLATES[template]
    command=["docker","run","-d","--name",name,"--memory=256m","--cpus=0.5","--pids-limit=128","--restart=no",spec["image"],*spec["command"]]
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=120,check=False)
    except (FileNotFoundError,subprocess.TimeoutExpired):
        return {"ok":False,"error":"docker_create_unavailable_or_timed_out"}
    if result.returncode!=0:
        return {"ok":False,"error":"docker_create_failed"}
    return {"ok":True,"name":name,"template":template,"image":spec["image"],"container_id":result.stdout.strip()[:64],"note":"Container created without host port publishing or host-volume mounts."}


def docker_server_delete(container_id:str)->dict[str,Any]:
    """Delete only a listed, stopped container; never delete its volumes."""
    if not isinstance(container_id,str) or not CONTAINER_ID_RE.fullmatch(container_id):
        return {"ok":False,"error":"invalid_container_id"}
    listing=docker_containers()
    if not listing["available"]:
        return {"ok":False,"error":"docker_unavailable"}
    match=next((c for c in listing["containers"] if c["id"]==container_id),None)
    if match is None:
        return {"ok":False,"error":"container_not_found"}
    if str(match.get("state","")).lower()=="running":
        return {"ok":False,"error":"stop_server_before_delete"}
    try:
        result=subprocess.run(["docker","rm",match["id"]],capture_output=True,text=True,timeout=20,check=False)
    except (FileNotFoundError,subprocess.TimeoutExpired):
        return {"ok":False,"error":"docker_delete_unavailable_or_timed_out"}
    if result.returncode!=0:
        return {"ok":False,"error":"docker_delete_failed"}
    return {"ok":True,"deleted_container_id":match["id"],"name":match.get("name","")}


class Handler(BaseHTTPRequestHandler):
    server_version="NeoOS-Server/0.2"
    def _send(self,status:int,payload:dict[str,Any],content_type:str="application/json; charset=utf-8")->None:
        body=json.dumps(payload,ensure_ascii=False).encode("utf-8") if content_type.startswith("application/json") else payload["raw"]
        self.send_response(status); self.send_header("Content-Type",content_type); self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store"); self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers(); self.wfile.write(body)
    def _authorized(self)->bool:
        supplied=self.headers.get("Authorization",""); expected="Bearer "+TOKEN if TOKEN else ""
        return bool(TOKEN) and hmac.compare_digest(supplied,expected)
    def do_GET(self)->None:
        path=urlparse(self.path).path
        if path=="/health": self._send(200,{"ok":True,"service":"neoos-server"}); return
        if path in ("/","/dashboard"):
            try: body=DASHBOARD_PATH.read_bytes()
            except OSError: self._send(500,{"error":"dashboard_unavailable"}); return
            self._send(200,{"raw":body},"text/html; charset=utf-8"); return
        if path not in ("/api/status","/api/docker","/api/containers"): self._send(404,{"error":"not_found"}); return
        if not self._authorized(): self._send(401,{"error":"unauthorized"}); return
        if path=="/api/status": self._send(200,system_status())
        elif path=="/api/docker": self._send(200,docker_status())
        else: self._send(200,docker_containers())
    def do_POST(self)->None:
        path=urlparse(self.path).path
        allowed={"/api/container-action","/api/server-create","/api/server-delete"}
        if path not in allowed: self._send(405,{"error":"method_not_allowed"}); return
        if not self._authorized(): self._send(401,{"error":"unauthorized"}); return
        try: length=int(self.headers.get("Content-Length","0"))
        except ValueError: length=0
        if length<1 or length>1024: self._send(400,{"error":"invalid_request_size"}); return
        try: body=json.loads(self.rfile.read(length))
        except (json.JSONDecodeError,UnicodeDecodeError): self._send(400,{"error":"invalid_json"}); return
        if not isinstance(body,dict) or body.get("confirm") is not True:
            self._send(400,{"error":"explicit_confirmation_required"}); return
        if path=="/api/server-create":
            name,template=body.get("name"),body.get("template")
            if not isinstance(name,str) or not isinstance(template,str):
                self._send(400,{"error":"name_and_template_required"}); return
            result=docker_server_create(name,template)
        elif path=="/api/server-delete":
            container_id=body.get("container_id")
            if not isinstance(container_id,str):
                self._send(400,{"error":"container_id_required"}); return
            result=docker_server_delete(container_id)
        else:
            container_id,action=body.get("container_id"),body.get("action")
            if not isinstance(container_id,str) or not isinstance(action,str):
                self._send(400,{"error":"container_id_and_action_required"}); return
            result=docker_container_action(container_id,action)
        if result.get("ok"): self._send(200,result)
        elif result.get("error")=="docker_unavailable": self._send(503,result)
        elif result.get("error")=="container_not_found": self._send(404,result)
        elif result.get("error") in ("unsupported_action","invalid_container_id","invalid_server_name","unsupported_template","server_name_exists","explicit_confirmation_required","stop_server_before_delete"): self._send(400,result)
        else: self._send(502,result)
    def log_message(self,fmt:str,*args:Any)->None: print("NeoOS Server:",fmt%args)

def main()->None:
    if not TOKEN or len(TOKEN)<24: raise SystemExit("Set NEOOS_SERVER_TOKEN to a random value of at least 24 characters.")
    server=ThreadingHTTPServer((HOST,PORT),Handler)
    print(f"NeoOS Server listening on {HOST}:{PORT}; authenticated API enabled.")
    print("Remote access: use SSH port forwarding; do not expose this port publicly.")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=="__main__": main()
