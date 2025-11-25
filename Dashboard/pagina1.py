# Dashboard/pagina1.py
import os
import sys

import streamlit as st

# ================== RUTAS / IMPORTS ==================
THIS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(THIS_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ui.theme_dark import apply_theme
from ml.ml_analysis import load_bundle
from ml.model_dashboard import run_model_dashboard

# ================== CONFIG GLOBAL DE LA PÁGINA ==================
st.set_page_config(page_title="Predicción de delitos – Página 1", layout="wide")
apply_theme()

# ================== INYECTAR CSS DE KPIs ==================
kpi_css_path = os.path.join(ROOT_DIR, "ui", "kpi_styles.css")
if os.path.exists(kpi_css_path):
    with open(kpi_css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("No se encontró ui/kpi_styles.css. Verifica la ruta del CSS de KPIs.")


# ================== CARGA ÚNICA DEL BUNDLE (cacheado) ==================
@st.cache_resource
def get_bundle():
    return load_bundle()


bundle = get_bundle()

# ================== CORRER TODO EL DASHBOARD DEL MODELO ==================
run_model_dashboard(bundle)
