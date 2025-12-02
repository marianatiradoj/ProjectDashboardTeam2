# Dashboard/pagina5.py
"""
Página 5 – Dashboard interactivo de delitos históricos.

This page:
- Loads the central dataset.
- Applies hierarchical filters.
- Computes and renders KPI cards.
- Renders charts and a geospatial map linked to the same filters.
- Sends the current filter context to the chatbot page on demand.
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
from config import COLONIAS_GEOJSON  # <-- por ahora no se usa aquí directamente
from ui.theme_dark import apply_theme
from core.data_loader import load_central_dataset
from interactive_dashboard.filters import render_filters
from interactive_dashboard.kpis import compute_kpis, render_kpi_cards
from interactive_dashboard.charts import render_main_charts
from interactive_dashboard.maps import render_map_section


# ---------------------------------------------------------------------
# Helper: build a natural-language question for the chatbot
# ---------------------------------------------------------------------
def _build_filter_question(seleccion: dict) -> str:
    """
    Build a Spanish question summarizing current filters
    so the chatbot can generate an executive analysis.
    """
    parts = []

    # Year range
    year_range = seleccion.get("anio_hecho")
    if isinstance(year_range, tuple) and len(year_range) == 2:
        y1, y2 = year_range
        if y1 == y2:
            parts.append(f"en el año {y1}")
        else:
            parts.append(f"entre los años {y1} y {y2}")

    # Month range
    month_range = seleccion.get("mes_hecho")
    if isinstance(month_range, tuple) and len(month_range) == 2:
        m1, m2 = month_range
        if m1 == m2:
            parts.append(f"en el mes de {m1}")
        else:
            parts.append(f"entre los meses de {m1} y {m2}")

    # Weekday range
    day_range = seleccion.get("dia")
    if isinstance(day_range, tuple) and len(day_range) == 2:
        d1, d2 = day_range
        if d1 == d2:
            parts.append(f"en el día {d1}")
        else:
            parts.append(f"entre los días {d1} y {d2}")

    # Crime scope
    macro = seleccion.get("delito_grupo_macro")
    if macro and macro != "Totalidad":
        parts.append(f"para el tipo principal de delito '{macro}'")

    grupo = seleccion.get("delito_grupo")
    if grupo and grupo != "Totalidad":
        parts.append(f"en el grupo de delito '{grupo}'")

    # Geography
    alc = seleccion.get("alcaldia_hecho")
    if alc and alc != "Totalidad":
        parts.append(f"en la alcaldía {alc}")

    region = seleccion.get("region_cdmx")
    if region and region != "Totalidad":
        parts.append(f"en la región {region}")

    # Time of day
    periodo = seleccion.get("periodo_hora")
    if periodo and periodo != "Totalidad":
        parts.append(f"en el periodo del día '{periodo}'")

    # Violence and climate
    violencia = seleccion.get("clase_violencia")
    if violencia and violencia != "Totalidad":
        parts.append(f"con tipo de violencia '{violencia}'")

    clima = seleccion.get("clima_condicion")
    if clima and clima != "Totalidad":
        parts.append(f"cuando la condición climática es '{clima}'")

    quincena = seleccion.get("quincena")
    if quincena and quincena != "Totalidad":
        parts.append(f"dentro de la ventana de quincena '{quincena}'")

    if parts:
        scope = ", ".join(parts)
    else:
        scope = "en todo el histórico disponible"

    question = (
        "Con base en el dataset histórico de delitos, genera un análisis ejecutivo "
        f"de las tendencias delictivas {scope}. Incluye: evolución temporal, "
        "alcaldías y zonas más afectadas, tipos de delito predominantes, patrones "
        "por día y horario, y tres recomendaciones accionables para la autoridad."
    )
    return question


# ---------------------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard interactivo",
    layout="wide",
)

# Apply global dark theme.
apply_theme()

# Inject KPI CSS if available.
CSS_PATH = Path(ROOT_DIR) / "ui" / "kpi_styles.css"
if CSS_PATH.exists():
    st.markdown(
        f"<style>{CSS_PATH.read_text()}</style>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Main page entrypoint
# ---------------------------------------------------------------------
def main() -> None:
    """Main entrypoint for the interactive crime dashboard page."""
    # Title and short intro
    st.title("Dashboard interactivo de delitos históricos")
    st.markdown(
        """
        Este tablero permite explorar la dinámica histórica de los delitos en la ciudad.
        Utiliza los filtros del panel lateral para acotar el periodo, el tipo de delito
        y las características contextuales de los incidentes.
        """
    )

    # Load unified dataset (cached helper)
    df = load_central_dataset()

    st.write("Total de registros:", len(df))

    if "anio_hecho" in df.columns:
        st.write("Registros por año (df):")
        st.write(df["anio_hecho"].value_counts().sort_index())

    # Apply hierarchical filters (time, crime, geography, context)
    df_filtrado, seleccion = render_filters(df)

    st.write("Registros después de filtros:", len(df_filtrado))

    # Expose filter context so other pages (e.g. chatbot) can reuse it
    st.session_state["interactive_filters"] = seleccion

    # Button to send filters to chatbot page with an auto-generated question
    st.markdown("---")
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button(
            "💬 Enviar estos filtros al chatbot",
            help="Abre el asistente y genera un análisis automático usando esta configuración de filtros.",
        ):
            auto_q = _build_filter_question(seleccion)
            st.session_state["chatbot_use_filters_once"] = True
            st.session_state["chatbot_auto_question"] = auto_q
            st.switch_page("Dashboard/pagina3.py")

    # Empty-state guard
    if df_filtrado is None or df_filtrado.empty:
        st.warning(
            "No hay registros que cumplan con la combinación actual de filtros. "
            "Ajusta los criterios en el panel lateral para ampliar el universo de análisis."
        )
        return

    # KPI cards based on filtered subset
    kpis = compute_kpis(df_filtrado)
    render_kpi_cards(kpis)

    # Charts linked to the same filters
    st.markdown("---")
    render_main_charts(df_filtrado, seleccion)

    # Geospatial map linked to the same filters
    st.markdown("---")
    # ⬇️ Aquí está la corrección: ya NO pasamos 'colonias_path' como keyword
    render_map_section(df_filtrado)


# Streamlit entrypoint
if __name__ == "__main__":
    main()
