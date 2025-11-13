# ui/filters.py
import streamlit as st

TIME_RANGES = ["Últimas 24h", "Última semana", "Último mes"]
CUADRANTES  = ["Norte", "Sur", "Este", "Oeste"]

def render_filters_block(key_prefix: str = ""):
    """
    Dibuja los filtros en el sidebar y devuelve (rango, cuadrantes).

    key_prefix permite que cada página tenga sus propios keys:
      - Página 1: key_prefix="p1_"
      - Página 2: key_prefix="p2_"
    """
    key_rango = f"{key_prefix}flt_rango_tiempo"
    key_cuads = f"{key_prefix}flt_cuadrantes"

    rango = st.selectbox(
        "Rango de Tiempo",
        TIME_RANGES,
        key=key_rango,
    )

    cuadrantes = st.multiselect(
        "Cuadrante",
        CUADRANTES,
        key=key_cuads,
    )

    st.divider()
    return rango, cuadrantes

def get_filters(key_prefix: str = ""):
    """Lee los filtros desde session_state con el mismo prefix que se usó al dibujarlos."""
    key_rango = f"{key_prefix}flt_rango_tiempo"
    key_cuads = f"{key_prefix}flt_cuadrantes"

    rango = st.session_state.get(key_rango, TIME_RANGES[0])
    cuadrantes = st.session_state.get(key_cuads, [])
    return {"rango_tiempo": rango, "cuadrantes": cuadrantes}
