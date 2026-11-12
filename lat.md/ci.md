# CI

GitHub Actions pipeline in [[.github/workflows/ci.yml]], run on pushes to `main` and manual dispatch only, to conserve free-tier minutes; branch and PR app tests run in a separate lean workflow (see [[testing#Where they run]]).

Free, real tools run for real; paid tools are placeholders that log what they would do.

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

## Running locally with act

Make targets wrap act with the flags verified on Colima/Apple silicon; payloads for `push` and `pull_request` live in `.github/act/`.

act refuses host-touching flags (`--container-daemon-socket`, `--artifact-server-path`) in a project `.actrc`, so they live in `ACT_FLAGS` in the Makefile. Steps that cannot work under act are guarded with `!env.ACT`: the gitleaks action (needs a real push payload) and artifact upload inside the Playwright container (no Node).
