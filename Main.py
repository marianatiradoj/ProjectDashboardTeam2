import streamlit as st
from pathlib import Path

from ui.theme_dark import apply_theme
from config import ROOT_DIR  # project root for all relative paths

# App base config
st.set_page_config(
    page_title="Thales – Panel de analítica",
    page_icon=":material/analytics:",
    layout="wide",
)
apply_theme()

BASE = ROOT_DIR

# Session state defaults
if "role" not in st.session_state:
    st.session_state.role = None

if "go_home" not in st.session_state:
    st.session_state.go_home = False

# Page definitions
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
    title="Tendencias Históricas del Crimen (2016–2024)",
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
    icon="🗂️",
)

page5 = st.Page(
    str(BASE / "Dashboard" / "pagina5.py"),
    title="Dashboard Interactivo",
    icon="🔍",
)

# Navigation logic
role = st.session_state.role

if role is None:
    if st.session_state.go_home:
        st.session_state.go_home = False
        st.session_state.role = "Guest"
        st.rerun()

    # Restricted navigation for anonymous users
    nav = st.navigation([welcome_page])
else:
    # Default page when logged in
    page1.default = True

    # Grouped navigation sections
    nav = st.navigation(
        {
            "Operación y Modelos": [page1, page5],
            "Tendencias y Datos": [page2, page4],
            "Asistentes de IA": [page3],
        }
    )

nav.run()
