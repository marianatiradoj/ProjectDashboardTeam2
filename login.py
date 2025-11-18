import streamlit as st
from ui.theme_dark import inject_css

ROLES = ["Admin", "Decision Maker", "Citizen", "Guest"]


def app():
    inject_css()
    st.header(":material/login: Log in")
    st.write("Select your role to access the appropriate workspace.")
    role = st.selectbox("Choose your role", ROLES, index=ROLES.index("Guest"))
    if st.button("Log in", use_container_width=True):
        st.session_state.role = role
        st.rerun()


if __name__ == "__main__":
    app()
