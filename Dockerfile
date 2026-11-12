# syntax=docker/dockerfile:1.7

# ---------- builder: resolve deps with uv into /app/.venv ----------
FROM ghcr.io/astral-sh/uv:0.9-python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# deps layer (cached unless lockfile changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# ---------- runtime: slim, non-root, no build tooling ----------
FROM python:3.12-slim-bookworm AS runtime
ARG APP_VERSION=dev
LABEL org.opencontainers.image.source="https://github.com/fred9702/bcc-s2" \
      org.opencontainers.image.title="bcc-s2" \
      org.opencontainers.image.version="${APP_VERSION}"
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app
WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app data ./data
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    APP_VERSION=${APP_VERSION} \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
USER 10001
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4).status != 200)"]
ENTRYPOINT ["python", "-m", "streamlit", "run", "/app/.venv/lib/python3.12/site-packages/bcc_s2/app.py"]
