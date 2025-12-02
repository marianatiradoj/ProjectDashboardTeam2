# interactive_dashboard/charts.py
"""
Charts module for the interactive crime dashboard.

This module defines reusable Altair-based visualizations that react to the
filtered dataframe provided by the filter layer.

All display texts are in Spanish for end users. Code comments remain in English.
"""

from __future__ import annotations

from typing import Dict, Any

import altair as alt
import pandas as pd
import streamlit as st

# Disable Altair's default row limit; we always pre-aggregate data.
alt.data_transformers.disable_max_rows()


# ---------------------------------------------------------------------
# Shared label mapping (same spirit as filters / KPIs)
# ---------------------------------------------------------------------
def _prettify_label(value: Any) -> str:
    """
    Convert raw categorical codes into human-friendly labels.

    Mirrors filters logic:
    - Replace underscores with spaces.
    - Use title case for display.
    """
    if value is None:
        return ""
    return str(value).replace("_", " ").title()


def _configure_chart(base: alt.Chart, height: int = 320) -> alt.Chart:
    """
    Apply common visual configuration to all charts.
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
    Serie temporal mensual de incidentes.

    Prioriza ANIO_HECHO + MES_HECHO (robusto a orígenes CSV / Snowflake).
    Solo si no existen esas columnas, cae a FECHA_HECHO.
    """
    title = "Evolución mensual de incidentes"

    # ---------------------------------------------------------
    # 1) Camino principal: usar anio_hecho + mes_hecho
    # ---------------------------------------------------------
    if {"anio_hecho", "mes_hecho"}.issubset(df.columns) and not df.empty:
        tmp = df[["anio_hecho", "mes_hecho"]].copy()

        # Año a numérico
        tmp["anio_hecho"] = pd.to_numeric(tmp["anio_hecho"], errors="coerce")

        # Normalizar mes en español (mayúsculas, sin espacios)
        tmp["mes_hecho_norm"] = tmp["mes_hecho"].astype(str).str.strip().str.upper()

        month_map = {
            "ENERO": 1,
            "FEBRERO": 2,
            "MARZO": 3,
            "ABRIL": 4,
            "MAYO": 5,
            "JUNIO": 6,
            "JULIO": 7,
            "AGOSTO": 8,
            "SEPTIEMBRE": 9,
            "OCTUBRE": 10,
            "NOVIEMBRE": 11,
            "DICIEMBRE": 12,
        }
        tmp["mes_num"] = tmp["mes_hecho_norm"].map(month_map)

        # Quitar registros sin año o sin mes válido
        tmp = tmp.dropna(subset=["anio_hecho", "mes_num"])
        if tmp.empty:
            return _empty_chart(title)

        # Construir timestamp → primer día del mes
        tmp["mes"] = pd.to_datetime(
            {
                "year": tmp["anio_hecho"].astype(int),
                "month": tmp["mes_num"].astype(int),
                "day": 1,
            },
            errors="coerce",
        )
        tmp = tmp.dropna(subset=["mes"])
        if tmp.empty:
            return _empty_chart(title)

        ts = tmp.groupby("mes").size().reset_index(name="incidentes").sort_values("mes")

    # ---------------------------------------------------------
    # 2) Fallback: solo si no tenemos anio_hecho + mes_hecho
    # ---------------------------------------------------------
    elif "fecha_hecho" in df.columns and not df.empty:
        fechas = pd.to_datetime(df["fecha_hecho"], errors="coerce").dropna()
        if fechas.empty:
            return _empty_chart(title)

        ts = (
            fechas.to_frame(name="fecha_hecho")
            .assign(mes=lambda x: x["fecha_hecho"].dt.to_period("M").dt.to_timestamp())
            .groupby("mes")
            .size()
            .reset_index(name="incidentes")
            .sort_values("mes")
        )
    else:
        return _empty_chart(title)

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
    Bar chart: incidents by main crime macro group.
    """
    title = "Incidentes por tipo principal de delito"

    if "delito_grupo_macro" not in df.columns or df.empty:
        return _empty_chart(title)

    counts = df["delito_grupo_macro"].dropna().astype(str).value_counts()

    if counts.empty:
        return _empty_chart(title)

    counts = counts.rename_axis("codigo_macro").reset_index(name="incidentes")
    counts["tipo_delito"] = counts["codigo_macro"].map(_prettify_label)

    # Limit to Top N if needed
    counts = counts.head(top_n)

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


def _chart_by_group_within_macro(
    df: pd.DataFrame,
    macro_value: Any,
    top_n: int = 15,
) -> alt.Chart:
    """
    Bar chart: incidents by 'delito_grupo' inside the selected macro group.

    Used when user has chosen a specific 'Tipo principal de delito'
    in the filters (not 'Totalidad').
    """
    if "delito_grupo" not in df.columns or df.empty:
        return _empty_chart("Distribución de subgrupos de delito")

    counts = df["delito_grupo"].dropna().astype(str).value_counts()
    if counts.empty:
        return _empty_chart("Distribución de subgrupos de delito")

    counts = counts.rename_axis("codigo_grupo").reset_index(name="incidentes")
    counts["grupo_delito"] = counts["codigo_grupo"].map(_prettify_label)

    # Top N subgroups for readability
    counts = counts.head(top_n)

    macro_label = _prettify_label(macro_value)
    title = f"Distribución de subgrupos dentro de {macro_label}"

    base = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("incidentes:Q", title="Número de incidentes"),
            y=alt.Y(
                "grupo_delito:N",
                title="Grupo del delito",
                sort="-x",
            ),
            tooltip=[
                alt.Tooltip("grupo_delito:N", title="Grupo del delito"),
                alt.Tooltip("incidentes:Q", title="Incidentes"),
            ],
        )
        .properties(title=title)
    )

    return _configure_chart(base, height=320)


def _chart_by_alcaldia(df: pd.DataFrame, top_n: int = 10) -> alt.Chart:
    """
    Bar chart: incidents by municipality (alcaldía).
    """
    title = "Incidentes por alcaldía"

    if "alcaldia_hecho" not in df.columns or df.empty:
        return _empty_chart(title)

    counts = df["alcaldia_hecho"].dropna().astype(str).value_counts()

    if counts.empty:
        return _empty_chart(title)

    counts = counts.rename_axis("codigo_alc").reset_index(name="incidentes")
    counts["alcaldia_label"] = counts["codigo_alc"].map(_prettify_label)

    counts = counts.head(top_n)

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
    Heatmap of incident counts by weekday and time-of-day segment.
    """
    title = "Distribución de incidentes por día y periodo del día"

    if "dia" not in df.columns or "periodo_hora" not in df.columns or df.empty:
        return _empty_chart(title)

    heat_df = df[["dia", "periodo_hora"]].dropna().copy()
    if heat_df.empty:
        return _empty_chart(title)

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
def render_main_charts(df: pd.DataFrame, seleccion: Dict[str, Any]) -> None:
    """
    Render the main set of charts for the interactive dashboard.

    Args:
        df: Filtered dataframe after applying all user selections.
        seleccion: Current filter selections. Uses 'delito_grupo_macro'
                   to switch the left chart when a macro crime type is chosen.
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

    # Read macro filter to switch chart behavior
    macro_selected = seleccion.get("delito_grupo_macro", "Totalidad")

    with col1:
        # If a specific macro is selected, show subgroups distribution
        if macro_selected and macro_selected != "Totalidad":
            chart_left = _chart_by_group_within_macro(df, macro_selected)
        else:
            chart_left = _chart_by_macro(df)
        st.altair_chart(chart_left, use_container_width=True)

    with col2:
        chart_alc = _chart_by_alcaldia(df)
        st.altair_chart(chart_alc, use_container_width=True)

    # 3) Heatmap for weekday vs time-of-day
    st.subheader("Patrones por día de la semana y periodo del día")
    heatmap = _chart_heatmap_weekday_hour(df)
    st.altair_chart(heatmap, use_container_width=True)
