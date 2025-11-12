import streamlit as st
from ui.filters import render_filters_block

def render_sidebar_menu(show_filters: bool = True):
    """Sidebar propio: Menú de páginas + (opcional) filtros."""
    with st.sidebar:
        st.subheader("🧭 Menú")
        # Ajusta las rutas si tus archivos se llaman distinto
        st.page_link("pages/pagina1.py", label="Dashboard y Mapa", icon=":material/filter_1:")
        st.page_link("pages/pagina2.py", label="Gráficas", icon=":material/filter_2:")
        st.page_link("pages/pagina3.py", label="LLM", icon=":material/filter_3:")
        st.markdown("---")
        if show_filters:
            st.subheader("🎛️ Filtros")
            render_filters_block()
