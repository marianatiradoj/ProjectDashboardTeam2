import streamlit as st
from ui.theme import inject_css

def app():
    inject_css()
    st.header(":material/science: Exploratory Data Analysis")
    st.write("EDA workspace. Agrega tus filtros, tablas y visualizaciones aquí.")

if __name__ == "__main__":
    app()
