"""Start a real Streamlit server for Playwright tests (session-scoped)."""

from __future__ import annotations

import os
import socket
import subprocess  # nosec B404 - launching our own app under test
import sys
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "src" / "bcc_s2" / "app.py"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope="session")
def app_url() -> Iterator[str]:
    port = _free_port()
    env = {**os.environ, "APP_ENV": "e2e", "APP_VERSION": "test"}
    proc = subprocess.Popen(  # noqa: S603  # nosec B603
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP),
            "--server.headless=true",
            f"--server.port={port}",
            "--browser.gatherUsageStats=false",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(60):
            try:
                if urllib.request.urlopen(f"{url}/_stcore/health", timeout=1).status == 200:  # noqa: S310  # nosec B310
                    break
            except OSError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Streamlit did not become healthy")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@pytest.fixture
def dashboard(page, app_url):  # type: ignore[no-untyped-def]
    """Page loaded and fully rendered (KPI tiles visible)."""
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(app_url)
    page.get_by_test_id("stMetric").first.wait_for(timeout=30_000)
    yield page
    assert not errors, f"JS errors: {errors}"
