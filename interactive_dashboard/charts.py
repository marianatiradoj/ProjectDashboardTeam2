# interactive_dashboard/charts.py
"""
Charts module for the interactive crime dashboard.

This module defines reusable Altair-based visualizations that react to the
filtered dataframe provided by the filter layer.

All display texts are in Spanish for end users. Code comments remain in English.
"""

from __future__ import annotations

from typing import Dict

import altair as alt
import pandas as pd
import streamlit as st

# Disable Altair's default row limit; we always pre-aggregate data.
alt.data_transformers.disable_max_rows()


# ---------------------------------------------------------------------
# Shared label mapping (same spirit as filters / KPIs)
# ---------------------------------------------------------------------
def _prettify_label(value: str) -> str:
    """
    Convert raw categorical codes into human-friendly labels.

    This mirrors the mapping logic used by filters:
    - Replace underscores with spaces.
    - Use title case for display.
    """
    if value is None:
        return ""
    return str(value).replace("_", " ").title()


def _configure_chart(base: alt.Chart, height: int = 320) -> alt.Chart:
    """
    Apply common visual configuration to all charts.

    Args:
        base (alt.Chart): Altair chart instance.
        height (int): Base height for the visualization.

    Returns:
        alt.Chart: Configured chart.
    """
    return (
        base.properties(height=height)
        .configure_axis(
            labelColor="#e5e7eb",
            titleColor="#e5e7eb",
            gridOpacity=0.15,
        )
        .configure_view(strokeOpacity=0)  # remove outer border
        .configure_legend(
            labelColor="#e5e7eb",
            titleColor="#e5e7eb",
        )
    )


def _empty_chart(title: str) -> alt.Chart:
    """
    Return an empty chart used as fallback when data is not available.
    """
    return (
        alt.Chart(pd.DataFrame({"x": [], "y": []})).mark_point().properties(title=title)
    )


# ---------------------------------------------------------------------
# Individual charts (all pre-aggregated in pandas)
# ---------------------------------------------------------------------
def _chart_monthly_timeseries(df: pd.DataFrame) -> alt.Chart:
    """
    Monthly incident time series using 'fecha_hecho'.

    The function aggregates records by month in pandas to avoid
    sending millions of rows to the browser.
    """
    title = "Evolución mensual de incidentes"

    if "fecha_hecho" not in df.columns or df.empty:
        return _empty_chart(title)

    fechas = pd.to_datetime(df["fecha_hecho"], errors="coerce").dropna()
    if fechas.empty:
        return _empty_chart(title)

    # Aggregate by month (start of month)
    ts = (
        fechas.to_frame(name="fecha_hecho")
        .assign(mes=lambda x: x["fecha_hecho"].dt.to_period("M").dt.to_timestamp())
        .groupby("mes")
        .size()
        .reset_index(name="incidentes")
    )

    base = (
        alt.Chart(ts)
        .mark_line(point=True)
        .encode(
            x=alt.X("mes:T", title="Mes del hecho"),
            y=alt.Y("incidentes:Q", title="Número de incidentes"),
            tooltip=[
                alt.Tooltip("mes:T", title="Mes"),
                alt.Tooltip("incidentes:Q", title="Incidentes"),
            ],
        )
        .interactive()
        .properties(title=title)
    )

    return _configure_chart(base, height=260)


def _chart_by_macro(df: pd.DataFrame, top_n: int = 10) -> alt.Chart:
    """
    Horizontal bar chart showing incidents by main crime type.

    Args:
        df (pd.DataFrame): Filtered dataset.
        top_n (int): Maximum number of categories to display.
    """
    title = "Incidentes por tipo principal de delito"

    if "delito_grupo_macro" not in df.columns or df.empty:
        return _empty_chart(title)

    # Robust value_counts → reset_index pattern
    counts = df["delito_grupo_macro"].dropna().astype(str).value_counts()

    if counts.empty:
        return _empty_chart(title)

    counts = counts.rename_axis("codigo_macro").reset_index(name="incidentes")

    # Apply prettify mapping for display labels
    counts["tipo_delito"] = counts["codigo_macro"].map(_prettify_label)

    base = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("incidentes:Q", title="Número de incidentes"),
            y=alt.Y(
                "tipo_delito:N",
                title="Tipo principal de delito",
                sort="-x",
            ),
            tooltip=[
                alt.Tooltip("tipo_delito:N", title="Tipo de delito"),
                alt.Tooltip("incidentes:Q", title="Incidentes"),
            ],
        )
        .properties(title=title)
    )

    return _configure_chart(base, height=320)


