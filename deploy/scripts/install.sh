#!/usr/bin/env bash
# Instalación inicial en el servidor (idempotente).
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ ! -f .env ]; then
    cp .env.example .env
    TOKEN=$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-40)
    sed -i "s|^TEG_ADMIN_TOKEN=.*|TEG_ADMIN_TOKEN=${TOKEN}|" .env
    echo ">> .env creado con TEG_ADMIN_TOKEN generado."
    echo ">> EDITAR .env: TEG_PUBLIC_BASE_URL, TEG_CORS_ORIGINS, TEG_DOMAIN."
fi

mkdir -p data backups

docker compose build
docker compose up -d backend

echo ">> esperando healthcheck..."
for i in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:$(grep -oP '^TEG_PORT=\K.*' .env || echo 8123)/health" >/dev/null; then
        echo ">> backend OK: http://127.0.0.1:$(grep -oP '^TEG_PORT=\K.*' .env || echo 8123)/health"
        exit 0
    fi
    sleep 1
done
echo "!! el backend no respondió al healthcheck" >&2
docker compose logs backend | tail -20
exit 1
