# Dashboard/pagina2.py
import streamlit as st

from ui.theme_dark import inject_dark_theme
from ui.sidebar_menu import render_sidebar_menu

from components.charts_eda import (
    render_top5_crimes_bar,
    render_hourly_heatmap,
    render_weekly_timeseries,
    render_monthly_stacked_percent,
    load_crime_data,
)

st.set_page_config(page_title="Datos Históricos", layout="wide")
inject_dark_theme()

render_sidebar_menu(show_filters=False)

df = load_crime_data()

# ===== Filtros =====
with st.sidebar:
    st.subheader("Filtros EDA")

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

# ===== Layout =====
st.title("Datos Históricos")
st.caption("Exploración visual del comportamiento delictivo")
st.divider()

col1, col2 = st.columns(2)

# --- Izquierda ---
with col1:
    st.subheader("Distribución de grupo de delitos (Top 5)")
    render_top5_crimes_bar(
        df,
        hour_range=hora_rango,
        mes=mes,
        dia_semana=dia_semana,
        zona=zona,   # ✔ corregido
    )

    st.subheader("Heatmap horas vs día")
    render_hourly_heatmap(
        df,
        hour_range=hora_rango,
        mes=mes,
        dia_semana=dia_semana,
        zona=zona,
        tipos_crimen=tipos_crimen,
    )

# --- Derecha ---
with col2:
    st.subheader("Serie semanal por día")
    render_weekly_timeseries(
        df,
        hour_range=hora_rango,
        mes=mes,
        zona=zona,
        tipos_crimen=tipos_crimen,  # ✔ corregido
    )

    st.subheader("Composición mensual (%)")
    render_monthly_stacked_percent(
        df,
        hour_range=hora_rango,
        mes=mes,            # se ignora dentro de la función
        zona=zona,
        tipos_crimen=tipos_crimen,
    )

