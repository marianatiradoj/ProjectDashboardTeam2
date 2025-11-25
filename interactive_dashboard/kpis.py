# interactive_dashboard/kpis.py

from __future__ import annotations

from typing import Dict, Any, Optional

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------
# Label formatting helpers
# ---------------------------------------------------------------------
def _prettify(t: Any) -> str:
    """
    Format categorical labels for display purposes.

    Underscores are replaced by spaces and the text is converted
    to title case. The original values in the dataframe remain
    unchanged; this function is only used for UI rendering.
    """
    if t is None:
        return ""
    return str(t).replace("_", " ").title()


# ---------------------------------------------------------------------
# KPI computation helpers
# ---------------------------------------------------------------------
def _safe_count(df: pd.DataFrame) -> int:
    """
    Return the total number of rows as an integer.
    This KPI is used as a proxy for total incidents.
    """
    if df is None or df.empty:
        return 0
    return int(len(df))


def _compute_date_range(df: pd.DataFrame) -> Optional[str]:
    """
    Build a human-readable date range based on 'fecha_hecho'.
    If the column is missing or empty, return None.
    """
    if "fecha_hecho" not in df.columns or df.empty:
        return None

    fechas = df["fecha_hecho"].dropna()
    if fechas.empty:
        return None

    start = fechas.min().date()
    end = fechas.max().date()

    if start == end:
        return start.strftime("%d/%m/%Y")
    return f"{start.strftime('%d/%m/%Y')} – {end.strftime('%d/%m/%Y')}"


def _compute_daily_average(df: pd.DataFrame) -> Optional[float]:
    """
    Compute the average number of incidents per day using 'fecha_hecho'.
    If the column is missing or empty, return None.
    """
    if "fecha_hecho" not in df.columns or df.empty:
        return None

    fechas = df["fecha_hecho"].dropna()
    if fechas.empty:
        return None

    counts_per_day = fechas.dt.date.value_counts().sort_index()
    if counts_per_day.empty:
        return None

    return float(counts_per_day.mean())


def _top_category(df: pd.DataFrame, column: str) -> Optional[str]:
    """
    Return the most frequent category in a given column.
    If the column is missing or has no valid values, return None.
    """
    if column not in df.columns or df.empty:
        return None

    vc = df[column].dropna().value_counts()
    if vc.empty:
        return None

    return str(vc.index[0])


def _n_unique(df: pd.DataFrame, column: str) -> Optional[int]:
    """
    Return the number of unique non-null values in a given column.
    If the column is missing or empty, return None.
    """
    if column not in df.columns or df.empty:
        return None
    n = df[column].dropna().nunique()
    return int(n) if n > 0 else None


# ---------------------------------------------------------------------
# Public KPI API
# ---------------------------------------------------------------------
def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute core KPIs for the crime dashboard using the filtered dataframe.
    """
    kpis: Dict[str, Any] = {}

    kpis["total_incidents"] = _safe_count(df)
    kpis["date_range"] = _compute_date_range(df)
    kpis["daily_avg"] = _compute_daily_average(df)
    kpis["n_colonias"] = _n_unique(df, "colonia_hecho")
    kpis["peak_weekday"] = _top_category(df, "dia")
    kpis["top_macro"] = _top_category(df, "delito_grupo_macro")
    kpis["top_group"] = _top_category(df, "delito_grupo")
    kpis["top_alcaldia"] = _top_category(df, "alcaldia_hecho")

    return kpis


def render_kpi_cards(kpis: Dict[str, Any]) -> None:
    """
    Render KPI cards in two logical rows:
        - Row 1: volume and coverage indicators.
        - Row 2: profile of crime concentration.
    Visual styles are defined in ui/kpi_styles.css.
    """

    total_incidents = kpis.get("total_incidents", 0)
    date_range = kpis.get("date_range", None)
    daily_avg = kpis.get("daily_avg", None)
    n_colonias = kpis.get("n_colonias", None)
    peak_weekday = kpis.get("peak_weekday", None)
    top_macro = kpis.get("top_macro", None)
    top_group = kpis.get("top_group", None)
    top_alcaldia = kpis.get("top_alcaldia", None)

    # Caption with temporal coverage
    if date_range is not None:
        st.caption(f"Periodo analizado: {date_range}")
    else:
        st.caption("Periodo analizado: sin información disponible.")

    # Format values for display
    total_str = f"{total_incidents:,}".replace(",", " ")
    daily_str = (
        f"{daily_avg:,.1f}".replace(",", " ")
        if daily_avg is not None
        else "No disponible"
    )
    colonias_str = (
        f"{n_colonias:,}".replace(",", " ")
        if n_colonias is not None
        else "No disponible"
    )
    weekday_str = _prettify(peak_weekday) if peak_weekday else "No disponible"

    macro_str = _prettify(top_macro) if top_macro else "No disponible"
    group_str = _prettify(top_group) if top_group else "No disponible"
    alcaldia_str = _prettify(top_alcaldia) if top_alcaldia else "No disponible"

    # Row 1: volume and basic coverage
    row1_html = f"""
    <div class="kpi-grid-row1">
        <div class="kpi-card">
            <div class="kpi-label">Total de incidentes en el periodo</div>
            <div class="kpi-value">{total_str}</div>
            <div class="kpi-subtext">Registros después de aplicar filtros.</div>
        </div>
        <div class="kpi-card alt-1">
            <div class="kpi-label">Promedio diario de incidentes</div>
            <div class="kpi-value">{daily_str}</div>
            <div class="kpi-subtext">Promedio calculado con base en la fecha del hecho.</div>
        </div>
        <div class="kpi-card alt-2">
            <div class="kpi-label">Colonias afectadas</div>
            <div class="kpi-value">{colonias_str}</div>
            <div class="kpi-subtext">Colonias con al menos un incidente registrado.</div>
        </div>
        <div class="kpi-card alt-3">
            <div class="kpi-label">Día con más incidentes</div>
            <div class="kpi-value">{weekday_str}</div>
            <div class="kpi-subtext">Día de la semana con mayor concentración de casos.</div>
        </div>
    </div>
    """

    # Row 2: crime concentration profile
    row2_html = f"""
    <div class="kpi-grid-row2">
        <div class="kpi-card">
            <div class="kpi-label">Tipo principal de delito más frecuente</div>
            <div class="kpi-value">{macro_str}</div>
            <div class="kpi-subtext">Categoría principal con mayor número de registros.</div>
        </div>
        <div class="kpi-card alt-1">
            <div class="kpi-label">Grupo de delito más frecuente</div>
            <div class="kpi-value">{group_str}</div>
            <div class="kpi-subtext">Grupo específico con mayor incidencia en el periodo.</div>
        </div>
        <div class="kpi-card alt-2">
            <div class="kpi-label">Alcaldía con más incidentes</div>
            <div class="kpi-value">{alcaldia_str}</div>
            <div class="kpi-subtext">Alcaldía con el mayor número de registros.</div>
        </div>
    </div>
    """

    # Render both rows
    st.markdown(row1_html + row2_html, unsafe_allow_html=True)
