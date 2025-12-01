# core/data_loader.py
from pathlib import Path
import json

import pandas as pd
import streamlit as st


# Project-relative paths (stable for local and deploy)
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "Database" / "FGJ_CLEAN_Final.csv"
COLONIAS_GEOJSON_PATH = BASE_DIR / "Geodata" / "colonias_iecm.geojson"


@st.cache_data(show_spinner="Loading historical dataset…")
def load_central_dataset() -> pd.DataFrame:
    """Load the main historical dataset used across the app."""
    return pd.read_csv(DATASET_PATH, low_memory=False)


@st.cache_data(show_spinner="Loading colonias polygons…")
def load_colonias_geojson() -> dict:
    """Load colonias polygons GeoJSON for mapping components."""
    with open(COLONIAS_GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
