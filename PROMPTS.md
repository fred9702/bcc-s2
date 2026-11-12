# AI usage & key prompts

This project was built with **Claude Code** (Anthropic, model Claude Opus 5.5) on a paid subscription, driving the terminal, git, GitHub CLI and local tooling. The human role was product owner/architect: setting direction, challenging trade-offs, reviewing each stacked PR.

Prompts are quoted verbatim (lightly trimmed), in order.

## 1. Brief & ideas

> *(Pasted the BlueCrest brief)* "I'm going to share some ideas first and then we'll crack on."

> "Dataset: Kaggle stock-market dataset … Stock App: streamlit/demo-stockpeers … Containerised with Python Slim + Multi Stage build… UV or Poetry? Implement Act … Workflow with Matrix deployment to staging/prod? Terragrunt? DevSecOps applied … Minikube … Terraform + K8s provider: Create a Deployment module? Everything env var driven, Cloud Native principles. CSV mounted as a ConfigMap? Grafana/Prometheus? Dashboards as Code using JSONnet?"

Outcome: AI recommended uv, a committed CSV subset, real (free) security scanners in CI with mocks for paid tools, and flagged Grafana as a stretch goal.

## 2. Steering decisions

> "I wanted to look into Terragrunt because that's what BCC uses. I suggested minikube to simulate deployments as close to reality as possible. For stock peers, why don't we use a script that pulls <1MiB worth of yfinance data? … In my current role, we use Terraform K8s provider and build TF modules with it… Stacked PRs pls."

> "Wait, let's discuss Kustomize a bit more... Terragrunt essentially replaces Kustomize because it covers a wider range of providers, as opposed to just K8s?"

Outcome: AI clarified that breadth comes from Terraform (Terragrunt is a DRY/orchestration wrapper), and that Terragrunt env inputs replace Kustomize overlays when workloads are managed via the TF Kubernetes provider. Trade-off recorded in `lat.md/architecture.md`.

> "Call it bcc-s2. I also want lat.md initiated in the repo."

## 3. Data

> "For stock peers, why don't we use a script that pulls <1MiB worth of yfinance data? Reduces UI toil."

Decision (human): use a fetch script for recent data instead of the Kaggle stock-market dataset, which ends in 2020 (and needs a Kaggle login, so CI could not fetch it anyway).

Outcome: `scripts/fetch_data.py` snapshots VOD.L + 7 telecom peers (5y daily, ~560 KiB) and a synthetic vol surface. Size guard keeps it ConfigMap-compatible. A yfinance SQLite cache lock (`database is locked`) on concurrent downloads was fixed by the AI with `threads=False` and an empty-ticker guard.

## 4. App

> "Build the Streamlit app: read the CSVs at startup, VOD.L focus vs peers, make it as rich as possible within the time box. Keep analytics pure and tested."

Outcome: env-driven config, validated CSV loading, pure analytics module (100% covered), five tabs (candlestick+SMA, peer comparison & correlation, rolling vol/drawdown, 3D vol surface with smile/term-structure slices, data download). Verified visually with Playwright before opening the PR.
