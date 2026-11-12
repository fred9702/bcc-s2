"""Native Streamlit app tests (streamlit.testing.v1.AppTest): headless, no browser.

https://docs.streamlit.io/develop/concepts/app-testing
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[2] / "src" / "bcc_s2" / "app.py")


@pytest.fixture
def at() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception, app.exception
    return app


def test_renders_title_kpis_and_tabs(at: AppTest) -> None:
    assert at.title[0].value.startswith("📈")
    assert [m.label for m in at.metric] == [
        "VOD.L last",
        "Total return",
        "Ann. volatility",
        "Sharpe (rf=0)",
        "Max DD",
    ]
    assert [t.label for t in at.tabs] == ["Price", "Peers", "Risk", "Vol surface", "Data"]


def test_default_focus_and_peers(at: AppTest) -> None:
    assert at.selectbox[0].value == "VOD.L"
    assert "VOD.L" not in at.multiselect[0].value
    assert len(at.multiselect[0].value) == 7


def test_changing_focus_updates_kpis(at: AppTest) -> None:
    at.selectbox[0].select("VZ").run()
    assert not at.exception
    assert at.metric[0].label == "VZ last"
    assert "VZ" not in at.multiselect[0].value


def test_clearing_peers_shows_info(at: AppTest) -> None:
    at.multiselect[0].set_value([]).run()
    assert not at.exception
    assert any("at least one peer" in i.value for i in at.info)


@pytest.mark.parametrize("window", [5, 60, 120])
def test_rolling_window_slider(at: AppTest, window: int) -> None:
    at.slider[0].set_value(window).run()
    assert not at.exception
    assert any(f"Rolling {window}d" in h.value for h in at.subheader)


def test_sma_toggle(at: AppTest) -> None:
    at.toggle[0].set_value(False).run()
    assert not at.exception


def test_surface_tenor_select_slider(at: AppTest) -> None:
    at.select_slider[0].set_value(1.0).run()
    assert not at.exception


def test_sidebar_shows_env_and_credit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("APP_VERSION", "abc123")
    at = AppTest.from_file(APP, default_timeout=30).run()
    captions = " ".join(c.value for c in at.sidebar.caption)
    assert "staging" in captions and "abc123" in captions
    assert "demo-stockpeers" in captions


def test_missing_data_fails_fast(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert at.exception
    assert "data file not found" in at.exception[0].message
