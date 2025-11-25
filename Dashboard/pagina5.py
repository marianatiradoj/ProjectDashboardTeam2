# Dashboard/pagina5.py
"""
Página 5 – Dashboard interactivo de delitos históricos.

This page:
- Loads the central dataset.
- Applies hierarchical filters.
- Computes and renders KPI cards.
- Provides a base layout for charts and maps.
"""

import os
import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------
# Path setup so core and interactive modules can be imported
# ---------------------------------------------------------------------
THIS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(THIS_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------
from ui.theme_dark import apply_theme
from core.data_loader import load_central_dataset
from interactive_dashboard.filters import render_filters
from interactive_dashboard.kpis import compute_kpis, render_kpi_cards
from interactive_dashboard.charts import render_main_charts
from interactive_dashboard.maps import render_map_section


# ---------------------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Página 5 – Dashboard interactivo",
    layout="wide",
)

# Apply global dark theme styles for consistency across the app.
apply_theme()

# Load external CSS for KPI cards
CSS_PATH = Path(ROOT_DIR) / "ui" / "kpi_styles.css"
if CSS_PATH.exists():
    with open(CSS_PATH, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Main page entrypoint
# ---------------------------------------------------------------------
def main() -> None:
    """
    Main entrypoint for the interactive crime dashboard page.
    """

    # 1. Page title and short introduction
    st.title("Dashboard interactivo de delitos históricos")

    st.markdown(
        """
        Este tablero permite explorar la dinámica histórica de los delitos en la ciudad.
        Utiliza los filtros del panel lateral para acotar el periodo, el tipo de delito
        y las características contextuales de los incidentes.
        """
    )

    # 2. Load unified dataset (cached in core.data_loader)
    df = load_central_dataset()

    # 3. Render filters and obtain filtered dataframe + selections
    df_filtrado, seleccion = render_filters(df)

    # 4. Handle empty result sets
    if df_filtrado is None or df_filtrado.empty:
        st.warning(
            "No hay registros que cumplan con la combinación actual de filtros. "
            "Ajusta los criterios en el panel lateral para ampliar el universo de análisis."
        )
        return

    # 5. Compute and render KPI cards
    kpis = compute_kpis(df_filtrado)
    render_kpi_cards(kpis)

    # 6. Placeholder for charts and maps (to be implemented)
    st.markdown("---")
    st.markdown(
        "En las siguientes secciones se integrarán las gráficas interactivas y el mapa "
        "geoespacial vinculados a los mismos filtros."
    )
    render_main_charts(df_filtrado, seleccion)

    # 7. Mapa interactivo vinculado a los mismos filtros
    st.markdown("---")
    render_map_section(df_filtrado)


if __name__ == "__main__":
    main()
