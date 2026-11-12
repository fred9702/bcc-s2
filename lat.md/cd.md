# CD

Deployment workflow in [[.github/workflows/cd.yml]], triggered when CI succeeds on `main` (or manually). A matrix runs staging then prod sequentially (`max-parallel: 1`).

## Staging

A real deployment to an ephemeral minikube cluster inside the runner, so manifests, PSA and probes are exercised exactly as in the local simulation.

The image is built straight into minikube's Docker daemon, then `terragrunt plan` and `apply` run, followed by a smoke test: rollout status, health endpoint and UI through the Service, and env vars inside the pod.

## Prod

Gated by the `prod` GitHub Environment, which requires manual approval and only deploys from protected branches.

It runs a real `terragrunt plan` with prod inputs (against minikube), then a mocked apply that logs the intended OIDC role assumption, EKS context switch and signed GHCR image.

## Placeholders

OWASP ZAP baseline DAST against staging and Slack/Teams notifications are mocked as `::notice` annotations.
