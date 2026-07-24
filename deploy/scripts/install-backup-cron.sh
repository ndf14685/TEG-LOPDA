#!/usr/bin/env bash
# Instala el cron diario de backup de la DB (05:00) si no está ya instalado.
set -e
REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LINE="0 5 * * * $REPO_DIR/deploy/scripts/backup.sh >> $REPO_DIR/backups/backup.log 2>&1"
( crontab -l 2>/dev/null | grep -vF "deploy/scripts/backup.sh"; echo "$LINE" ) | crontab -
echo "✅ cron instalado: $LINE"
