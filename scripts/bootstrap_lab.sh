#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python -m venv "${ROOT_DIR}/.venv"
source "${ROOT_DIR}/.venv/bin/activate"

pip install --upgrade pip
pip install -r "${ROOT_DIR}/requirements.txt"

python -m pytest -q "${ROOT_DIR}/tests/test_backend.py"

echo "Setup complete. Activate with: source ${ROOT_DIR}/.venv/bin/activate"