# Architecture

High-level view of the bcc-s2 system: a Streamlit market dashboard packaged as a container and deployed to Kubernetes via Terraform modules orchestrated by Terragrunt.

## Components

The system is split into an app layer, a packaging layer and an infrastructure layer.

- **App**: Python package in [[src/bcc_s2]], a Streamlit dashboard that loads market data from CSV at startup.
- **Packaging**: multi-stage Docker image built with uv.
- **Infrastructure**: Terraform module using the Kubernetes provider, with Terragrunt providing per-environment (staging/prod) configuration.
- **CI/CD**: GitHub Actions running lint, tests, security scans, image build and a minikube deployment.

## Design decisions

Key choices and their trade-offs.

### uv over Poetry

uv gives faster resolution, a single lockfile and a simple multi-stage Docker build.

### Terragrunt over Kustomize

Terraform with the Kubernetes provider manages workloads; Terragrunt env folders replace Kustomize overlays.
