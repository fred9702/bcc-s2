from __future__ import annotations

from collections.abc import Iterator

import pytest
import streamlit as st


@pytest.fixture(autouse=True)
def _clear_streamlit_cache() -> Iterator[None]:
    """st.cache_data is process-wide; isolate each AppTest from earlier runs."""
    st.cache_data.clear()
    yield
    st.cache_data.clear()
