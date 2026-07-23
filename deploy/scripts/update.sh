#!/usr/bin/env bash
# Actualización con backup previo y rollback documentado (deploy/scripts/rollback.md).
set -euo pipefail
cd "$(dirname "$0")/../.."

echo ">> backup previo a actualizar"
./deploy/scripts/backup.sh

PREV_COMMIT=$(git rev-parse HEAD)
echo ">> commit actual: ${PREV_COMMIT} (anotalo para rollback)"

git pull --ff-only

docker compose build backend
docker compose up -d backend

sleep 3
PORT=$(grep -oP '^TEG_PORT=\K.*' .env || echo 8123)
if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; then
    echo ">> actualización OK"
else
    echo "!! healthcheck falló tras actualizar; ver deploy/scripts/rollback.md" >&2
    exit 1
fi
