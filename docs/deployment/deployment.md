# Despliegue

## Requisitos

Docker + Compose (ya instalados en el servidor). Alternativa sin Docker:
`uv` + systemd (`deploy/systemd/teg-backend.service`).

## Primera instalación

```bash
cd /home/ndf/workspace/TEG-LOPDA
./deploy/scripts/install.sh     # crea .env con admin token, build, up, healthcheck
# luego editar .env: TEG_PUBLIC_BASE_URL, TEG_CORS_ORIGINS, TEG_DOMAIN
docker compose restart backend
```

## Operación diaria

```bash
docker compose up -d backend      # levantar
docker compose stop backend       # detener
docker compose logs -f backend    # logs (JSON estructurado)
curl http://127.0.0.1:8123/health # healthcheck
curl http://127.0.0.1:8123/metrics # métricas (solo loopback)
./deploy/scripts/backup.sh        # backup de SQLite (retiene 14)
./deploy/scripts/update.sh        # actualizar (backup + git pull + rebuild)
```

Rollback: `deploy/scripts/rollback.md`.

Reinicio automático: `restart: unless-stopped` en compose + healthcheck del
contenedor. Con systemd: `Restart=always`.

## DNS y HTTPS

1. Crear un registro A en el DNS del dominio:
   `teg.tudominio.com  →  IP pública del servidor` (TTL 300 para probar).
2. Verificar propagación: `dig +short teg.tudominio.com`.
3. HTTPS automático con Caddy (perfil `edge` del compose): al primer request,
   Caddy obtiene el certificado de Let's Encrypt. Requiere puertos 80 y 443
   abiertos y el DNS apuntando. Alternativa nginx + certbot:
   `deploy/nginx/teg.conf.example`.

El dominio es configurable: `TEG_DOMAIN` (proxy) y `TEG_PUBLIC_BASE_URL`
(links de invitación) en `.env`.

## Exposición segura (Etapa 5)

Estado del servidor (relevado 2026-07-22): **el puerto 80 lo ocupa Apache con
Nextcloud — no se toca**. El 443 está libre. El backend TEG solo escucha en
`127.0.0.1:8123`. `ufw` requiere sudo con password.

Diseño: Caddy en contenedor publica **solo el 443** y obtiene el certificado
de Let's Encrypt por desafío **TLS-ALPN-01** (no necesita el puerto 80).
Consecuencia aceptada: no hay redirección http→https para el dominio del TEG
(el 80 responde Nextcloud); los join links ya se generan con `https://`.

Pasos:

```bash
# 1. DNS: registro A  teg.tudominio.com -> IP pública (lo hace el dueño del dominio)
dig +short teg.tudominio.com          # verificar propagación

# 2. Si el servidor está detrás de un router: redirigir el puerto externo 443
#    al 443 de esta máquina (igual que se haya hecho para Nextcloud con el 80).

# 3. Firewall (requiere sudo del operador):
sudo ufw status verbose               # si está inactivo, no hay nada que abrir
sudo ufw allow 443/tcp                # solo si ufw está activo

# 4. Configurar .env: TEG_DOMAIN, TEG_PUBLIC_BASE_URL=https://teg.tudominio.com,
#    TEG_CORS_ORIGINS=https://teg.tudominio.com  y levantar el edge:
docker compose --profile edge up -d

# 5. Verificar
curl -sI https://teg.tudominio.com/health
curl -sI https://teg.tudominio.com/metrics   # debe dar 404 (bloqueado en proxy)
```

Puertos expuestos resultantes: 443 (Caddy) únicamente; 8123 sigue en loopback.

Riesgos: (a) rate limit de Let's Encrypt si el DNS no propagó — verificar
`dig` antes de levantar el edge; (b) sin redirección :80 para este dominio
(ver arriba); (c) endpoint público — mitigado con tokens por jugador, rate
limiting, CORS restringido y `/metrics` bloqueado.

Rollback de la exposición:

```bash
docker compose --profile edge down   # baja Caddy; el backend sigue local
sudo ufw delete allow 443/tcp        # si se había abierto
```
