import streamlit as st
from pathlib import Path
import base64
import mimetypes

def _load_bg_as_base64(path: Path):
    """Convierte la imagen de fondo a base64."""
    if not path.exists():
        return None, None
    mime, _ = mimetypes.guess_type(str(path))
    if mime is None:
        mime = "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return mime, b64

def app():
    # ======== FONDO ========
    bg_path = Path("images/welcome_bg.jpg")
    mime, b64 = _load_bg_as_base64(bg_path)

    if b64:
        bg_rule = f"background-image:url('data:{mime};base64,{b64}');"
    else:
        bg_rule = "background: radial-gradient(1200px 600px at 20% 30%, #1f4dcf22, transparent), #0B1120;"

    # ======== CSS ========
    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            height: 100%;
            margin: 0;
            overflow: hidden;
        }}

        body, .stApp {{
            {bg_rule}
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
        }}

        [data-testid="stAppViewContainer"] {{
            background: rgba(0,0,0,0.38) !important;
            backdrop-filter: blur(6px);
        }}

        header[data-testid="stHeader"] {{
            background: linear-gradient(90deg, #1E3A8A, #2563EB);
        }}

        main.block-container {{
            padding: 0 !important;
            margin: 0 !important;
            height: 100vh !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }}

        /* ===== CONTENEDOR HERO ===== */
        .hero-centered {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 1.2rem;
            max-width: 600px;
            width: 100%;
        }}

        /* Logo */
        .brand img {{
            width: clamp(200px, 38vw, 380px);
            height: auto;
            filter: drop-shadow(0 6px 24px rgba(0,0,0,.35));
        }}

        /* Texto principal */
        .title {{
            color: #60A5FA !important;
            font-weight: 900 !important;
            font-size: clamp(1.8rem, 4vw, 2.8rem);
            margin: 0.25rem 0 1rem 0;
            text-shadow: 0 2px 10px rgba(0,0,0,.35);
        }}

        /* Botón principal */
        div.stButton > button:first-child {{
            background:#2563EB !important; color:#fff !important;
            border:0 !important; border-radius:12px !important;
            height:3.25rem !important; font-size:1.08rem !important; font-weight:800 !important;
            width: min(520px, 88vw) !important;
            box-shadow: 0 10px 28px rgba(37,99,235,.45) !important;
            transition: transform .15s ease, box-shadow .15s ease, filter .15s ease !important;
        }}
        div.stButton > button:hover {{
            filter: brightness(1.05) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 14px 36px rgba(37,99,235,.55) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ======== CONTENIDO ========
    st.markdown('<div class="hero-centered">', unsafe_allow_html=True)

    logo = Path("images/horizontal_blue.png")
    if logo.exists():
        st.markdown('<div class="brand">', unsafe_allow_html=True)
        st.image(str(logo))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="title">Bienvenido</div>', unsafe_allow_html=True)

    if st.button("Inicia Sesión"):
        st.session_state.role = "Guest"
        st.session_state.go_home = True
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    app()
