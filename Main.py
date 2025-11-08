import streamlit as st
from pathlib import Path

st.set_page_config(page_title="", page_icon=":material/analytics:", layout="wide")
BASE = Path(__file__).parent

if "role" not in st.session_state:
    st.session_state.role = None
if "go_home" not in st.session_state:
    st.session_state.go_home = False

welcome_page = st.Page(str(BASE / "welcome.py"), title="Welcome", icon=":material/home:", default=True)
home_page = st.Page(str(BASE / "dashboard" / "home.py"), title="Dashboard", icon=":material/monitoring:")

role = st.session_state.role

if role is None:
    if st.session_state.go_home:
        st.session_state.go_home = False
        st.session_state.role = "Guest"
        st.rerun()
    pg = st.navigation([welcome_page])
else:
    home_page.default = True
    pg = st.navigation({"Panel": [home_page]})

pg.run()

