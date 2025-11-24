# Dashboard/pagina3.py
import streamlit as st
from ui.theme_dark import apply_theme
from chatbot.chatbot_app import run_chatbot_page


# --- Initial configuration and global theme ---
st.set_page_config(
    page_title="Consultor Inteligente de Datos",
    layout="wide",
)
apply_theme()


# --- Page header ---
st.title("Consultor Inteligente de Datos")
st.caption(
    "Asistente conversacional para consultar información y generar análisis en tiempo real."
)
st.divider()


# --- Chat assistant module ---
run_chatbot_page()
