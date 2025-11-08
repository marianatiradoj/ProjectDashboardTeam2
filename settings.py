import streamlit as st
from ui.theme import inject_css

def app():
    inject_css()
    st.header(":material/settings: Settings")
    st.write("App settings go here.")

if __name__ == "__main__":
    app()
