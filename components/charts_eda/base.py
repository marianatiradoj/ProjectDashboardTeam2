# components/charts_eda/base.py
from __future__ import annotations

from typing import Iterable, Optional, Tuple, List

import pandas as pd

# ----------------- COLUMNAS CLAVE -----------------
HORA_COL = "hour_int"              # hora en entero 0–23
RAW_HOUR_COL = "hora_hecho"        # texto original

# Aliases para compatibilidad con código viejo
HOUR_COL = HORA_COL                # antes se usaba HOUR_COL

MONTH_COL = "mes_hecho"            # nombre del mes en español
WEEKDAY_COL = "dia"                # LUNES, MARTES, ...
ZONA_COL = "region_cdmx"           # Centro, Norte, Sur, ...
DELITO_COL = "delito_grupo"
DELITO_MACRO_COL = "delito_grupo_macro"

# Alias para código antiguo que importaba DIA_COL
DIA_COL = WEEKDAY_COL

# Orden "bonito" de meses y días
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

# ✅ Alias para compatibilidad con código viejo
DAY_ORDER = WEEKDAY_ORDER


# ----------------- PALETA (misma estética azul oscura) -----------------
PALETTE = {
    "bg_fig": "#020617",
    "bg_axes": "#020617",
    "grid": "#1E293B",
    "text": "#E5E7EB",

    # Barras
    "bar_light": "#60A5FA",
    "bar_main": "#2563EB",
    "bar_dark": "#1D4ED8",

    # Líneas (para la serie semanal)
    "line": "#60A5FA",       # color principal de la línea
    "line_alt": "#93C5FD",   # si luego quieres otra variante

    # (si tienes más claves, déjalas igual)
}


# ----------------- NORMALIZAR HORA -----------------
def normalize_hour_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Asegura que exista la columna HORA_COL (0–23) a partir de hora_hecho.
    No rompe nada si ya existe.
    """
    if HORA_COL in df.columns:
        df[HORA_COL] = pd.to_numeric(df[HORA_COL], errors="coerce").astype("Int64")
        return df

    if RAW_HOUR_COL in df.columns:
        parsed = pd.to_datetime(df[RAW_HOUR_COL], format="%H:%M:%S", errors="coerce")
        df[HORA_COL] = parsed.dt.hour.astype("Int64")

    return df


# ----------------- FILTROS COMUNES -----------------
def apply_common_filters(
    df: pd.DataFrame,
    hour_range: Optional[Tuple[int, int]] = None,
    mes: Optional[str] = None,
    dia_semana: Optional[str] = None,
    zona: Optional[str] = None,
    tipos_crimen: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """
    Aplica TODOS los filtros globales al DataFrame de forma consistente.
    Cualquier parámetro en None o "Todos"/"Todas" se IGNORA.
    """
    df_f = df.copy()

    # Normalizar hora
    df_f = normalize_hour_column(df_f)

    # --- Hora ---
    if (
        hour_range is not None
        and HORA_COL in df_f.columns
        and pd.notna(df_f[HORA_COL]).any()
    ):
        h0, h1 = hour_range
        df_f = df_f[(df_f[HORA_COL] >= h0) & (df_f[HORA_COL] <= h1)]

    # --- Mes ---
    if mes and mes != "Todos" and MONTH_COL in df_f.columns:
        df_f = df_f[df_f[MONTH_COL] == mes]

    # --- Día de la semana ---
    if dia_semana and dia_semana != "Todos" and WEEKDAY_COL in df_f.columns:
        df_f = df_f[df_f[WEEKDAY_COL] == dia_semana]

    # --- Zona / región CDMX ---
    if zona and zona != "Todas" and ZONA_COL in df_f.columns:
        df_f = df_f[df_f[ZONA_COL] == zona]

    # --- Tipo de crimen (macro) ---
    if tipos_crimen:
        tipos_crimen = list(tipos_crimen)
        if DELITO_MACRO_COL in df_f.columns:
            df_f = df_f[df_f[DELITO_MACRO_COL].isin(tipos_crimen)]
        elif DELITO_COL in df_f.columns:
            df_f = df_f[df_f[DELITO_COL].isin(tipos_crimen)]

    return df_f
