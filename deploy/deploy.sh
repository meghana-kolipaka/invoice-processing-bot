#!/usr/bin/env bash
# Simple deployment script: install dependencies, run the tests, and stop if anything fails.
# Usage: ./deploy/deploy.sh   (run from the project folder on the target machine)
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[1/4] Creating virtual environment"
python3 -m venv .venv
source .venv/bin/activate
echo "[2/4] Installing dependencies"
pip install -q -r requirements.txt
echo "[3/4] Running tests"
python -m pytest -q
echo "[4/4] Creating folders"
mkdir -p input logs reports archive
echo "Deployment OK. Start the API with: python main.py api"
