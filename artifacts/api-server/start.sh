#!/bin/bash
set -e
cd "$(dirname "$0")"
PORT=${PORT:-8080}
python -m uvicorn main:app --reload --host 0.0.0.0 --port "$PORT" --log-level info
