import streamlit as st
from ui.theme_dark import inject_dark_theme
from ui.sidebar_menu import render_sidebar_menu

st.set_page_config(page_title="Panel Principal", layout="wide")
inject_dark_theme()

# Sidebar: Menú + Filtros, con prefijo único para esta página
render_sidebar_menu(show_filters=True, key_prefix="p1_")

# ===== Botón superior =====
if st.button("Haz una pregunta", key="ask", type="primary", use_container_width=True):
    st.switch_page("pages/pagina3.py")

st.divider()

# ===== Helpers KPI con delta (verde/rojo) =====
def fmt_number(x):
    if isinstance(x, float):
        # si parece ratio 0..1 lo mostramos con 2 decimales
        return f"{x:.2f}" if 0 <= x <= 1 else f"{x:,.2f}".replace(",", " ")
    if isinstance(x, (int, float)):
        return f"{x:,.0f}".replace(",", " ")
    return str(x)

def previous_range_label(rango: str) -> str:
    return {
        "Últimas 24h": "24h previas",
        "Última semana": "Semana previa",
        "Último mes": "Mes previo",
    }.get(rango, "Periodo previo")

def kpi_metric(col, label, current, previous, *, inverse=False, suffix=""):
    """
    Muestra un KPI con delta y color automático:
      - inverse=False  -> mayor es mejor (verde si sube)
      - inverse=True   -> menor es mejor (verde si baja)
    """
    delta_txt = "—"
    if previous is not None:
        try:
            change = current - previous
            if previous != 0:
                pct = (change / previous) * 100
                arrow = "↑" if pct >= 0 else "↓"
                delta_txt = f"{arrow}{abs(pct):.1f}% vs {previous_range_label(st.session_state.get('flt_rango_tiempo',''))}"
        except Exception:
            delta_txt = "—"

    delta_color = "inverse" if inverse else "normal"
    value_str = fmt_number(current) + (suffix or "")
    with col:
        st.metric(label=label, value=value_str, delta=delta_txt, delta_color=delta_color)

# ===== Datos de ejemplo (cámbialos por los reales) =====
# Tip: marca inverse=True donde "menos es mejor" (p.ej., tiempos, quejas, incidentes)
data = {
    "Indicador A": {"current": 120, "previous": 100, "inverse": False, "suffix": ""},   # mayor es mejor
    "Indicador B": {"current": 8,   "previous": 12,  "inverse": True,  "suffix": ""},   # menor es mejor
    "Indicador C": {"current": 0.87,"previous": 0.82,"inverse": False, "suffix": ""},   # ratio 0..1
    "Indicador D": {"current": 45,  "previous": 50,  "inverse": True,  "suffix": ""},   # menor es mejor
}

# ===== Render KPIs =====
k1, k2, k3, k4 = st.columns(4)
kpi_metric(k1, "Indicador A", data["Indicador A"]["current"], data["Indicador A"]["previous"], inverse=data["Indicador A"]["inverse"], suffix=data["Indicador A"]["suffix"])
kpi_metric(k2, "Indicador B", data["Indicador B"]["current"], data["Indicador B"]["previous"], inverse=data["Indicador B"]["inverse"], suffix=data["Indicador B"]["suffix"])
kpi_metric(k3, "Indicador C", data["Indicador C"]["current"], data["Indicador C"]["previous"], inverse=data["Indicador C"]["inverse"], suffix=data["Indicador C"]["suffix"])
kpi_metric(k4, "Indicador D", data["Indicador D"]["current"], data["Indicador D"]["previous"], inverse=data["Indicador D"]["inverse"], suffix=data["Indicador D"]["suffix"])

st.divider()

# ===== Mapa (placeholder) =====
st.subheader("🗺️ Mapa")
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
            border:1px solid rgba(99,102,241,.35);
            background: rgba(2,6,23,.6);
            display:flex; align-items:center; justify-content:center;
        ">
          <span style="opacity:.8">Aquí irá tu mapa (components/map_view.py).</span>
        </div>
        """,
        unsafe_allow_html=True
    )