def _chart_by_alcaldia(df: pd.DataFrame, top_n: int = 10) -> alt.Chart:
    """
    Horizontal bar chart showing incidents by municipality of the event.

    Args:
        df (pd.DataFrame): Filtered dataset.
        top_n (int): Maximum number of categories to display.
    """
    title = "Incidentes por alcaldía"

    if "alcaldia_hecho" not in df.columns or df.empty:
        return _empty_chart(title)

    counts = df["alcaldia_hecho"].dropna().astype(str).value_counts()

    if counts.empty:
        return _empty_chart(title)

    counts = counts.rename_axis("codigo_alc").reset_index(name="incidentes")

    counts["alcaldia_label"] = counts["codigo_alc"].map(_prettify_label)

    base = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("incidentes:Q", title="Número de incidentes"),
            y=alt.Y(
                "alcaldia_label:N",
                title="Alcaldía",
                sort="-x",
            ),
            tooltip=[
                alt.Tooltip("alcaldia_label:N", title="Alcaldía"),
                alt.Tooltip("incidentes:Q", title="Incidentes"),
            ],
        )
        .properties(title=title)
    )

    return _configure_chart(base, height=320)


def _chart_heatmap_weekday_hour(df: pd.DataFrame) -> alt.Chart:
    """
    Heatmap of incident counts by weekday and hour period.

    Assumes:
        - 'dia' contains weekday names (already mapped in filters/KPIs).
        - 'periodo_hora' contains discrete time-of-day segments.

    The function returns an empty chart if those columns are not available.
    """
    title = "Distribución de incidentes por día y periodo del día"

    if "dia" not in df.columns or "periodo_hora" not in df.columns or df.empty:
        return _empty_chart(title)

    heat_df = df[["dia", "periodo_hora"]].dropna().copy()

    if heat_df.empty:
        return _empty_chart(title)

    # Apply prettify mapping for labels used in the heatmap
    heat_df["dia_label"] = heat_df["dia"].astype(str)
    heat_df["periodo_label"] = heat_df["periodo_hora"].astype(str)

    heat_df = (
        heat_df.groupby(["dia_label", "periodo_label"])
        .size()
        .reset_index(name="incidentes")
    )

    if heat_df.empty:
        return _empty_chart(title)

    # Explicit weekday order to keep logical sequence
    weekday_order = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Miercoles",  # fallback
        "Jueves",
        "Viernes",
        "Sábado",
        "Sabado",  # fallback
        "Domingo",
    ]

    base = (
        alt.Chart(heat_df)
        .mark_rect()
        .encode(
            x=alt.X(
                "periodo_label:N",
                title="Periodo del día",
                sort="ascending",
            ),
            y=alt.Y(
                "dia_label:N",
                title="Día de la semana",
                sort=weekday_order,
            ),
            color=alt.Color(
                "incidentes:Q",
                title="Número de incidentes",
                scale=alt.Scale(scheme="inferno"),
            ),
            tooltip=[
                alt.Tooltip("dia_label:N", title="Día"),
                alt.Tooltip("periodo_label:N", title="Periodo"),
                alt.Tooltip("incidentes:Q", title="Incidentes"),
            ],
        )
        .properties(title=title)
    )

    return _configure_chart(base, height=320)


# ---------------------------------------------------------------------
# Public entrypoint used in pagina5.py
# ---------------------------------------------------------------------
def render_main_charts(df: pd.DataFrame, seleccion: Dict) -> None:
    """
    Render the main set of charts for the interactive dashboard.

    Args:
        df (pd.DataFrame): Filtered dataframe after applying all user selections.
        seleccion (Dict): Dictionary describing current filter selections.
                          Currently not used inside the charts, but kept
                          for future contextual annotations.
    """
    if df is None or df.empty:
        st.info(
            "No hay datos disponibles para generar gráficas con los filtros actuales."
        )
        return

    # 1) Monthly time series – full width
    st.subheader("Tendencias temporales")
    ts_chart = _chart_monthly_timeseries(df)
    st.altair_chart(ts_chart, use_container_width=True)

    # 2) Two-column layout for categorical distributions
    st.subheader("Distribución por tipo de delito y alcaldía")
    col1, col2 = st.columns(2)

    with col1:
        chart_macro = _chart_by_macro(df)
        st.altair_chart(chart_macro, use_container_width=True)

    with col2:
        chart_alc = _chart_by_alcaldia(df)
        st.altair_chart(chart_alc, use_container_width=True)

    # 3) Heatmap for weekday vs time-of-day
    st.subheader("Patrones por día de la semana y periodo del día")
    heatmap = _chart_heatmap_weekday_hour(df)
    st.altair_chart(heatmap, use_container_width=True)
