import streamlit as st
from ui.theme_dark import inject_dark_theme
from ui.sidebar_menu import render_sidebar_menu

st.set_page_config(page_title="Datos Históricos", layout="wide")
inject_dark_theme()

render_sidebar_menu(show_filters=True, key_prefix="p2_")

# ===== Título principal =====
st.title("Datos Históricos")
st.caption("Visualización exploratoria de los datos (EDA).")

st.divider()

# ===== Layout 2 x 2 para 4 gráficas =====
col1, col2 = st.columns(2, gap="large")

# --- Columna izquierda ---
with col1:
    st.subheader("Gráfica 1")
    graf1 = st.empty()   # aquí luego metemos, por ejemplo: render_eda_chart1()
    graf1.markdown(
        """
        <div style="
            width:100%;
            height:260px;
            border-radius:14px;
            border:1px dashed rgba(148,163,184,.6);
            background: rgba(15,23,42,.65);
            display:flex;align-items:center;justify-content:center;
        ">
          <span style="opacity:.8">Espacio reservado para Gráfica 1</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Gráfica 2")
    graf2 = st.empty()
    graf2.markdown(
        """
        <div style="
            width:100%;
            height:260px;
            border-radius:14px;
            border:1px dashed rgba(148,163,184,.6);
            background: rgba(15,23,42,.65);
            display:flex;align-items:center;justify-content:center;
        ">
          <span style="opacity:.8">Espacio reservado para Gráfica 2</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Columna derecha ---
with col2:
    st.subheader("Gráfica 3")
    graf3 = st.empty()
    graf3.markdown(
        """
        <div style="
            width:100%;
            height:260px;
            border-radius:14px;
            border:1px dashed rgba(148,163,184,.6);
            background: rgba(15,23,42,.65);
            display:flex;align-items:center;justify-content:center;
        ">
          <span style="opacity:.8">Espacio reservado para Gráfica 3</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Gráfica 4")
    graf4 = st.empty()
    graf4.markdown(
        """
        <div style="
            width:100%;
            height:260px;
            border-radius:14px;
            border:1px dashed rgba(148,163,184,.6);
            background: rgba(15,23,42,.65);
            display:flex;align-items:center;justify-content:center;
        ">
          <span style="opacity:.8">Espacio reservado para Gráfica 4</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
