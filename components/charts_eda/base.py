# components/charts_eda/base.py
from __future__ import annotations

from typing import Iterable, Optional, Tuple, List

import pandas as pd

# Core columns
HORA_COL = "hour_int"  # hour as integer 0–23
RAW_HOUR_COL = "hora_hecho"

# Aliases for backward compatibility
HOUR_COL = HORA_COL

MONTH_COL = "mes_hecho"
WEEKDAY_COL = "dia"
ZONA_COL = "region_cdmx"
DELITO_COL = "delito_grupo"
DELITO_MACRO_COL = "delito_grupo_macro"

DIA_COL = WEEKDAY_COL

# Month and weekday order for plotting
MONTH_ORDER: List[str] = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]

WEEKDAY_ORDER: List[str] = [
    "LUNES",
    "MARTES",
    "MIERCOLES",
    "JUEVES",
    "VIERNES",
    "SABADO",
    "DOMINGO",
]

# Alias for backward compatibility
DAY_ORDER = WEEKDAY_ORDER

# Color palette for charts
PALETTE = {
    "bg_fig": "#020617",
    "bg_axes": "#020617",
    "grid": "#1E293B",
    "text": "#E5E7EB",
    # Bars
    "bar_light": "#60A5FA",
    "bar_main": "#2563EB",
    "bar_dark": "#1D4ED8",
    # Lines (weekly series)
    "line": "#60A5FA",
    "line_alt": "#93C5FD",
}


def normalize_hour_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure HORA_COL (0–23) exists, derived from RAW_HOUR_COL if needed.
    Does nothing if the column already exists.
    """
    if HORA_COL in df.columns:
        df[HORA_COL] = pd.to_numeric(df[HORA_COL], errors="coerce").astype("Int64")
        return df

    if RAW_HOUR_COL in df.columns:
        parsed = pd.to_datetime(df[RAW_HOUR_COL], format="%H:%M:%S", errors="coerce")
        df[HORA_COL] = parsed.dt.hour.astype("Int64")

    return df


def apply_common_filters(
    df: pd.DataFrame,
    hour_range: Optional[Tuple[int, int]] = None,
    mes: Optional[str] = None,
    dia_semana: Optional[str] = None,
    zona: Optional[str] = None,
    tipos_crimen: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """
    Apply all global filters in a consistent way.
    Any parameter set to None or 'Todos'/'Todas' is ignored.
    """
    df_f = df.copy()

    # Normalize hour column
    df_f = normalize_hour_column(df_f)

    # Hour filter
    if (
        hour_range is not None
        and HORA_COL in df_f.columns
        and pd.notna(df_f[HORA_COL]).any()
    ):
        h0, h1 = hour_range
        df_f = df_f[(df_f[HORA_COL] >= h0) & (df_f[HORA_COL] <= h1)]

    # Month filter
    if mes and mes != "Todos" and MONTH_COL in df_f.columns:
        df_f = df_f[df_f[MONTH_COL] == mes]

    # Weekday filter
    if dia_semana and dia_semana != "Todos" and WEEKDAY_COL in df_f.columns:
        df_f = df_f[df_f[WEEKDAY_COL] == dia_semana]

    # Zone / region filter
    if zona and zona != "Todas" and ZONA_COL in df_f.columns:
        df_f = df_f[df_f[ZONA_COL] == zona]

    # Crime type filter (macro or specific)
    if tipos_crimen:
        tipos_crimen = list(tipos_crimen)
        if DELITO_MACRO_COL in df_f.columns:
            df_f = df_f[df_f[DELITO_MACRO_COL].isin(tipos_crimen)]
        elif DELITO_COL in df_f.columns:
            df_f = df_f[df_f[DELITO_COL].isin(tipos_crimen)]

    return df_f
