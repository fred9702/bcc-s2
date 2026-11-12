# App

Streamlit dashboard in [[src/bcc_s2/app.py]] that loads CSVs once at startup (cached) and renders five tabs for a focus ticker and its peers.

## Configuration

All runtime config comes from environment variables via [[src/bcc_s2/config.py#load_settings]] (12-factor), so the same image runs in every environment.

`DATA_DIR`, `PRICES_FILE`, `SURFACE_FILE` locate the CSVs (in Kubernetes, `DATA_DIR` points at the ConfigMap mount). `APP_ENV`, `APP_VERSION` are shown in the sidebar; `DEFAULT_TICKER` picks the initial focus.

## Data loading

[[src/bcc_s2/data.py#load_prices]] and [[src/bcc_s2/data.py#load_surface]] validate required columns and fail fast with [[src/bcc_s2/data.py#DataError]], so a bad ConfigMap crashes the pod instead of serving wrong data.

## Analytics

Pure pandas functions in [[src/bcc_s2/analytics.py]], with no Streamlit imports so they are unit-testable.

Includes rebasing ([[src/bcc_s2/analytics.py#normalise]]), annualised rolling vol, drawdown, focus-vs-peer-average ([[src/bcc_s2/analytics.py#peer_relative]]) and a summary table ([[src/bcc_s2/analytics.py#summary]]).

## Views

Five tabs: Price, Peers, Risk, Vol surface and Data.

- **Price**: candlestick + volume with optional SMA 20/50.
- **Peers**: normalised performance, focus vs peer average, return correlation heatmap, summary stats.
- **Risk**: rolling annualised vol, drawdown, daily return histogram.
- **Vol surface**: 3D implied-vol surface, smile at a chosen tenor, ATM term structure.
- **Data**: filtered table with CSV download.
