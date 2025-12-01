# config.py
import os
from pathlib import Path

# Project root (base directory for all relative paths)
ROOT_DIR = Path(__file__).resolve().parent

# Core datasets
DATA_PATH = ROOT_DIR / "Database" / "FGJ_CLEAN_Final.csv"
COLONIAS_GEOJSON_PATH = ROOT_DIR / "Geodata" / "colonias_iecm.geojson"
REGEX_CONFIG_PATH = ROOT_DIR / "EDA" / "regex_config.jam"

# Backwards-compatible alias for old imports
COLONIAS_GEOJSON = COLONIAS_GEOJSON_PATH

# ML assets
MODELS_DIR = ROOT_DIR / "ml" / "models"
DATA_ARTIFACTS_DIR = ROOT_DIR / "ml" / "data_artifacts"

# Static assets
IMAGES_DIR = ROOT_DIR / "images"

# Mapbox token (for local use; in deploy prefer st.secrets["MAPBOX_TOKEN"])
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "YOUR_DEFAULT_TOKEN")

# Model parameters (kept for potential use)
MODEL_PARAMS = {
    "random_forest": {"n_estimators": 200, "max_depth": 10},
    "xgboost": {"learning_rate": 0.1, "n_estimators": 300},
}

# UI defaults
DEFAULT_CITY = "CDMX"
DEFAULT_ROLE = "guest"
