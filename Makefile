IMAGE ?= bcc-s2
TAG   ?= local

.PHONY: install run test lint docker-build docker-run

install:      ## install deps + git hooks
	uv sync && uv run pre-commit install
run:          ## run app locally on :8501
	uv run streamlit run src/bcc_s2/app.py
test:
	uv run pytest
lint:         ## ruff, mypy, bandit, hadolint
	uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run bandit -q -r src -c pyproject.toml && hadolint Dockerfile
docker-build:
	docker build -t $(IMAGE):$(TAG) --build-arg APP_VERSION=$(TAG) .
docker-run:
	docker run --rm -p 8501:8501 -e APP_ENV=docker $(IMAGE):$(TAG)
