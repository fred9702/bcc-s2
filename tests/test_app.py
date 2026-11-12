from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "src" / "bcc_s2" / "app.py")


def test_app_renders_without_exceptions() -> None:
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert at.title[0].value.startswith("📈")
    assert len(at.metric) == 5


def test_changing_focus_ticker() -> None:
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.selectbox[0].select("VZ").run()
    assert not at.exception
    assert at.metric[0].label == "VZ last"
