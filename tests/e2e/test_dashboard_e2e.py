"""Full browser tests (Playwright) against a live Streamlit server. Run: pytest -m e2e"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_title_and_kpis(dashboard: Page) -> None:
    expect(dashboard).to_have_title("BCC Market Dashboard")
    expect(dashboard.get_by_role("heading", name=re.compile("Market Dashboard"))).to_be_visible()
    expect(dashboard.get_by_test_id("stMetric")).to_have_count(5)
    expect(dashboard.get_by_test_id("stMetricLabel").first).to_contain_text("VOD.L last")


def test_sidebar_env_and_credit(dashboard: Page) -> None:
    sidebar = dashboard.get_by_test_id("stSidebar")
    expect(sidebar).to_contain_text("e2e")
    expect(sidebar.get_by_role("link", name="streamlit/demo-stockpeers")).to_be_visible()


def test_price_chart_renders(dashboard: Page) -> None:
    expect(dashboard.locator(".js-plotly-plot").first).to_be_visible(timeout=15_000)


@pytest.mark.parametrize(
    ("tab", "expected"),
    [
        ("Peers", "Normalised performance"),
        ("Risk", "Drawdown from peak"),
        ("Vol surface", "ATM term structure"),
        ("Data", "Download CSV"),
    ],
)
def test_tabs(dashboard: Page, tab: str, expected: str) -> None:
    dashboard.get_by_role("tab", name=tab).click()
    expect(dashboard.get_by_text(expected).first).to_be_visible(timeout=15_000)


def test_vol_surface_3d(dashboard: Page) -> None:
    dashboard.get_by_role("tab", name="Vol surface").click()
    # Plotly 3D surfaces render to a WebGL canvas
    expect(dashboard.locator(".js-plotly-plot .gl-container canvas").first).to_be_attached(
        timeout=15_000
    )


def test_change_focus_ticker(dashboard: Page) -> None:
    dashboard.get_by_test_id("stSidebar").get_by_test_id("stSelectbox").click()
    dashboard.get_by_role("option", name="VZ", exact=True).click()
    expect(dashboard.get_by_test_id("stMetricLabel").first).to_contain_text("VZ last")


def test_horizon_control_changes_total_return(dashboard: Page) -> None:
    total = dashboard.get_by_test_id("stMetricValue").nth(1)
    before = total.inner_text()
    dashboard.get_by_test_id("stSidebar").get_by_text("5Y", exact=True).click()
    expect(total).not_to_have_text(before, timeout=15_000)


def test_csv_download(dashboard: Page) -> None:
    dashboard.get_by_role("tab", name="Data").click()
    with dashboard.expect_download() as dl:
        dashboard.get_by_role("button", name="Download CSV").click()
    assert dl.value.suggested_filename == "prices_filtered.csv"
