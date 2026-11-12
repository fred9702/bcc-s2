# bcc-s2

BlueCrest Capital – Stage 2 take-home: a containerised **Streamlit market dashboard** (price timeseries, peer comparison, implied-vol surface) that reads CSV data on startup, with GitHub Actions CI/CD, DevSecOps tooling, and a **Terraform + Terragrunt** Kubernetes deployment simulated on **minikube**.

## Quick start

```bash
uv sync
uv run pre-commit install
uv run streamlit run src/bcc_s2/app.py   # http://localhost:8501
uv run pytest                          # unit + native Streamlit AppTest
make e2e                               # Playwright browser tests (pytest -m e2e)
make docker-build docker-run           # containerised
```

## Local Kubernetes (minikube + Terragrunt)

```bash
make k8s-up                   # minikube + metrics-server
make k8s-deploy ENV=staging   # build image, load into minikube, terragrunt apply
make k8s-url ENV=staging      # http://localhost:8080
make k8s-destroy ENV=staging
```

## Repo layout

| Path | Purpose |
|---|---|
| `src/bcc_s2/` | Streamlit app package |
| `scripts/fetch_data.py` | yfinance snapshot → `data/*.csv` |
| `tests/` | pytest: unit, `app/` native AppTest, `e2e/` Playwright |
| `infra/modules/streamlit-app/` | Terraform module (Kubernetes provider) |
| `infra/live/` | Terragrunt: `root.hcl`, `_envcommon/`, `staging/`, `prod/` |
| `lat.md/` | Architecture knowledge graph ([lat.md](https://www.npmjs.com/package/lat.md)) used with Claude Code |
| `PROMPTS.md` | AI usage and key prompts |

## Credits

- Dashboard concept (focus stock vs peers, rebased performance, stock-vs-peer-average view) inspired by [streamlit/demo-stockpeers](https://github.com/streamlit/demo-stockpeers) by the Streamlit team (Apache-2.0). This app is a re-implementation reading from CSV rather than live yfinance calls; no code was copied.
- Market data from Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance) (for personal/educational use).

## AI usage

Built with Claude Code (Opus 5.5, paid subscription). See [PROMPTS.md](PROMPTS.md).
