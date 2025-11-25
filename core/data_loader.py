from pathlib import Path
import json

import pandas as pd
import streamlit as st

# Resolve project root directory (one level above /core/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Path to the main dataset used across the platform
DATASET_PATH = BASE_DIR / "Database" / "FGJ_CLEAN_Final.csv"

# Path to the colonias polygons used for mapping
COLONIAS_GEOJSON_PATH = BASE_DIR / "Geodata" / "colonias_iecm.geojson"


@st.cache_data(show_spinner="Cargando datos históricos…")
def load_central_dataset() -> pd.DataFrame:
    """
    Load the central historical dataset used across the application.
    Cached for better performance in all pages.
    """
    return pd.read_csv(DATASET_PATH, low_memory=False)


@st.cache_data(show_spinner="Cargando polígonos de colonias…")
def load_colonias_geojson() -> dict:
    """
    Load colonias polygons from a GeoJSON file.

    The returned dictionary can be passed directly to mapping libraries
    that accept GeoJSON-like structures (for example, pydeck or folium).
    """
    with open(COLONIAS_GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
    return geojson_data
