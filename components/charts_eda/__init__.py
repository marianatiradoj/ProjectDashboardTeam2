# components/charts_eda/__init__.py
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

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

# CARGA DE DATOS
DATA_PATH = Path(r"C:\Users\maria\Documents\ProjectDashboardTeam2\Database\FGJ_CLEAN_Final.csv")


@st.cache_data(show_spinner=False)
def load_crime_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df = normalize_hour_column(df)
    return df


# EXPORTAR FUNCIONES DE GRÁFICA
from .top5_crimes import render_top5_crimes_bar          
from .hourly_heatmap import render_hourly_heatmap        
from .weekly_timeseries import render_weekly_timeseries  
from .monthly_stacked import render_monthly_stacked_percent  
