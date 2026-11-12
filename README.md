# bcc-s2

BlueCrest Capital – Stage 2 take-home: a containerised **Streamlit market dashboard** (price timeseries, peer comparison, implied-vol surface) that reads CSV data on startup, with GitHub Actions CI/CD, DevSecOps tooling, and a **Terraform + Terragrunt** Kubernetes deployment simulated on **minikube**.

## Quick start

```bash
uv sync
uv run pre-commit install
uv run streamlit run src/bcc_s2/app.py   # http://localhost:8501
uv run pytest
```

## Repo layout

| Path | Purpose |
|---|---|
| `src/bcc_s2/` | Streamlit app package |
| `scripts/fetch_data.py` | yfinance snapshot → `data/*.csv` |
| `tests/` | pytest: data, analytics, Streamlit AppTest |
| `lat.md/` | Architecture knowledge graph ([lat.md](https://www.npmjs.com/package/lat.md)) used with Claude Code |
| `PROMPTS.md` | AI usage and key prompts |

## AI usage

Built with Claude Code (Opus 5.5, paid subscription). See [PROMPTS.md](PROMPTS.md).
