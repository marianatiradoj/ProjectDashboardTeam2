# Dashboard/pagina3.py
import streamlit as st
from ui.theme_dark import apply_theme
from chatbot.chatbot_app import run_chatbot_page

# Page-level configuration
st.set_page_config(
    page_title="Consultor Inteligente de Datos",
    layout="wide",
)
apply_theme()

# Header section
st.title("Consultor Inteligente de Datos")
st.caption(
    "Asistente conversacional para consultar información y generar análisis en tiempo real. "
    "Puedes usar los filtros del dashboard interactivo para generar un análisis específico."
)
st.divider()

# --- Load filter context (generated in the interactive dashboard) ---
# If the user previously selected filters on Page 5, they are stored here.
filter_context = st.session_state.get("interactive_filters")

# --- Optional trigger to use interactive dashboard filters ---
# User decides when the chatbot should answer based on filters.
col1, col2 = st.columns([1, 3])
with col1:
    use_filters = st.button(
        "Generar análisis con filtros del dashboard",
        help="Usa los filtros activos del dashboard para generar una respuesta contextualizada.",
    )

# Store one-time activation so chatbot knows when to read filters
if use_filters:
    st.session_state["chatbot_use_filters_once"] = True

# --- Render chatbot interface ---
# The chatbot behaves normally unless the user triggers filter-based reasoning.
run_chatbot_page(filter_context=filter_context)
