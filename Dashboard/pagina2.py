# Dashboard/pagina2.py
import streamlit as st
from ui.theme_dark import apply_theme
from core.data_loader import load_central_dataset

from components.charts_eda import (
    render_top5_crimes_bar,
    render_hourly_heatmap,
    render_weekly_timeseries,
    render_monthly_stacked_percent,
)


# --- Initial configuration and global theme ---
st.set_page_config(
    page_title="Dashboard Histórico – Tendencias",
    layout="wide",
)
apply_theme()

st.title("Dashboard Histórico – Tendencias")
st.caption("Exploración visual del comportamiento delictivo en el tiempo.")
st.divider()


# --- Load central historical dataset ---
df = load_central_dataset()


# --- Sidebar filters for this dashboard ---
with st.sidebar:
    st.subheader("Filtros del Dashboard")

    zonas = ["Todas"] + sorted(df["region_cdmx"].dropna().unique().tolist())
    zona = st.selectbox("Zona", zonas, key="p2_zona")

    hora_rango = st.slider(
        "Hora del día",
        min_value=0,
        max_value=23,
        value=(0, 23),
        step=1,
        key="p2_hora_rango",
    )

    meses = ["Todos"] + sorted(df["mes_hecho"].dropna().unique().tolist())
    mes = st.selectbox("Mes", meses, key="p2_mes")

    dias = ["Todos"] + sorted(df["dia"].dropna().unique().tolist())
    dia_semana = st.selectbox("Día de la semana", dias, key="p2_dia_semana")

    delitos_unicos = sorted(df["delito_grupo_macro"].dropna().unique().tolist())
    tipos_crimen = st.multiselect(
        "Tipo de crimen",
        delitos_unicos,
        key="p2_tipos_crimen",
    )


# --- Main layout: two-column structure ---
col1, col2 = st.columns(2)


# --- Left column: distribution and heatmap ---
with col1:
    st.subheader("Distribución por grupo de delitos (Top 5)")
    render_top5_crimes_bar(
        df,
        hour_range=hora_rango,
        mes=mes,
        dia_semana=dia_semana,
        zona=zona,
    )

    st.subheader("Mapa de calor: hora vs día")
    render_hourly_heatmap(
        df,
        hour_range=hora_rango,
        mes=mes,
        dia_semana=dia_semana,
        zona=zona,
        tipos_crimen=tipos_crimen,
    )


# --- Right column: time series and monthly composition ---
with col2:
    st.subheader("Serie semanal por día")
    render_weekly_timeseries(
        df,
        hour_range=hora_rango,
        mes=mes,
        zona=zona,
        tipos_crimen=tipos_crimen,
    )

    st.subheader("Composición mensual (%)")
    render_monthly_stacked_percent(
        df,
        hora_rango,
        mes=mes,
        zona=zona,
        tipos_crimen=tipos_crimen,
    )
