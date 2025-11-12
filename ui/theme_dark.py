import streamlit as st

def inject_dark_theme():
    """Tema oscuro global + fix selects + oculta panel nativo del sidebar."""
    st.markdown("""
    <style>
    html, body, .stApp { background-color:#0B1120 !important; color:#E2E8F0 !important; font-family:'Inter',sans-serif !important; }
    header[data-testid="stHeader"] { background:linear-gradient(90deg,#1E3A8A,#2563EB); color:#fff !important; }
    section[data-testid="stSidebar"] { background-color:#111827 !important; border-right:1px solid #1E293B !important; }
    .stSidebar [data-testid="stSidebarNavItems"] a span { color:#E2E8F0 !important; }
    h1,h2,h3,h4,h5,h6,label,p,span,div { color:#E2E8F0 !important; }

    .stButton>button{
      background:linear-gradient(90deg,#2563EB,#1E40AF) !important; color:#fff !important; border:none !important; border-radius:10px !important;
      font-weight:600 !important; box-shadow:0 4px 16px rgba(37,99,235,.35); transition:.2s;
    }
    .stButton>button:hover{ background:linear-gradient(90deg,#1E40AF,#1D4ED8) !important; transform:translateY(-2px); box-shadow:0 6px 20px rgba(37,99,235,.55); }

    input[type="text"], input[type="password"], textarea, select {
      background-color:#1E293B !important; color:#E2E8F0 !important; border:1px solid #334155 !important; border-radius:8px !important;
    }

    hr,.stDivider{ border-color:#1E293B !important; }
    .stTabs [data-baseweb="tab"]{ background:#1E293B !important; color:#E2E8F0 !important; border-radius:10px !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"]{ color:#E2E8F0 !important; }
    a,a:visited{ color:#60A5FA !important; }
    footer{ visibility:hidden; }

    /* Selects + menú en portal */
    .stSelectbox label,.stMultiSelect label,label{ color:#e2e8f0 !important; font-weight:600 !important; }
    div[data-baseweb="select"]>div{ background:#0f172a !important; color:#f8fafc !important; border:1px solid #334155 !important; border-radius:10px !important; }
    div[data-baseweb="select"] span{ color:#f8fafc !important; }
    div[data-baseweb="select"] [aria-hidden="true"]{ color:#94a3b8 !important; }
    div[data-baseweb="tag"]{ background:#1f2937 !important; color:#e5e7eb !important; border:1px solid #334155 !important; }

    body div[data-baseweb="popover"], body div[data-baseweb="menu"], body [role="listbox"]{
      background:#0a0f1a !important; border:1px solid #1e293b !important; box-shadow:0 12px 28px rgba(0,0,0,.45) !important; color:#e2e8f0 !important;
    }
    body [role="listbox"] [role="option"], body [role="listbox"] [role="option"] *{
      color:#e2e8f0 !important; -webkit-text-fill-color:#e2e8f0 !important; opacity:1 !important; background:transparent !important;
    }
    body [role="listbox"] [role="option"]:hover, body [role="listbox"] [role="option"][aria-selected="true"]{
      background:#2563eb !important; color:#fff !important; -webkit-text-fill-color:#fff !important;
    }

    /* ❌ Ocultar solo el panel nativo de páginas en el sidebar */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"],
    section[data-testid="stSidebar"] [data-testid="stSidebarPages"]{
      display:none !important;
    }
    </style>
    """, unsafe_allow_html=True)
