FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# UID/GID 1000 para que el bind mount ./data del host (dueño ndf) sea escribible
RUN groupadd -g 1000 teg && useradd -u 1000 -g teg -d /app teg

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY migrations ./migrations

RUN mkdir -p /app/data && chown -R teg:teg /app
USER teg

ENV TEG_HOST=0.0.0.0 TEG_PORT=8123 TEG_DB_PATH=/app/data/teg.db PYTHONPATH=/app/src

EXPOSE 8123

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["uv", "run", "--no-sync", "python", "-c", "import urllib.request,os,sys; sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"TEG_PORT\"]}/health', timeout=3).status == 200 else 1)"]

CMD ["sh", "-c", "uv run --no-sync uvicorn teg_backend.main:app --host $TEG_HOST --port $TEG_PORT"]
