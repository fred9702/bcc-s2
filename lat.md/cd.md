# CD

Deployment workflow in [[.github/workflows/cd.yml]], triggered when CI succeeds on `main` (or manually). A matrix runs staging then prod sequentially (`max-parallel: 1`).

## Staging

A real deployment to an ephemeral minikube cluster inside the runner, so manifests, PSA and probes are exercised exactly as in the local simulation.

The image is built straight into minikube's Docker daemon, then `terragrunt plan` and `apply` run. Terraform's `wait_for_rollout` means the apply only succeeds once the startup/readiness probes pass, so no separate smoke-test step is kept (removed for speed and simplicity).

## Prod

Gated by the `prod` GitHub Environment, which requires manual approval and only deploys from protected branches.

It runs a real `terragrunt plan` with prod inputs (against minikube), then a mocked apply that logs the intended OIDC role assumption, EKS context switch and signed GHCR image.

## Placeholders

Slack/Teams notifications are mocked as a `::notice` annotation.
