IMAGE ?= bcc-s2
TAG   ?= local

.PHONY: install run test e2e lint docker-build docker-run

install:      ## install deps + git hooks
	uv sync && uv run pre-commit install
run:          ## run app locally on :8501
	uv run streamlit run src/bcc_s2/app.py
test:        ## native unit + Streamlit AppTest suite
	uv run pytest
e2e:          ## Playwright browser suite against a live server
	uv run playwright install chromium && uv run pytest -m e2e --no-cov
lint:         ## ruff, mypy, bandit, hadolint
	uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run bandit -q -r src -c pyproject.toml && hadolint Dockerfile
docker-build:
	docker build -t $(IMAGE):$(TAG) --build-arg APP_VERSION=$(TAG) .
docker-run:
	docker run --rm -p 8501:8501 -e APP_ENV=docker $(IMAGE):$(TAG)

# ---------- local Kubernetes (minikube + Terragrunt) ----------
ENV ?= staging
.PHONY: k8s-up k8s-deploy k8s-plan k8s-url k8s-destroy
k8s-up:       ## start minikube with metrics-server (for HPA)
	minikube start --driver=docker --cpus=2 --memory=3072 --addons=metrics-server
k8s-plan:
	cd infra/live/$(ENV) && IMAGE=$(IMAGE) IMAGE_TAG=$(TAG) terragrunt run --all --non-interactive -- plan
k8s-deploy: docker-build  ## build, load image into minikube, terragrunt apply ENV
	minikube image load $(IMAGE):$(TAG)
	cd infra/live/$(ENV) && IMAGE=$(IMAGE) IMAGE_TAG=$(TAG) terragrunt run --all --non-interactive -- apply -auto-approve
k8s-url:      ## port-forward the service to localhost:8080
	kubectl -n bcc-$(ENV) port-forward svc/bcc-dashboard 8080:80
k8s-destroy:
	cd infra/live/$(ENV) && terragrunt run --all --non-interactive -- destroy -auto-approve

# ---------- run GitHub Actions locally ----------
.PHONY: act act-list
act-list:     ## list workflow jobs act can run
	act -l
act:          ## run CI lint+test jobs locally (Apple silicon: amd64 runner image)
	act push -W .github/workflows/ci.yml -j lint -j test --container-architecture linux/amd64
