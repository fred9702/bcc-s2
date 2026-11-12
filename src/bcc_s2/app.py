"""Streamlit market dashboard: timeseries, peers, risk and implied-vol surface.

Run: uv run streamlit run src/bcc_s2/app.py
"""

from __future__ import annotations

import logging

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from bcc_s2 import analytics as a
from bcc_s2.config import load_settings
from bcc_s2.data import load_prices, load_surface

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("bcc_s2")

st.set_page_config(page_title="BCC Market Dashboard", page_icon="📈", layout="wide")
settings = load_settings()


@st.cache_data
def get_prices() -> pd.DataFrame:
    df = load_prices(settings.prices_path)
    log.info("loaded %d price rows from %s", len(df), settings.prices_path)
    return df


@st.cache_data
def get_surface() -> pd.DataFrame:
    df = load_surface(settings.surface_path)
    log.info("loaded %d surface points from %s", len(df), settings.surface_path)
    return df


prices = get_prices()
surface = get_surface()
tickers = sorted(prices["Ticker"].unique())

# ---------- sidebar ----------
with st.sidebar:
    st.header("Controls")
    focus = st.selectbox(
        "Focus ticker",
        tickers,
        index=tickers.index(settings.default_ticker) if settings.default_ticker in tickers else 0,
    )
    peers = st.multiselect(
        "Peers", [t for t in tickers if t != focus], default=[t for t in tickers if t != focus]
    )
    lo, hi = prices["Date"].min().date(), prices["Date"].max().date()
    horizon = st.segmented_control(
        "Horizon", ["3M", "6M", "1Y", "3Y", "5Y"], default="1Y", key="horizon"
    )
    months = {"3M": 3, "6M": 6, "1Y": 12, "3Y": 36, "5Y": 60}[horizon or "1Y"]
    start = max(lo, (pd.Timestamp(hi) - pd.DateOffset(months=months)).date())
    window = st.slider("Rolling window (days)", 5, 120, 20)
    st.caption(f"Data: {lo} → {hi} · {len(tickers)} tickers")
    st.caption(f"env **{settings.app_env}** · version `{settings.app_version}`")
    st.caption(
        "Inspired by [streamlit/demo-stockpeers](https://github.com/streamlit/demo-stockpeers)"
        " (Apache-2.0) · data: Yahoo Finance via yfinance"
    )

selected = [focus, *peers]
closes_all = a.close_matrix(prices)[selected]
closes = closes_all.loc[pd.Timestamp(start) :]

st.title("📈 Market Dashboard")
st.caption(f"{focus} vs telecom peers · daily adjusted closes · local currencies")

# ---------- KPI tiles ----------
s = a.summary(closes)
c1, c2, c3, c4, c5 = st.columns(5)
last, prev = closes[focus].iloc[-1], closes[focus].iloc[-2]
c1.metric(f"{focus} last", f"{last:,.2f}", f"{(last / prev - 1):+.2%} 1D")
c2.metric("Total return", f"{s.loc[focus, 'Total return']:+.1%}")
c3.metric("Ann. volatility", f"{s.loc[focus, 'Ann. vol']:.1%}")
c4.metric("Sharpe (rf=0)", f"{s.loc[focus, 'Sharpe (rf=0)']:.2f}")
c5.metric("Max drawdown", f"{s.loc[focus, 'Max drawdown']:.1%}")

tab_price, tab_peers, tab_risk, tab_surface, tab_data = st.tabs(
    ["Price", "Peers", "Risk", "Vol surface", "Data"]
)

