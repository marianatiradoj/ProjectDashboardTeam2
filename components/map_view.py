import streamlit as st

def render_map():
    st.markdown(
        """
        <div style="
            width:100%;
            height:520px;
            border-radius:14px;
            border:1px solid rgba(99,102,241,.35);
            background: rgba(2,6,23,.6);
            display:flex; align-items:center; justify-content:center;
        ">
          <span style="opacity:.8">Aquí irá tu mapa (Folium/pydeck).</span>
        </div>
        """,
        unsafe_allow_html=True
    )
