"""Pure analytics on price data (no Streamlit imports, fully unit-testable)."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def close_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    """Wide Date x Ticker matrix of closes, forward-filled across market holidays."""
    wide = prices.pivot_table(index="Date", columns="Ticker", values="Close")
    return wide.sort_index().ffill()


def normalise(closes: pd.DataFrame) -> pd.DataFrame:
    """Rebase each column to 1.0 at its first valid observation."""
    return closes / closes.bfill().iloc[0]


def returns(closes: pd.DataFrame) -> pd.DataFrame:
    return closes.pct_change(fill_method=None).dropna(how="all")


def rolling_vol(closes: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Annualised rolling volatility of daily returns."""
    return pd.DataFrame(returns(closes).rolling(window).std() * np.sqrt(TRADING_DAYS))


def drawdown(closes: pd.DataFrame) -> pd.DataFrame:
    """Drawdown from running peak (0 = at peak, -0.2 = 20% below)."""
    return closes / closes.cummax() - 1


def peer_relative(normalised: pd.DataFrame, ticker: str) -> pd.Series:
    """Ticker's normalised price divided by the equal-weight average of its peers."""
    peers = normalised.drop(columns=[ticker])
    if peers.empty:
        raise ValueError("need at least one peer")
    return normalised[ticker] / peers.mean(axis=1)


def summary(closes: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker summary stats over the given window."""
    rets = returns(closes)
    total = closes.ffill().iloc[-1] / closes.bfill().iloc[0] - 1
    vol = rets.std() * np.sqrt(TRADING_DAYS)
    ann_ret = (1 + rets.mean()) ** TRADING_DAYS - 1
    out = pd.DataFrame(
        {
            "Last": closes.ffill().iloc[-1],
            "Total return": total,
            "Ann. vol": vol,
            "Sharpe (rf=0)": ann_ret / vol,
            "Max drawdown": drawdown(closes).min(),
        }
    )
    out.index.name = "Ticker"
    return out
