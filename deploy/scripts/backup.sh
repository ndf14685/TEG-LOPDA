#!/usr/bin/env bash
# Backup consistente de SQLite (usa la API de backup, seguro con WAL activo).
set -euo pipefail
cd "$(dirname "$0")/../.."

DB="${1:-data/teg.db}"
OUT_DIR="backups"
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="${OUT_DIR}/teg-${STAMP}.db"

mkdir -p "${OUT_DIR}"

if [ ! -f "${DB}" ]; then
    echo ">> no existe ${DB}, nada que respaldar"
    exit 0
fi

if command -v sqlite3 >/dev/null; then
    sqlite3 "${DB}" ".backup '${OUT}'"
else
    docker compose exec -T backend uv run --no-sync python -c \
        "import sqlite3; src = sqlite3.connect('/app/data/teg.db'); dst = sqlite3.connect('/app/data/backup-tmp.db'); src.backup(dst); dst.close()"
    mv data/backup-tmp.db "${OUT}"
fi

gzip "${OUT}"
echo ">> backup: ${OUT}.gz"

# retener los últimos 14
ls -1t "${OUT_DIR}"/teg-*.db.gz 2>/dev/null | tail -n +15 | xargs -r rm --
