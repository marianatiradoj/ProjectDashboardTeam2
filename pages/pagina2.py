import streamlit as st
from ui.theme_dark import inject_dark_theme
from ui.sidebar_menu import render_sidebar_menu

st.set_page_config(page_title="Página 2", layout="wide")
inject_dark_theme()
render_sidebar_menu(show_filters=True)

st.title("Página 2")
st.write("Contenido de la página 2.")
