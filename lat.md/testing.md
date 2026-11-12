# Testing

Everything runs through pytest, at three levels. Plain `pytest` runs unit and native app tests; `pytest -m e2e` runs the browser suite (excluded by default via `addopts`).

## Unit tests

[[tests/test_data.py]] and [[tests/test_analytics.py]] cover CSV validation, env-driven settings and the pure analytics functions, including a check that the committed CSVs are valid and ConfigMap-sized.

## Native app tests

[[tests/app/test_app_native.py]] uses Streamlit's headless `AppTest` to run the script and drive widgets without a browser: focus/peer selection, empty peers, rolling window, SMA toggle, tenor slider, sidebar env/credit, and fail-fast on missing data.

`st.cache_data` is process-wide, so an autouse fixture in [[tests/app/conftest.py]] clears it around each test; without it the missing-data test silently reuses cached prices.

## Playwright e2e

[[tests/e2e/test_dashboard_e2e.py]] drives Chromium against a real server started by the session fixture in [[tests/e2e/conftest.py]] on a free port.

Covers title/KPIs, sidebar, Plotly rendering, every tab, the WebGL vol surface, changing focus ticker, horizon changing the total return, and the CSV download. The page fixture fails a test on any uncaught JS error.

## Where they run

[[.github/workflows/app-tests.yml]] runs native tests on every non-main branch push and the Playwright suite on PRs into `main`. CI on `main` runs the default suite.

The e2e job runs inside the official `mcr.microsoft.com/playwright/python` image (browsers and system deps preinstalled), whose tag must match the exact `playwright` pin in `pyproject.toml`. `make e2e` uses the same image locally.

## Parallelism

The e2e suite runs under pytest-xdist (`-n auto` in CI); each worker starts its own Streamlit server on a free port via the session fixture.

The native suite stays serial: at ~5 s, xdist worker startup costs as much as it saves. Locally `make e2e` defaults to 2 workers because each worker is a server plus a Chromium and starves a small Docker VM.
