### PROJECT VARIABLES

# config.py
import os

# Paths
DATA_PATH = "data/crime_data.csv"
SHAPE_PATH = "data/colonias_shapefile.shp"

# API tokens
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "YOUR_DEFAULT_TOKEN")

# Model parameters
MODEL_PARAMS = {
    "random_forest": {"n_estimators": 200, "max_depth": 10},
    "xgboost": {"learning_rate": 0.1, "n_estimators": 300},
}

# UI
DEFAULT_CITY = "CDMX"
DEFAULT_ROLE = "guest"