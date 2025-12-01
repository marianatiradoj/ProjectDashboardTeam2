# components/charts_eda/__init__.py
from __future__ import annotations

import pandas as pd
import streamlit as st

from config import DATA_PATH  # unified dataset path

from .base import (
    HORA_COL,
    RAW_HOUR_COL,
    MONTH_COL,
    WEEKDAY_COL,
    ZONA_COL,
    DELITO_COL,
    DELITO_MACRO_COL,
    MONTH_ORDER,
    WEEKDAY_ORDER,
    PALETTE,
    normalize_hour_column,
    apply_common_filters,
)


# Cached loader for charts that need direct data access
@st.cache_data(show_spinner=False)
def load_crime_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df = normalize_hour_column(df)
    return df


# Export chart render functions
from .top5_crimes import render_top5_crimes_bar
from .hourly_heatmap import render_hourly_heatmap
from .weekly_timeseries import render_weekly_timeseries
from .monthly_stacked import render_monthly_stacked_percent
