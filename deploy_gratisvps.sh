#!/bin/bash
set -e
echo "[1/3] installing docker (GratisVPS/Ubuntu)"
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER || true
fi
echo "[2/3] pulling ubuntu image"
docker pull ubuntu:22.04 || true
echo "[3/3] starting VPS service"
pip install -q fastapi uvicorn[standard] pydantic 2>&1 | tail -n 3
uvicorn app_docker:app --host 0.0.0.0 --port 8000
