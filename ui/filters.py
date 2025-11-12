import streamlit as st

TIME_RANGES = ["Últimas 24h", "Última semana", "Último mes"]
CUADRANTES  = ["Norte", "Sur", "Este", "Oeste"]

KEY_RANGO = "flt_rango_tiempo"
KEY_CUADS = "flt_cuadrantes"

def _ensure_defaults():
    if KEY_RANGO not in st.session_state:
        st.session_state[KEY_RANGO] = TIME_RANGES[0]
    if KEY_CUADS not in st.session_state:
        st.session_state[KEY_CUADS] = []

def render_filters_block():
    """Dibuja SOLO los filtros (para usarlos dentro del sidebar del menú)."""
    _ensure_defaults()
    rango = st.selectbox(
        "Rango de Tiempo",
        TIME_RANGES,
        index=TIME_RANGES.index(st.session_state[KEY_RANGO]),
        key=KEY_RANGO,
    )
    cuadrantes = st.multiselect(
        "Cuadrante",
        CUADRANTES,
        default=st.session_state[KEY_CUADS],
        key=KEY_CUADS,
    )
    st.divider()
    return rango, cuadrantes

def get_filters():
    _ensure_defaults()
    return {
        "rango_tiempo": st.session_state[KEY_RANGO],
        "cuadrantes": st.session_state[KEY_CUADS],
    }
