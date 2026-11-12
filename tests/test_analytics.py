from __future__ import annotations

import pandas as pd
import pytest

from bcc_s2 import analytics as a


@pytest.fixture
def closes(prices: pd.DataFrame) -> pd.DataFrame:
    return a.close_matrix(prices)


def test_normalise_starts_at_one(closes: pd.DataFrame) -> None:
    assert (a.normalise(closes).iloc[0] == 1.0).all()


def test_drawdown(closes: pd.DataFrame) -> None:
    dd = a.drawdown(closes)
    assert dd["AAA"].min() == pytest.approx(9 / 12 - 1)
    assert dd["BBB"].min() == 0


def test_peer_relative(closes: pd.DataFrame) -> None:
    rel = a.peer_relative(a.normalise(closes), "AAA")
    assert rel.iloc[-1] == pytest.approx((12 / 10) / (24 / 20))


def test_peer_relative_needs_peers(closes: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        a.peer_relative(a.normalise(closes[["AAA"]]), "AAA")


def test_summary(closes: pd.DataFrame) -> None:
    s = a.summary(closes)
    assert s.loc["AAA", "Total return"] == pytest.approx(0.2)
    assert s.loc["BBB", "Last"] == 24
    assert s.loc["AAA", "Ann. vol"] > 0


def test_rolling_vol_shape(closes: pd.DataFrame) -> None:
    assert a.rolling_vol(closes, window=2).shape[1] == 2
