IMAGE ?= bcc-s2
TAG   ?= local

.PHONY: install run test e2e e2e-local lint docker-build docker-run

install:      ## install deps + git hooks
	uv sync && uv run pre-commit install
run:          ## run app locally on :8501
	uv run streamlit run src/bcc_s2/app.py
test:        ## native unit + Streamlit AppTest suite
	uv run pytest
PW_IMAGE ?= mcr.microsoft.com/playwright/python:v1.65.1-noble
E2E_WORKERS ?= 2   # each worker = Streamlit server + Chromium; raise if Docker has the RAM
e2e:          ## Playwright suite in the official Playwright image (same as CI), parallel
	docker run --rm --ipc=host -v "$(CURDIR)":/work -w /work \
	  -e UV_PROJECT_ENVIRONMENT=/opt/venv -e UV_PYTHON_DOWNLOADS=never $(PW_IMAGE) \
	  bash -c "pip install -q --break-system-packages uv && uv sync -q --locked && uv run pytest -m e2e --no-cov -n $(E2E_WORKERS) -p no:cacheprovider"
e2e-local:    ## Playwright suite on the host (faster iteration)
	uv run playwright install chromium && uv run pytest -m e2e --no-cov -n auto
lint:         ## ruff, mypy, bandit, hadolint
	uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run bandit -q -r src -c pyproject.toml && hadolint Dockerfile
docker-build:
	docker build -t $(IMAGE):$(TAG) --build-arg APP_VERSION=$(TAG) .
docker-run:
	docker run --rm -p 8501:8501 -e APP_ENV=docker $(IMAGE):$(TAG)

# ---------- local Kubernetes (minikube + Terragrunt) ----------
ENV ?= staging
.PHONY: k8s-up k8s-deploy k8s-plan k8s-url k8s-tunnel k8s-destroy
k8s-up:       ## start minikube with metrics-server (HPA) and ingress-nginx
	minikube start --driver=docker --cpus=2 --memory=3072 --addons=metrics-server --addons=ingress
k8s-plan:
	cd infra/live/$(ENV) && IMAGE=$(IMAGE) IMAGE_TAG=$(TAG) terragrunt run --all --non-interactive -- plan
k8s-deploy: docker-build  ## build, load image into minikube, terragrunt apply ENV
	minikube image load $(IMAGE):$(TAG)
	cd infra/live/$(ENV) && IMAGE=$(IMAGE) IMAGE_TAG=$(TAG) terragrunt run --all --non-interactive -- apply -auto-approve
k8s-tunnel:   ## expose the Ingress on 127.0.0.1:80/443 (macOS docker driver); keep running, may ask for sudo
	minikube tunnel
k8s-url:      ## fallback: port-forward the Service to localhost:8080
	kubectl -n bcc-$(ENV) port-forward svc/bcc-dashboard 8080:80
k8s-destroy:
	cd infra/live/$(ENV) && terragrunt run --all --non-interactive -- destroy -auto-approve

# ---------- run GitHub Actions locally (act) ----------
# Host-specific flags must be on the command line: act refuses them in a project .actrc.
# /var/run/docker.sock is the daemon socket *inside* the Colima/Docker Desktop VM.
ACT_FLAGS ?= --container-daemon-socket /var/run/docker.sock --artifact-server-path .act/artifacts
ACT_PUSH  = act push -e .github/act/push.json $(ACT_FLAGS)
.PHONY: act act-list act-ci act-image act-native act-e2e
act-list:     ## list the jobs act can run
	act -l
CI_GATES ?= lint test security infra
act-ci:       ## CI quality gates, one act run per job (act's -j takes a single job; the last one wins)
	@set -e; for j in $(CI_GATES); do echo "==> act: ci.yml / $$j"; \
	  $(ACT_PUSH) -W .github/workflows/ci.yml -j $$j; done
act-image:    ## CI image job (runs the gates first via needs:) - slow
	$(ACT_PUSH) -W .github/workflows/ci.yml -j image
act-native:   ## app-tests: native AppTest job (branch push)
	$(ACT_PUSH) -W .github/workflows/app-tests.yml -j native
act-e2e:      ## app-tests: Playwright job in the Playwright image (PR into main)
	act pull_request -e .github/act/pull_request.json $(ACT_FLAGS) \
	  -W .github/workflows/app-tests.yml -j e2e --env E2E_WORKERS=$(E2E_WORKERS)
act: act-ci act-native  ## default: everything that runs on a branch/main push except the image build
