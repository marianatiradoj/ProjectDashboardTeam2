import streamlit as st
from ui.theme_dark import apply_theme


# --- Initial page configuration and global theme ---
st.set_page_config(
    page_title="Modelo Predictivo – Forecasting Operativo",
    layout="wide",
)
apply_theme()

st.title("Modelo Predictivo – Forecasting Operativo")
st.caption("Proyección de indicadores clave para apoyar la toma de decisiones.")


# --- Top navigation button (chat assistant) ---
if st.button(
    "Haz una pregunta al consultor",
    key="ask",
    type="primary",
    use_container_width=True,
):
    st.switch_page("Dashboard/pagina3.py")

st.divider()


# --- KPI utilities ---
def fmt_number(value):
    """Format numerical values with consistent style."""
    if isinstance(value, float):
        return f"{value:.2f}" if 0 <= value <= 1 else f"{value:,.2f}".replace(",", " ")
    if isinstance(value, (int, float)):
        return f"{value:,.0f}".replace(",", " ")
    return str(value)


def previous_range_label(rango: str) -> str:
    """Resolve human-readable comparison labels."""
    return {
        "Últimas 24h": "24h previas",
        "Última semana": "Semana previa",
        "Último mes": "Mes previo",
    }.get(rango, "Periodo previo")


def kpi_metric(col, label, current, previous, *, inverse=False, suffix: str = ""):
    """Render a KPI metric with percentage delta and direction."""
    delta_txt = "—"

    if previous is not None:
        try:
            change = current - previous
            if previous != 0:
                pct = (change / previous) * 100
                arrow = "↑" if pct >= 0 else "↓"
                rango = st.session_state.get("flt_rango_tiempo", "")
                ref_label = previous_range_label(rango)
                delta_txt = f"{arrow}{abs(pct):.1f}% vs {ref_label}"
        except Exception:
            delta_txt = "—"

    delta_color = "inverse" if inverse else "normal"
    value_str = fmt_number(current) + (suffix or "")

    with col:
        st.metric(
            label=label,
            value=value_str,
            delta=delta_txt,
            delta_color=delta_color,
        )


# --- Example KPI data (replace with model outputs if needed) ---
kpi_data = {
    "Nivel de riesgo proyectado": {
        "current": 120,
        "previous": 100,
        "inverse": False,
        "suffix": "",
    },
    "Incidentes esperados (reducción)": {
        "current": 8,
        "previous": 12,
        "inverse": True,
        "suffix": "",
    },
    "Precisión del modelo": {
        "current": 0.87,
        "previous": 0.82,
        "inverse": False,
        "suffix": "",
    },
    "Tiempo promedio de respuesta": {
        "current": 45,
        "previous": 50,
        "inverse": True,
        "suffix": " min",
    },
}


# --- KPI layout ---
c1, c2, c3, c4 = st.columns(4)

kpi_metric(
    c1,
    "Nivel de riesgo proyectado",
    kpi_data["Nivel de riesgo proyectado"]["current"],
    kpi_data["Nivel de riesgo proyectado"]["previous"],
    inverse=kpi_data["Nivel de riesgo proyectado"]["inverse"],
    suffix=kpi_data["Nivel de riesgo proyectado"]["suffix"],
)
kpi_metric(
    c2,
    "Incidentes esperados (reducción)",
    kpi_data["Incidentes esperados (reducción)"]["current"],
    kpi_data["Incidentes esperados (reducción)"]["previous"],
    inverse=kpi_data["Incidentes esperados (reducción)"]["inverse"],
    suffix=kpi_data["Incidentes esperados (reducción)"]["suffix"],
)
kpi_metric(
    c3,
    "Precisión del modelo",
    kpi_data["Precisión del modelo"]["current"],
    kpi_data["Precisión del modelo"]["previous"],
    inverse=kpi_data["Precisión del modelo"]["inverse"],
    suffix=kpi_data["Precisión del modelo"]["suffix"],
)
kpi_metric(
    c4,
    "Tiempo promedio de respuesta",
    kpi_data["Tiempo promedio de respuesta"]["current"],
    kpi_data["Tiempo promedio de respuesta"]["previous"],
    inverse=kpi_data["Tiempo promedio de respuesta"]["inverse"],
    suffix=kpi_data["Tiempo promedio de respuesta"]["suffix"],
)

st.divider()


# --- Geospatial predictive map section ---
st.subheader("🗺️ Distribución geográfica proyectada")

try:
    from components.map_view import render_map

    render_map()
except Exception:
    st.markdown(
        """
        <div style="
            width:100%;
            height:520px;
            border-radius:14px;
            border:1px solid rgba(148,163,184,.45);
            background: rgba(10,17,40,.85);
            display:flex; align-items:center; justify-content:center;
        ">
          <span style="opacity:.85">
            Aquí se mostrará el mapa con la distribución espacial del modelo predictivo.
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
