# interactive_dashboard/maps.py
#
# This module provides all map-related functionality for the interactive
# crime dashboard. It loads polygon geometries for Mexico City colonias,
# joins them with filtered crime data, and generates an interactive
# choropleth map using Folium.
#
# All functions are written to be modular and reusable inside pagina5.py.

from __future__ import annotations

import geopandas as gpd
import pandas as pd
import streamlit as st
import folium
from folium.plugins import MousePosition
from typing import Optional


# ---------------------------------------------------------------------
# Load colonias polygons
# ---------------------------------------------------------------------
def load_colonias_geometries(path: str) -> gpd.GeoDataFrame:
    """
    Load Mexico City colonias polygons from a shapefile.

    Args:
        path (str): Path to the main .shp file.

    Returns:
        GeoDataFrame: Geospatial dataframe containing colonia polygons.
    """
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)  # normalize to WGS84
    gdf["colonia_norm"] = gdf["NOM_COL"].astype(str).str.strip().str.upper()
    return gdf


# ---------------------------------------------------------------------
# Prepare data for thematic mapping
# ---------------------------------------------------------------------
def prepare_choropleth_data(
    df_filtered: pd.DataFrame,
    gdf_colonias: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Join filtered crime data with colonia polygons.

    Args:
        df_filtered (pd.DataFrame): Crime data after user filters.
        gdf_colonias (GeoDataFrame): Colonias polygons.

    Returns:
        GeoDataFrame: Merged dataset ready for folium mapping.
    """
    if df_filtered.empty:
        # Return polygons but with zero counts
        gdf_colonias["incidentes"] = 0
        return gdf_colonias

    # Normalize colonia column in crime dataset
    df_aux = df_filtered.copy()
    df_aux["colonia_norm"] = df_aux["colonia_hecho"].astype(str).str.strip().str.upper()

    # Compute incident count per colonia
    counts = df_aux.groupby("colonia_norm").size().reset_index(name="incidentes")

    # Merge with polygons
    merged = gdf_colonias.merge(counts, on="colonia_norm", how="left")
    merged["incidentes"] = merged["incidentes"].fillna(0).astype(int)

    return merged


# ---------------------------------------------------------------------
# Build Folium map (interactive)
# ---------------------------------------------------------------------
def render_folium_map(
    gdf: gpd.GeoDataFrame,
    map_height: int = 580,
) -> None:
    """
    Render a Folium choropleth map inside Streamlit.

    Args:
        gdf (GeoDataFrame): Geographic data with incident counts.
        map_height (int): Display height inside Streamlit.
    """
    # Compute map center
    centroid = gdf.geometry.unary_union.centroid
    map_center = [centroid.y, centroid.x]

    # Create map
    m = folium.Map(location=map_center, zoom_start=11, tiles="cartodbpositron")

    # Add mouse coordinates tool
    MousePosition().add_to(m)

    # Choropleth layer
    folium.Choropleth(
        geo_data=gdf.to_json(),
        data=gdf,
        columns=["colonia_norm", "incidentes"],
        key_on="feature.properties.colonia_norm",
        fill_color="YlOrRd",
        fill_opacity=0.75,
        line_opacity=0.4,
        nan_fill_color="#cccccc",
        highlight=True,
        legend_name="Número de incidentes",
    ).add_to(m)

    # Add colonia labels on hover
    folium.GeoJson(
        gdf,
        name="Colonias",
        tooltip=folium.GeoJsonTooltip(
            fields=["colonia_norm", "incidentes"],
            aliases=["Colonia", "Incidentes"],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    # Display map in Streamlit
    st.components.v1.html(m._repr_html_(), height=map_height, scrolling=False)


# ---------------------------------------------------------------------
# High-level wrapper (used in pagina5)
# ---------------------------------------------------------------------
def render_map_section(
    df_filtered: pd.DataFrame,
    colonias_path: str,
) -> None:
    """
    High-level wrapper combining data loading, merging and map rendering.

    Args:
        df_filtered (pd.DataFrame): Dataset with filters applied.
        colonias_path (str): Path to colonias shapefile.
    """

    st.markdown("## Mapa interactivo de incidencia por colonia")

    with st.spinner("Cargando mapa geográfico..."):
        gdf_colonias = load_colonias_geometries(colonias_path)
        gdf_map = prepare_choropleth_data(df_filtered, gdf_colonias)
        render_folium_map(gdf_map)
