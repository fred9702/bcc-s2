# CI

GitHub Actions pipeline in [[.github/workflows/ci.yml]], run on every PR and on `main`. Free, real tools run for real; paid tools are placeholders that log what they would do.

## Quality gates

Parallel `lint`, `test` and `security` jobs must pass before the image is built.

- **lint**: ruff (lint + format), mypy strict, hadolint, `lat check`.
- **test**: pytest with coverage; JUnit + coverage XML uploaded as artifacts.
- **security**: bandit (SAST), pip-audit (dependency CVEs, strict), gitleaks (secrets), checkov (Dockerfile/Terraform/Actions misconfig, soft-fail).

## Image

Builds with buildx and GHA layer cache, runs a container smoke test on the health endpoint, scans with Trivy (SARIF), and generates an SPDX SBOM with Syft.

Pushes to GHCR only on `main`, tagged with the short SHA and `latest`.

## Placeholders

Mocked steps emit `::notice` annotations so they are visible in the run summary: SonarQube quality gate, Snyk, license compliance, cosign keyless signing and SBOM attestation.

## Supply chain

Dependabot tracks Actions, uv, Docker and Terraform. Trivy's action is pinned by commit SHA because its old tags were repointed in March 2026; pinning every action by SHA is the next hardening step.
