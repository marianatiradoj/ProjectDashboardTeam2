# components/charts_eda/__init__.py

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from pathlib import Path

# 🔹 Paleta y columnas compartidas
PALETTE = {
    "bg": "#020617",
    "panel": "#020617",
    "blue_light": "#60A5FA",
    "blue_mid": "#2563EB",
    "blue_dark": "#1D4ED8",
    "muted": "#9CA3AF",
    "text": "#E5E7EB",
}

DATA_PATH = Path("Database") / "FGJ_CLEAN_Final.csv"

HOUR_COL = "hour_int"
MONTH_COL = "mes_hecho"
DAY_COL = "dia"
ZONE_COL = "region_cdmx"
GROUP_COL = "delito_grupo_macro"


@st.cache_data(show_spinner=False)
def load_crime_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    # Crear columna hour_int una única vez si no existe
    if HOUR_COL not in df.columns and "hora_hecho" in df.columns:
        df[HOUR_COL] = (
            pd.to_datetime(df["hora_hecho"], format="%H:%M:%S", errors="coerce")
            .dt.hour
            .fillna(0)
            .astype(int)
        )
    return df


def apply_common_filters(
    df: pd.DataFrame,
    hour_range,
    mes: str,
    dia_semana: str,
    zona: str,
    tipos_crimen=None,
) -> pd.DataFrame:
    df_f = df.copy()

    if hour_range is not None and HOUR_COL in df_f.columns:
        h0, h1 = hour_range
        df_f = df_f[(df_f[HOUR_COL] >= h0) & (df_f[HOUR_COL] <= h1)]

    if mes != "Todos" and MONTH_COL in df_f.columns:
        df_f = df_f[df_f[MONTH_COL] == mes]

    if dia_semana != "Todos" and DAY_COL in df_f.columns:
        df_f = df_f[df_f[DAY_COL] == dia_semana]

    if zona != "Todas" and ZONE_COL in df_f.columns:
        df_f = df_f[df_f[ZONE_COL] == zona]

    if tipos_crimen:
        df_f = df_f[df_f[GROUP_COL].isin(tipos_crimen)]

    return df_f


# Helpers para otros módulos (si los usas)
def _safe_subset_after_filters(df_f: pd.DataFrame, msg: str) -> bool:
    if df_f.empty:
        st.info(msg)
        return False
    return True


# 👉 Importamos las funciones de cada archivo de gráfica
from .top5_crimes import render_top5_crimes_bar
from .hourly_heatmap import render_hourly_heatmap
from .weekly_timeseries import render_weekly_timeseries
from .monthly_stacked import render_monthly_stacked_percent
