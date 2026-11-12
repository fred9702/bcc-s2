"""Runtime configuration, entirely environment-variable driven (12-factor)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_REPO_DATA = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    prices_file: str
    surface_file: str
    app_env: str
    app_version: str
    default_ticker: str

    @property
    def prices_path(self) -> Path:
        return self.data_dir / self.prices_file

    @property
    def surface_path(self) -> Path:
        return self.data_dir / self.surface_file


def load_settings() -> Settings:
    return Settings(
        data_dir=Path(os.getenv("DATA_DIR", str(_REPO_DATA))),
        prices_file=os.getenv("PRICES_FILE", "prices.csv"),
        surface_file=os.getenv("SURFACE_FILE", "vol_surface.csv"),
        app_env=os.getenv("APP_ENV", "local"),
        app_version=os.getenv("APP_VERSION", "dev"),
        default_ticker=os.getenv("DEFAULT_TICKER", "VOD.L"),
    )
