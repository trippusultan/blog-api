#!/usr/bin/env bash
# run.sh — bootstrap .env + start FastAPI dev server
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SP="${DIR}/venv/lib/python$(python3 -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages"
export PYTHONPATH="${SP}"

if [[ -f "${DIR}/.env" ]]; then
  set -a; source "${DIR}/.env"; set +a
fi

exec "${DIR}/venv/bin/uvicorn" main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8001}" --reload
