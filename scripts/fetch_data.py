"""Fetch a small (<1 MiB) market data snapshot and generate a synthetic vol surface.

Run once, commit the CSVs. The app reads them at startup; CI never hits yfinance.

    uv run --group data python scripts/fetch_data.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

# European & US telecom peers around Vodafone (VOD.L).
TICKERS = ["VOD.L", "BT-A.L", "ORA.PA", "DTE.DE", "TEF.MC", "VZ", "T", "TMUS"]
MAX_BYTES = 1024 * 1024  # must fit in a Kubernetes ConfigMap


def fetch_prices(tickers: list[str], period: str) -> pd.DataFrame:
    raw = yf.download(
        tickers,
        period=period,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=False,
    )
    frames = []
    for t in tickers:
        df = raw[t].dropna(how="all").reset_index()
        if df.empty:
            raise SystemExit(f"no data returned for {t}")
        df["Ticker"] = t
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out = out[["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]]
    out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    out[["Open", "High", "Low", "Close"]] = out[["Open", "High", "Low", "Close"]].round(4)
    out["Volume"] = out["Volume"].fillna(0).astype("int64")
    return out.sort_values(["Ticker", "Date"])


def vol_surface() -> pd.DataFrame:
    """Synthetic implied-vol surface: ATM term structure + skew + smile (SVI-like)."""
    moneyness = np.round(np.arange(0.70, 1.31, 0.05), 2)
    tenors = np.array([1 / 12, 2 / 12, 3 / 12, 6 / 12, 9 / 12, 1.0, 1.5, 2.0])
    rows = []
    for t in tenors:
        atm = 0.18 + 0.06 * np.exp(-3 * t)  # downward-sloping term structure
        for m in moneyness:
            k = np.log(m)
            skew = -0.25 * k / np.sqrt(t)
            smile = 0.6 * k**2 / np.sqrt(t)
            rows.append(
                {
                    "Tenor": round(float(t), 4),
                    "Moneyness": float(m),
                    "ImpliedVol": round(float(atm + skew * 0.3 + smile * 0.3), 4),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--period", default="5y")
    p.add_argument("--out", type=Path, default=Path("data"))
    args = p.parse_args()
    args.out.mkdir(exist_ok=True)

    prices_path = args.out / "prices.csv"
    fetch_prices(TICKERS, args.period).to_csv(prices_path, index=False)
    size = prices_path.stat().st_size
    if size > MAX_BYTES:
        raise SystemExit(f"{prices_path} is {size} bytes (> 1 MiB); use a shorter --period")

    vol_surface().to_csv(args.out / "vol_surface.csv", index=False)
    print(f"wrote {prices_path} ({size / 1024:.0f} KiB) and vol_surface.csv")


if __name__ == "__main__":
    main()
