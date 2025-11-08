import streamlit as st
from pathlib import Path
from ui.theme import inject_css

def app():
    # --- No inyectamos el tema global claro ---
    # inject_css()  # <- coméntalo para que no aplique el fondo claro

    # ===== CSS oscuro solo para esta página =====
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #0B1120 !important;  /* azul oscuro */
            color: #ffffff !important;             /* texto blanco */
        }

        header[data-testid="stHeader"] {
            background: linear-gradient(90deg, #1E3A8A, #2563EB); /* barra azul */
        }

        /* Etiquetas de texto */
        label, p, h1, h2, h3, h4, h5, h6, div, span {
            color: #f1f5f9 !important;
        }

        /* Campos de entrada */
        input[type="text"], input[type="password"] {
            background-color: #1E293B !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }

        /* Botón principal */
        div.stButton > button:first-child {
            background-color: #2563EB !important;
            color: white !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 10px !important;
            height: 3rem !important;
            width: 100% !important;
            box-shadow: 0 4px 12px rgba(37,99,235,.45);
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #1e50d6 !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(37,99,235,.65);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ===== Layout dividido =====
    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        logo_path = Path("images/horizontal_blue.png")
        if logo_path.exists():
            st.image(str(logo_path), width=160)
        else:
            st.caption("Coloca tu logo en `images/horizontal_blue.png` (opcional).")

        st.markdown(
            """
            <h2 style="font-weight:800; margin-bottom:0;">Welcome Back</h2>
            <p style="color:#CBD5E1; margin-top:0.25rem;">Click to log in</p>
            """,
            unsafe_allow_html=True,
        )
### SI SE QUIERE INCORPORAR USERS
       # email = st.text_input("Email Address")
       # password = st.text_input("Password", type="password")
### ------------------------------------------------------------------
        if st.button("Log In", use_container_width=True):
            st.session_state.role = "Guest"
            st.session_state.go_home = True
            st.rerun()

    with col2:
        img_path = Path("images/welcome_image.jpg")
        if img_path.exists():
            st.image(str(img_path), use_container_width=True)
        else:
            st.warning("Sube una imagen a `images/welcome_image.jpg` para mostrar aquí.")

if __name__ == "__main__":
    app()
