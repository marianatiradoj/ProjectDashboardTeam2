# Dashboard/pagina1.py
import streamlit as st
from pathlib import Path

from config import ROOT_DIR  # Project root directory
from ui.theme_dark import apply_theme
from ml.ml_analysis import load_bundle
from ml.model_dashboard import run_model_dashboard

# Page configuration
st.set_page_config(page_title="Predicción de delitos", layout="wide")
apply_theme()

# Inject KPI-specific CSS if available
kpi_css_path = ROOT_DIR / "ui" / "kpi_styles.css"
if kpi_css_path.exists():
    st.markdown(
        f"<style>{kpi_css_path.read_text()}</style>",
        unsafe_allow_html=True,
    )
else:
    st.warning("No se encontró el archivo ui/kpi_styles.css.")


@st.cache_resource
def get_bundle():
    """
    Load and cache the full model bundle for inference.
    """
    return load_bundle()


# Cached model bundle used across the page
bundle = get_bundle()

# Run main model dashboard
run_model_dashboard(bundle)
