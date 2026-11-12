# Infrastructure

Kubernetes resources are defined as a reusable Terraform module (Kubernetes provider) and instantiated per environment with Terragrunt, simulated locally on minikube.

## Module

[[infra/modules/streamlit-app]] creates a namespace, a ConfigMap holding the CSVs, a Deployment, Service, Ingress, HPA, PodDisruptionBudget and NetworkPolicy.

The namespace enforces Pod Security Admission `restricted`. Pods run non-root with a read-only root filesystem, all capabilities dropped and seccomp `RuntimeDefault`. `/tmp` is an emptyDir and `HOME=/tmp` so Streamlit can write its cache.

The container's `runAsNonRoot` must be set explicitly: the provider otherwise sends `false` at container level, which overrides the pod setting and PSA rejects the pod.

## Data via ConfigMap

The CSVs are mounted read-only at `/data` and `DATA_DIR=/data` points the app at them, overriding the copy baked into the image.

A `checksum/data` pod annotation (sha256 of the ConfigMap content) rolls the Deployment whenever the data changes. The 1 MiB ConfigMap limit is why the data snapshot is size-guarded.

## Rollout and scaling

Rolling updates use `maxUnavailable=0, maxSurge=1`, gated by startup, readiness and liveness probes on `/_stcore/health`. Terraform waits for the rollout.

The HPA scales on CPU between `replicas` and `max_replicas`; Terraform ignores live replica drift because the HPA owns it. A PDB is created only when `replicas > 1`.

## Terragrunt layout

[[infra/live/root.hcl]] generates the provider and backend for every unit; [[infra/live/_envcommon/streamlit-app.hcl]] holds the shared unit definition.

Each environment has an `env.hcl` (name, kube context) and a `streamlit-app/terragrunt.hcl` with its own inputs: staging runs 1–2 replicas, prod 2–5 with larger requests/limits.

State is local for the simulation; the S3 backend with native lockfile locking is stubbed in `root.hcl` for a real account. `IMAGE`, `IMAGE_TAG`, `KUBE_CONTEXT` and `KUBECONFIG` come from the environment.

## Ingress

An optional `kubernetes_ingress_v1` (on by default) routes `ingress_host` to the Service through ingress-nginx, installed by minikube's `ingress` addon.

Hosts use `*.localhost` (`bcc-staging.localhost`, `bcc.localhost`), which resolve to 127.0.0.1 without DNS or `/etc/hosts` edits. On macOS with the docker driver the controller is only reachable via `minikube tunnel`.

Proxy read/send timeouts are raised to 3600s because Streamlit holds one websocket per session and nginx's 60s default drops idle sessions. TLS via cert-manager is a noted TODO for prod.
