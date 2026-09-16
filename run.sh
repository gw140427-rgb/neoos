#!/usr/bin/env bash
set -e
# run.sh — install dependencies and start the Mock VPS Service
# Usage: chmod +x run.sh && ./run.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Starting uvicorn on 0.0.0.0:8000..."
exec uvicorn app:app --host 0.0.0.0 --port 8000
