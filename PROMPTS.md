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

> "Did you credit the authors of the dashboard?"

Outcome: credits for streamlit/demo-stockpeers (Apache-2.0, concept only, no code copied) and yfinance added to README and the app sidebar.

## 5. Docker

> "Containerised with Python Slim + Multi Stage build… UV or Poetry?" → uv.

Outcome: uv builder stage → `python:3.12-slim` runtime, non-root, healthcheck, OCI labels. AI hit and fixed two issues: hadolint DL3025 (healthcheck in shell form) and a missing `buildx` plugin on the local Colima Docker setup.

## 6. CI

> "DevSecOps applied … Please add placeholders for any tooling you want to implement … mock functionality by printing a message on the action's logs."

Outcome: lint/test/security gates → image build, container smoke test, Trivy, Syft SBOM, GHCR push on main. Placeholders (SonarQube, Snyk, licenses, cosign) emit `::notice` annotations. While pinning, the AI found `trivy-action@0.28.0` no longer resolves (old tags removed after the March 2026 tag-repointing incident) and pinned v0.36.0 by commit SHA. actionlint caught a shellcheck warning.

> "Only run GHA on main, there's limited credits on the Free tier."

Outcome: CI triggers on `push: main` + `workflow_dispatch` only; PR branches are validated locally with `act`.

## 7. Infrastructure

> "In my current role, we use Terraform K8s provider and build TF modules with it… I wanted to look into Terragrunt because that's what BCC uses. I suggested minikube to simulate deployments as close to reality as possible."

Outcome: `infra/modules/streamlit-app` (namespace with PSA `restricted`, CSV ConfigMap with checksum-triggered rollouts, hardened Deployment, Service, HPA, PDB, NetworkPolicy) and a Terragrunt `live/` tree (`root.hcl` generating provider/backend, `_envcommon`, staging/prod inputs). Applied for real to minikube. The first apply hung: PSA rejected pods because the Kubernetes provider sends container-level `runAsNonRoot=false` by default; the AI diagnosed it from namespace events and set it explicitly.

> "Add classic GH rulesets for bcc-s2 via gh cli: main-branch-protection, require-pr-and-status-checks (and any other recommended)"

Outcome: three rulesets via `gh api` (main: no deletion/force-push; PR + required checks with admin PR-bypass, since CI is billing-blocked and main-only; release tags `v*` immutable), plus secret scanning push protection and Dependabot alerts/security updates.

## 8. CD

> "Workflow with Matrix deployment to staging/prod?" … "I suggested minikube to simulate deployments as close to reality as possible."

Outcome: `cd.yml` runs after CI on main. Matrix (staging → prod, sequential): staging is a real minikube deploy inside the runner with smoke tests; prod is approval-gated (GitHub Environment with required reviewer), runs a real `terragrunt plan` with prod inputs and a mocked apply. ZAP DAST and notifications are placeholders.

## 9. App testing

> "Implement Native App Testing for the Streamlit App (docs.streamlit.io/develop/concepts/app-testing). Native App Tests run on branches and full Playwright testing on PRs into main. Run everything from pytest."

Outcome: `tests/app/` AppTest suite (widgets, tabs, env, fail-fast) and `tests/e2e/` pytest-playwright suite against a live server started by a session fixture. `pytest` runs native, `pytest -m e2e` runs browser tests. New `app-tests.yml`: native on branch pushes, Playwright on PRs into main. The AI found `st.cache_data` leaking between AppTest runs (missing-data test passed on cached prices) and added a cache-clearing fixture; a segmented-control locator was fixed by asserting on behaviour (total return changes) rather than a role.

> "Ensure you use the Playwright base image for those tests + use pytest-xdist to run tests in parallel where appropriate"

Outcome: the e2e job runs in `mcr.microsoft.com/playwright/python:v1.65.1-noble` (with `--ipc=host`), and `playwright` is pinned to exactly 1.65.1 so library and browsers always match. `make e2e` uses the same image. pytest-xdist parallelises e2e (21s → 12s on the host); the native suite stays serial because xdist gave no gain at ~5s. The AI found `-n auto` failing locally from memory starvation (4 servers + 4 Chromiums in a Colima VM shared with minikube) and set local workers to 2, keeping `-n auto` on 16 GB CI runners.

## 10. Docs

> "Please add placeholders for any tooling … please include key prompts."

Outcome: README with a Mermaid architecture diagram, features, pipeline table, design decisions, known limitations, credits; `make act` / `make act-list` to run CI jobs locally.

## How AI was used (summary)

- **Claude Code did the hands-on work**: scaffolding, code, tests, Dockerfile, Terraform/Terragrunt, workflows, docs. It ran every tool locally (pytest, ruff, mypy, bandit, pip-audit, hadolint, actionlint, terraform, terragrunt, minikube, Playwright), and opened each stacked PR via `gh`.
- **The human steered and reviewed**: chose the stack (Terragrunt, minikube, Terraform k8s provider, uv, stacked PRs), challenged trade-offs (Kustomize vs Terragrunt), caught the missing credits, set CI cost constraints, asked for native + Playwright testing, reviewed and merged every PR.
- **The AI found and fixed real issues**: yfinance cache lock, hadolint DL3025, missing buildx, PSA rejection from the provider's `runAsNonRoot` default, `st.cache_data` leaking across AppTest runs, a deleted `trivy-action` tag, and a GitHub billing lock blocking Actions.
- **lat.md** kept a live architecture knowledge graph (`lat.md/`) that the agent updated and validated (`lat check`) with every PR.
