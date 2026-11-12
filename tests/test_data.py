from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from bcc_s2.config import load_settings
from bcc_s2.data import DataError, load_prices, load_surface


def test_load_prices_parses_and_sorts(prices_csv: Path) -> None:
    df = load_prices(prices_csv)
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert list(df["Ticker"].unique()) == ["AAA", "BBB"]


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="not found"):
        load_prices(tmp_path / "nope.csv")


def test_missing_columns_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.csv"
    p.write_text("Date,Close\n2024-01-01,1\n")
    with pytest.raises(DataError, match="missing columns"):
        load_prices(p)


def test_surface_rejects_non_positive_vol(tmp_path: Path) -> None:
    p = tmp_path / "s.csv"
    p.write_text("Tenor,Moneyness,ImpliedVol\n0.5,1.0,0.2\n0.5,1.1,-0.1\n")
    with pytest.raises(DataError, match="non-positive"):
        load_surface(p)


def test_committed_csvs_are_valid_and_configmap_sized() -> None:
    s = load_settings()
    assert s.prices_path.stat().st_size < 1024 * 1024
    assert "VOD.L" in set(load_prices(s.prices_path)["Ticker"])
    assert len(load_surface(s.surface_path)) > 0


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APP_ENV", "staging")
    s = load_settings()
    assert s.prices_path == tmp_path / "prices.csv"
    assert s.app_env == "staging"
