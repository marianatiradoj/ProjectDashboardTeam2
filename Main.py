import streamlit as st
from pathlib import Path

from ui.theme_dark import apply_theme

# =========================================
# CONFIGURACIÓN GLOBAL
# =========================================
st.set_page_config(
    page_title="Thales – Panel de analítica",
    page_icon=":material/analytics:",
    layout="wide",
)
apply_theme()

BASE = Path(__file__).parent

# =========================================
# ESTADO
# =========================================
if "role" not in st.session_state:
    st.session_state.role = None

if "go_home" not in st.session_state:
    st.session_state.go_home = False

# =========================================
# DEFINICIÓN DE PÁGINAS (NOMBRES EJECUTIVOS)
# =========================================
welcome_page = st.Page(
    str(BASE / "welcome.py"),
    title="Welcome",
    icon="🏠",
    default=True,
)

page1 = st.Page(
    str(BASE / "Dashboard" / "pagina1.py"),
    title="Modelo Predictivo – Forecasting Operativo",
    icon="🧮",
)
page2 = st.Page(
    str(BASE / "Dashboard" / "pagina2.py"),
    title="Dashboard Histórico – Tendencias",
    icon="📈",
)
page3 = st.Page(
    str(BASE / "Dashboard" / "pagina3.py"),
    title="Consultor Inteligente de Datos",
    icon="🤖",
)
page4 = st.Page(
    str(BASE / "Dashboard" / "pagina4.py"),
    title="Integración & EDA de Datos",
    icon="🧬",
)

page5 = st.Page(
    str(BASE / "Dashboard" / "pagina5.py"),
    title="Prueba de filtros – Página 5",
    icon="🔍",
)

# =========================================
# NAVEGACIÓN
# =========================================
role = st.session_state.role

if role is None:
    if st.session_state.go_home:
        st.session_state.go_home = False
        st.session_state.role = "Guest"
        st.rerun()

    nav = st.navigation([welcome_page])
else:
    page1.default = True
    nav = st.navigation(
        {
            "Panel": [page1, page2, page3, page4, page5],
        }
    )

nav.run()
