import streamlit as st

PALETTE = {
    "primary": "#2563EB",
    "bg": "#F5F7FA",
    "panel": "#FFFFFF",
    "text": "#0F172A",
    "muted": "#475569",
}

def inject_css():
    st.markdown(
        f"""
        <style>
          :root {{
            --primary: {PALETTE["primary"]};
            --bg: {PALETTE["bg"]};
            --panel: {PALETTE["panel"]};
            --text: {PALETTE["text"]};
            --muted: {PALETTE["muted"]};
          }}

          .stApp {{
            background: var(--bg);
            color: var(--text);
          }}

          header[data-testid="stHeader"] {{
            background: linear-gradient(90deg, #2563EB, #3B82F6);
          }}

          label {{
            font-weight: 600 !important;
            color: var(--text) !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )
