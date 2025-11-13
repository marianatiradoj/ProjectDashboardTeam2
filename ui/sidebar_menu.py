# ui/sidebar_menu.py
import streamlit as st
from ui.filters import render_filters_block


def render_sidebar_menu(show_filters: bool = True, key_prefix: str = ""):
    with st.sidebar:
        st.subheader("🧭 Menú")
        # rutas nuevas relativas a Main.py
        st.page_link(
            "dashboard/pagina2.py", label="Página 1", icon=":material/filter_1:"
        )
        st.page_link(
            "dashboard/pagina1.py", label="Página 2", icon=":material/filter_2:"
        )
        st.page_link(
            "dashboard/pagina3.py", label="Página 3", icon=":material/filter_3:"
        )
        st.page_link(
            "dashboard/pagina4.py", label="Página 4", icon=":material/filter_4:"
        )
        st.markdown("---")

        if show_filters:
            st.subheader("🎛️ Filtros")
            render_filters_block(key_prefix=key_prefix)
