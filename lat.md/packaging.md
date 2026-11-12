# Packaging

The app ships as a two-stage Docker image defined in [[Dockerfile]].

## Build stage

Uses the official uv image to `uv sync --locked --no-dev` into `/app/.venv`, with the dependency layer cached separately from source.

## Runtime stage

`python:3.12-slim` with only the venv and `data/` copied in, running as non-root uid 10001.

Streamlit is configured via `STREAMLIT_*` env vars, `DATA_DIR=/app/data` is the baked-in default that Kubernetes overrides with a ConfigMap mount, and a `HEALTHCHECK` probes `/_stcore/health` (the same endpoint used by the Kubernetes probes).
