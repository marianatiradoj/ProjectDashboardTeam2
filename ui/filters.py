# ui/filters.py
import streamlit as st

# Time and area options for sidebar filters
TIME_RANGES = ["Últimas 24h", "Última semana", "Último mes"]
CUADRANTES = ["Norte", "Sur", "Este", "Oeste"]


def render_filters_block(key_prefix: str = ""):
    """Render time and quadrant filters in the sidebar and return selected values."""
    key_rango = f"{key_prefix}flt_rango_tiempo"
    key_cuads = f"{key_prefix}flt_cuadrantes"

    rango = st.selectbox(
        "Rango de tiempo",
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
    """Read filter values from session_state using the same key prefix."""
    key_rango = f"{key_prefix}flt_rango_tiempo"
    key_cuads = f"{key_prefix}flt_cuadrantes"

    rango = st.session_state.get(key_rango, TIME_RANGES[0])
    cuadrantes = st.session_state.get(key_cuads, [])
    return {"rango_tiempo": rango, "cuadrantes": cuadrantes}
