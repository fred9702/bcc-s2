This directory defines the high-level concepts, business logic, and architecture of this project using markdown. It is managed by [lat.md](https://www.npmjs.com/package/lat.md) — a tool that anchors source code to these definitions. Install the `lat` command with `npm i -g lat.md` and run `lat --help`.

- [[architecture]] — components, layers and key design decisions
- [[data]] — market data snapshot (prices + vol surface) and its constraints
- [[app]] — Streamlit dashboard: configuration, data loading, analytics and views
- [[packaging]] — multi-stage uv Docker image, non-root runtime, healthcheck
- [[ci]] — GitHub Actions quality gates, security scans, image build and placeholders
- [[infra]] — Terraform Kubernetes module, Terragrunt environments, minikube simulation
- [[cd]] — staging deploy to minikube in Actions, approval-gated prod plan + mocked apply