# ---------- Price ----------
with tab_price:
    ohlc = prices[(prices["Ticker"] == focus) & (prices["Date"] >= pd.Timestamp(start))]
    ohlc = ohlc.set_index("Date")
    show_sma = st.toggle("Show SMA 20/50", value=True)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03
    )
    fig.add_trace(
        go.Candlestick(
            x=ohlc.index,
            open=ohlc["Open"],
            high=ohlc["High"],
            low=ohlc["Low"],
            close=ohlc["Close"],
            name=focus,
        ),
        1,
        1,
    )
    if show_sma:
        full = prices[prices["Ticker"] == focus].set_index("Date")["Close"]
        for n in (20, 50):
            sma = full.rolling(n).mean().loc[pd.Timestamp(start) :]
            fig.add_trace(
                go.Scatter(x=sma.index, y=sma, name=f"SMA {n}", line={"width": 1.5}), 1, 1
            )
    fig.add_trace(go.Bar(x=ohlc.index, y=ohlc["Volume"], name="Volume", opacity=0.5), 2, 1)
    fig.update_layout(
        height=600, xaxis_rangeslider_visible=False, margin={"t": 20}, legend={"orientation": "h"}
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- Peers ----------
with tab_peers:
    norm = a.normalise(closes)
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Normalised performance")
        st.plotly_chart(
            px.line(norm, labels={"value": "Rebased (1 = start)", "Ticker": ""}),
            use_container_width=True,
        )
    with right:
        st.subheader(f"{focus} vs peer average")
        if peers:
            rel = a.peer_relative(norm, focus).rename("Relative")
            st.plotly_chart(
                px.area(rel, labels={"value": "Focus / peer avg"}).update_layout(showlegend=False),
                use_container_width=True,
            )
        else:
            st.info("Pick at least one peer.")
    st.subheader("Return correlation")
    corr = a.returns(closes).corr()
    st.plotly_chart(
        px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1),
        use_container_width=True,
    )
    st.subheader("Summary")
    st.dataframe(
        s.style.format(
            {
                "Last": "{:,.2f}",
                "Total return": "{:+.1%}",
                "Ann. vol": "{:.1%}",
                "Sharpe (rf=0)": "{:.2f}",
                "Max drawdown": "{:.1%}",
            }
        ),
        use_container_width=True,
    )

# ---------- Risk ----------
with tab_risk:
    l2, r2 = st.columns(2)
    with l2:
        st.subheader(f"Rolling {window}d annualised vol")
        rv = a.rolling_vol(closes_all, window).loc[pd.Timestamp(start) :]
        st.plotly_chart(
            px.line(rv, labels={"value": "Vol", "Ticker": ""}), use_container_width=True
        )
    with r2:
        st.subheader("Drawdown from peak")
        st.plotly_chart(
            px.line(a.drawdown(closes), labels={"value": "Drawdown", "Ticker": ""}),
            use_container_width=True,
        )
    st.subheader("Daily return distribution")
    st.plotly_chart(
        px.histogram(
            a.returns(closes)[focus], nbins=80, labels={"value": f"{focus} daily return"}
        ).update_layout(showlegend=False),
        use_container_width=True,
    )

# ---------- Vol surface ----------
with tab_surface:
    st.caption("Synthetic implied-vol surface for VOD.L (illustrative; see lat.md/data.md).")
    grid = surface.pivot(index="Tenor", columns="Moneyness", values="ImpliedVol")
    fig3d = go.Figure(
        go.Surface(
            x=grid.columns,
            y=grid.index,
            z=grid.values,
            colorscale="Viridis",
            colorbar={"title": "IV"},
        )
    )
    fig3d.update_layout(
        height=600,
        margin={"t": 20},
        scene={
            "xaxis_title": "Moneyness K/S",
            "yaxis_title": "Tenor (y)",
            "zaxis_title": "Implied vol",
            "camera": {"eye": {"x": -1.6, "y": -1.6, "z": 0.9}},
        },
    )
    st.plotly_chart(fig3d, use_container_width=True)
    l3, r3 = st.columns(2)
    with l3:
        tenor = st.select_slider("Smile at tenor (y)", options=list(grid.index), value=0.5)
        st.plotly_chart(
            px.line(
                grid.loc[tenor], markers=True, labels={"value": "IV", "Moneyness": "K/S"}
            ).update_layout(showlegend=False),
            use_container_width=True,
        )
    with r3:
        st.markdown("**ATM term structure**")
        atm = grid[1.0] if 1.0 in grid.columns else grid.iloc[:, len(grid.columns) // 2]
        st.plotly_chart(
            px.line(atm, markers=True, labels={"value": "ATM IV", "Tenor": "Tenor"}).update_layout(
                showlegend=False
            ),
            use_container_width=True,
        )

# ---------- Data ----------
with tab_data:
    view = prices[prices["Ticker"].isin(selected) & (prices["Date"] >= pd.Timestamp(start))]
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button("Download CSV", view.to_csv(index=False), "prices_filtered.csv", "text/csv")
