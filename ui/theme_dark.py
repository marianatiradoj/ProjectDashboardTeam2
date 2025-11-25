# ui/theme_dark.py

import streamlit as st


def apply_theme():
    css = """
    <style>

    /* ============================================
       PALETA – CORPORATE BLUE (Moderna y formal)
       ============================================ */
    :root {
        --accent: #4DA3FF;              /* Azul Aurora */
        --accent-strong: #1E6FFF;       /* Azul intenso */
        --accent-hover: #8BC3FF;        /* Hover suave */
        
        --bg-main: #050816;             /* Fondo general */
        --bg-sidebar: #0B1120;          /* Sidebar profesional */
        --border-subtle: #1F2937;
    }

    /* ============================================
       FONDO DEL APLICATIVO
       ============================================ */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-main) !important;
    }

    /* ============================================
       SIDEBAR — ESTILO PROFESIONAL
       ============================================ */
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(
            180deg,
            #0F172A 0%,
            var(--bg-sidebar) 100%
        ) !important;
        border-right: 1px solid #0F1A2E !important;
        box-shadow: 6px 0px 18px rgba(10, 20, 40, 0.65);
        padding-top: 1rem !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #E5E7EB !important;
    }

    /* Links del menú (Panel) */
    [data-testid="stSidebar"] a {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.45rem 0.75rem;
        font-size: 14px !important;
        border-radius: 10px;
        color: #E5E7EB !important;
        transition: background 0.15s ease, transform 0.12s ease;
    }

    [data-testid="stSidebar"] a:hover {
        background-color: rgba(77,163,255,0.16) !important;
        color: #FFFFFF !important;
        transform: translateX(2px);
    }

    [data-testid="stSidebar"] a[aria-current="page"] {
        background: rgba(77,163,255,0.28) !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: inset 0 0 0 1px rgba(77,163,255,0.4);
    }

    /* Separadores */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08) !important;
    }

    /* ============================================
       SELECTBOX / MULTISELECT
       ============================================ */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background-color: #0D1525 !important;
        border: 1px solid #1F2937 !important;
        border-radius: 8px !important;
        color: white !important;
    }

    div[data-baseweb="menu"] {
        background-color: #0A101B !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="menu"] li {
        padding: 10px 14px !important;
        font-size: 15px !important;
        border-radius: 6px !important;
        color: #E5E7EB !important;
    }

    div[data-baseweb="menu"] li:hover {
        background-color: var(--accent-hover) !important;
        color: #0B1120 !important;
    }

    div[data-baseweb="menu"] li[aria-selected="true"] {
        background-color: var(--accent) !important;
        color: #0B1120 !important;
    }

    /* ============================================
       SLIDERS
       ============================================ */
    .stSlider > div > div > div {
        color: var(--accent) !important;
    }
    .stSlider > div [data-baseweb="slider"] {
        background-color: var(--accent) !important;
    }

    /* ============================================
       BOTONES
       ============================================ */
    div.stButton > button {
        background-color: var(--accent-strong) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: background 0.15s ease;
    }

    div.stButton > button:hover {
        background-color: var(--accent) !important;
        color: #0B1120 !important;
    }

    /* ============================================
       MÉTRICAS
       ============================================ */
    [data-testid="stMetricValue"] {
        color: white !important;
    }
    [data-testid="stMetricLabel"] {
        color: #BFC5D0 !important;
    }

    /* ============================================
       TARJETAS (.panel-card)
       ============================================ */
    .panel-card {
        background: rgba(15,23,42,0.96);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 12px 28px rgba(0,0,0,0.55);
    }

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def inject_dark_theme():
    apply_theme()
