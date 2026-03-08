#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${ROOT_DIR}/experiments"

source "${ROOT_DIR}/.venv/bin/activate"

python -m physics_ai.main_loop \
  --universe-count 32 \
  --generations 3 \
  --dynamics-type wave \
  --batch-size 8 \
  --checkpoint-dir "${RUN_DIR}"

LATEST_RUN=$(ls -d "${RUN_DIR}"/run_* 2>/dev/null | tail -n 1)
if [[ -n "${LATEST_RUN}" ]]; then
  python -m physics_ai.atlas_runner \
    --run-dir "${LATEST_RUN}" \
    --method umap \
    --output "${LATEST_RUN}/atlas.csv" \
    --plot "${LATEST_RUN}/atlas.png"
fi

echo "Pipeline complete. Latest run: ${LATEST_RUN:-none}"