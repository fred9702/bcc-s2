"""CSV loading and validation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PRICE_COLUMNS = {"Date", "Ticker", "Open", "High", "Low", "Close", "Volume"}
SURFACE_COLUMNS = {"Tenor", "Moneyness", "ImpliedVol"}


class DataError(ValueError):
    """Raised when an input CSV is missing or malformed."""


def _read(path: Path, required: set[str]) -> pd.DataFrame:
    if not path.is_file():
        raise DataError(f"data file not found: {path}")
    df = pd.read_csv(path)
    missing = required - set(df.columns)
    if missing:
        raise DataError(f"{path.name} missing columns: {sorted(missing)}")
    if df.empty:
        raise DataError(f"{path.name} is empty")
    return df


def load_prices(path: Path) -> pd.DataFrame:
    """Load long-format OHLCV prices, parsed and sorted."""
    df = _read(path, PRICE_COLUMNS)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.dropna(subset=["Close"]).sort_values(["Ticker", "Date"]).reset_index(drop=True)


def load_surface(path: Path) -> pd.DataFrame:
    """Load the implied-vol surface (Tenor in years, Moneyness K/S)."""
    df = _read(path, SURFACE_COLUMNS)
    if (df["ImpliedVol"] <= 0).any():
        raise DataError(f"{path.name} contains non-positive vols")
    return df.sort_values(["Tenor", "Moneyness"]).reset_index(drop=True)
