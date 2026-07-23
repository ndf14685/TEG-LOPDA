# Procedimiento de rollback

## 1. Volver al código anterior

```bash
cd /home/ndf/workspace/TEG-LOPDA
git log --oneline -5              # identificar el commit bueno (update.sh lo imprime)
git checkout <COMMIT_BUENO>
docker compose build backend
docker compose up -d backend
curl -sf http://127.0.0.1:8123/health && echo OK
```

## 2. Restaurar la base de datos (solo si hubo corrupción o migración fallida)

```bash
docker compose stop backend
ls backups/                        # elegir el backup
gunzip -k backups/teg-YYYYMMDD-HHMMSS.db.gz
cp backups/teg-YYYYMMDD-HHMMSS.db data/teg.db
rm -f data/teg.db-wal data/teg.db-shm
docker compose up -d backend
```

## 3. Verificar

```bash
curl -sf http://127.0.0.1:8123/health
docker compose logs backend --tail 30
```

Nota: las migraciones son solo hacia adelante (append-only). Si una migración
nueva rompió el esquema, restaurar el backup previo (paso 2) Y volver al
commit anterior (paso 1) juntos.
