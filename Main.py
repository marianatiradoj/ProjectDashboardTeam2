# Main.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Team 2 • Crime Dashboard",
    page_icon="🗺️",
    layout="wide"
)

# =========================
# Sidebar (navigation + controls)
# =========================
st.sidebar.title("Controls")
crime_type = st.sidebar.selectbox(
    "Crime type",
    ["All", "Robbery", "Assault", "Burglary"]
)
horizon = st.sidebar.radio("Prediction horizon", ["24h", "48h"], index=0)
show_table = st.sidebar.toggle("Show table", value=True)
st.sidebar.caption("Theme colors are defined in .streamlit/config.toml")

# =========================
# Title / Intro
# =========================
st.title("Team 2 — Safe & Smart City")
st.write(
    "Initial scaffold with a Folium map and a dummy dataframe. "
    "Model outputs and advanced UI will be integrated next."
)

# =========================
# Dummy data (replace later with your real pipeline/model output)
# =========================
# Si prefieres un CSV temporal:
# df = pd.read_csv("data/dummy_crime.csv")

df = pd.DataFrame({
    "crime_type": ["Robbery", "Assault", "Burglary", "Robbery"],
    "lat": [19.4326, 19.4450, 19.4100, 19.4280],
    "lon": [-99.1332, -99.1400, -99.1200, -99.1500],
    "severity": [0.7, 0.5, 0.6, 0.8],
})

if crime_type != "All":
    df_view = df[df["crime_type"] == crime_type].copy()
else:
    df_view = df.copy()

# =========================
# MAP BUILDER
# =========================
# OPCIÓN A) Si ya tienes tu función de mapa, impórtala aquí:
# from services.map_builder import build_map
# def create_map(dataframe):
#     return build_map(dataframe, horizon=horizon)   # adapta firma según tu código

# OPCIÓN B) Si aún no la tienes como función, pega tu lógica de Folium
#           EN LUGAR del bloque simple de abajo y retorna "m" (folium.Map).
def create_map(dataframe):
    # --- Simple placeholder map (reemplaza con tu código) ---
    m = folium.Map(location=[19.4326, -99.1332], zoom_start=12, tiles="cartodbpositron")

    BLUE = "#2563EB"  # combina con tu paleta azul
    for _, r in dataframe.iterrows():
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            popup=f"{r['crime_type']} — severity: {r['severity']}",
            color=BLUE,
            fill=True,
            fill_color=BLUE,
            fill_opacity=0.7
        ).add_to(m)
    return m

# =========================
# Render
# =========================
st.subheader(f"Map • {crime_type} • {horizon}")
map_obj = create_map(df_view)
st_map = st_folium(map_obj, height=600, width=None)

if show_table:
    st.subheader("Data")
    st.dataframe(df_view, use_container_width=True)

# =========================
# Footnote (helps your evidence box)
# =========================
st.markdown("""
**This task delivers:**
- Initial Streamlit structure (sidebar, layout, theme).
- Placeholder Folium map integrated in Streamlit.
- Dummy dataframe + basic filtering.
- Ready to plug in your real map builder and model outputs.
""")

