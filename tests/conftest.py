from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def prices() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=5)
    rows = []
    for ticker, closes in {"AAA": [10, 11, 12, 9, 12], "BBB": [20, 20, 22, 22, 24]}.items():
        for d, c in zip(dates, closes, strict=True):
            rows.append(
                {
                    "Date": d,
                    "Ticker": ticker,
                    "Open": c,
                    "High": c,
                    "Low": c,
                    "Close": float(c),
                    "Volume": 100,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def prices_csv(tmp_path: Path, prices: pd.DataFrame) -> Path:
    p = tmp_path / "prices.csv"
    prices.to_csv(p, index=False)
    return p
