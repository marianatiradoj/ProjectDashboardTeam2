import streamlit as st
from ui.theme_dark import inject_css


def app():
    inject_css()
    st.header(":material/neurology: Machine Learning")
    st.write("ML analysis workspace. Aquí puedes cargar modelos, métricas y gráficas.")


if __name__ == "__main__":
    app()
