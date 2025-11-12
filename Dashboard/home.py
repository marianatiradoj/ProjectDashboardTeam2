import streamlit as st
from ui.theme_dark import inject_dark_theme

inject_dark_theme()


def topbar():
    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    col1, col2 = st.columns([6,1])
    with col2:
        if st.button("Log out", use_container_width=True):
            st.session_state.role = None
            st.session_state.go_home = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def app():
    inject_css()
    topbar()

    st.sidebar.title("Panel")
    st.sidebar.write("Filtros iniciales")
    st.sidebar.selectbox("Rango de tiempo", ["Últimas 24h", "Última semana", "Último mes"])
    st.sidebar.multiselect("Zonas", ["Norte", "Sur", "Este", "Oeste"])
    st.sidebar.divider()
    st.sidebar.caption("Configura tus vistas desde aquí.")

    st.header(":material/monitoring: Dashboard")
    st.caption("Vista principal del panel de datos.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Indicador A", "—")
    k2.metric("Indicador B", "—")
    k3.metric("Indicador C", "—")
    k4.metric("Indicador D", "—")
    st.divider()
    st.write("Agrega aquí tus componentes principales o visualizaciones.")

if __name__ == "__main__":
    app()
