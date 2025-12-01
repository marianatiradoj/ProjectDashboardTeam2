import streamlit as st


def render_sidebar_menu(show_filters: bool = True, key_prefix: str = ""):
    with st.sidebar:
        st.markdown("### 📌 Menú")

        if st.button(
            "Página 1 – Panel principal",
            key=f"{key_prefix}sb_p1",
            use_container_width=True,
        ):
            st.switch_page("Dashboard/pagina1.py")

        if st.button(
            "Página 2 – Datos históricos",
            key=f"{key_prefix}sb_p2",
            use_container_width=True,
        ):
            st.switch_page("Dashboard/pagina2.py")

        if st.button(
            "Página 3 – Chatbot", key=f"{key_prefix}sb_p3", use_container_width=True
        ):
            st.switch_page("Dashboard/pagina3.py")

        if st.button(
            "Página 4 – EDA & carga", key=f"{key_prefix}sb_p4", use_container_width=True
        ):
            st.switch_page("Dashboard/pagina4.py")

        if show_filters:
            st.markdown("---")
            st.markdown("#### 🎛️ Filtros")
            st.caption("Los filtros propios de cada página aparecen aquí.")
