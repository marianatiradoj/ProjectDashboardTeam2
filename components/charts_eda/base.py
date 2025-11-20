# components/charts_eda/base.py
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------- Rutas ----------
DATA_PATH = Path("Database/FGJ_CLEAN_Final.csv")

# ---------- Columnas ----------
HOUR_COL = "hour_int"               # columna de hora en entero 0–23
HOUR_RAW_COL = "hora_hecho"
MES_COL = "mes_hecho"
DIA_COL = "dia"
ZONA_COL = "region_cdmx"
DELITO_MACRO_COL = "delito_grupo_macro"
MONTH_COL = "mes_hecho"

# Orden lógico (si después quieres usarlo)
DAY_ORDER = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
MONTH_ORDER = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
]

# ---------- Paleta (azules corporativos) ----------
PALETTE = {
    "bar_main": "#3B82F6",      # azul principal
    "bar_light": "#60A5FA",
    "bar_dark": "#1D4ED8",
    "line": "#38BDF8",
    "bg_fig": "#020617",
    "bg_axes": "#020617",
    "grid": "#1f2937",
    "text": "#E5E7EB",
}


# ---------- Carga de datos ----------
@st.cache_data(show_spinner="Cargando base de delitos…")
def load_crime_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    # Asegurar columna de hora numérica 0–23
    if HOUR_COL not in df.columns:
        if HOUR_RAW_COL in df.columns:
            df[HOUR_COL] = (
                pd.to_datetime(df[HOUR_RAW_COL].astype(str), errors="coerce")
                .dt.hour
            )
        elif "periodo_hora" in df.columns:
            df[HOUR_COL] = (
                pd.to_datetime(df["periodo_hora"].astype(str), errors="coerce")
                .dt.hour
            )

    if HOUR_COL in df.columns:
        df[HOUR_COL] = df[HOUR_COL].fillna(0).astype(int)

    return df


# ---------- Filtro común para TODAS las gráficas ----------
def apply_common_filters(
    df: pd.DataFrame,
    hour_range=None,
    mes: str = "Todos",
    dia_semana: str = "Todos",
    zona: str = "Todas",
    tipos_crimen=None,
) -> pd.DataFrame:
    df_f = df.copy()

    # Hora
    if hour_range is not None and HOUR_COL in df_f.columns:
        h0, h1 = hour_range
        df_f = df_f[(df_f[HOUR_COL] >= h0) & (df_f[HOUR_COL] <= h1)]

    # Mes
    if mes != "Todos" and MES_COL in df_f.columns:
        df_f = df_f[df_f[MES_COL] == mes]

    # Día de semana
    if dia_semana != "Todos" and DIA_COL in df_f.columns:
        df_f = df_f[df_f[DIA_COL] == dia_semana]

    # Zona (region_cdmx)
    if zona != "Todas" and ZONA_COL in df_f.columns:
        df_f = df_f[df_f[ZONA_COL] == zona]

    # Tipo de crimen (grupo macro)
    if tipos_crimen:
        if DELITO_MACRO_COL in df_f.columns:
            df_f = df_f[df_f[DELITO_MACRO_COL].isin(tipos_crimen)]

    return df_f
