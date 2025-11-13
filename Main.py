import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Thales", page_icon=":material/analytics:", layout="wide")
BASE = Path(__file__).parent

# Estado
if "role" not in st.session_state:
    st.session_state.role = None
if "go_home" not in st.session_state:
    st.session_state.go_home = False

# === Páginas ===
welcome_page = st.Page(
    str(BASE / "welcome.py"), title="Welcome", icon=":material/home:", default=True
)

# OJO: ahora van dentro de /dashboard
page1 = st.Page(
    str(BASE / "dashboard" / "pagina2.py"), title="Página 1", icon=":material/filter_1:"
)
page2 = st.Page(
    str(BASE / "dashboard" / "pagina1.py"), title="Página 2", icon=":material/filter_2:"
)
page3 = st.Page(
    str(BASE / "dashboard" / "pagina3.py"), title="Página 3", icon=":material/filter_3:"
)
page4 = st.Page(
    str(BASE / "dashboard" / "pagina4.py"), title="Página 4", icon=":material/filter_4:"
)

# === Navegación ===
role = st.session_state.role

if role is None:
    if st.session_state.go_home:
        st.session_state.go_home = False
        st.session_state.role = "Guest"
        st.rerun()
    pg = st.navigation([welcome_page])
else:
    page1.default = True
    pg = st.navigation(
        {
            "Panel": [page1, page2, page3, page4],
        }
    )

pg.run()
