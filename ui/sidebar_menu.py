# ui/sidebar_menu.py
import streamlit as st


def render_sidebar_menu(show_filters: bool = True, key_prefix: str = ""):
    """
    Sidebar sencillo:
      - Menú con las 4 páginas
      - SIN filtros globales (los filtros del EDA viven dentro de pagina2.py)

    Los parámetros show_filters y key_prefix se dejan para no romper llamadas
    anteriores, pero aquí no se usan.
    """
    with st.sidebar:
        st.subheader("📌 Menú")

        # 👇 Ajusta las rutas si tus archivos se llaman diferente
        st.page_link("Dashboard/pagina1.py", label="Página 1", icon=":material/map:")
        st.page_link("Dashboard/pagina2.py", label="Página 2", icon=":material/insights:")
        st.page_link("Dashboard/pagina3.py", label="Página 3", icon=":material/neurology:")
        st.page_link("Dashboard/pagina4.py", label="Página 4", icon=":material/table_view:")

        st.markdown("---")
        # Nada de filtros aquí. Los filtros específicos se dibujan en cada página.
