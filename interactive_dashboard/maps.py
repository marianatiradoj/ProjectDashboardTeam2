# interactive_dashboard/maps.py
"""
Geospatial map engine for the interactive crime dashboard.

This module:
- Loads the CDMX colonias GeoJSON.
- Normalizes colonia names using a token-based rule.
- Aggregates incident counts per logical colonia group using
  the 'colonia_catalogo' column in the dataset and the 'NOMUT'
  property in the GeoJSON.
- Supports preset map views (CDMX general, Centro, Norte, Sur,
  Oriente, Poniente, and an automatic view based on the current filters).
- Draws a bounding rectangle showing the current view window.
- Reports how many incidents are represented in the map vs. the
  total incidents in the filtered dataframe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Callable, Optional, Tuple

import json
import re
import unicodedata

import pandas as pd
import streamlit as st
import folium
from folium.plugins import MousePosition

# ---------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
COLONIAS_GEOJSON_PATH = BASE_DIR / "Geodata" / "colonias_iecm.geojson"

# Name of the property that contains the alcaldía in the GeoJSON
GEOJSON_ALCALDIA_PROP = "NOMDT"

# Name of the property that contains the colonia name in the GeoJSON
GEOJSON_COLONIA_PROP = "NOMUT"

# Regional views by alcaldía (used for center and highlight)
REGION_ALCALDIAS: Dict[str, List[str]] = {
    "Zona Centro": [
        "CUAUHTEMOC",
        "VENUSTIANO CARRANZA",
        "BENITO JUAREZ",
        "MIGUEL HIDALGO",
    ],
    "Zona Norte": [
        "GUSTAVO A. MADERO",
        "AZCAPOTZALCO",
    ],
    "Zona Sur": [
        "TLALPAN",
        "XOCHIMILCO",
        "COYOACAN",
        "ALVARO OBREGON",
        "MAGDALENA CONTRERAS",
    ],
    "Zona Oriente": [
        "IZTACALCO",
        "IZTAPALAPA",
    ],
    "Zona Poniente": [
        "CUAJIMALPA DE MORELOS",
        "MIGUEL HIDALGO",
        "ALVARO OBREGON",
    ],
}

# ---------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------


def _key_norm_str(x: Any) -> str:
    """
    Normalize a colonia name into a canonical key.

    Steps:
    - Convert to string.
    - Remove accents.
    - Replace non-alphanumeric characters with spaces.
    - Uppercase.
    - Collapse whitespace.
    """
    if not isinstance(x, str):
        x = "" if x is None else str(x)

    s = unicodedata.normalize("NFD", x)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    s = s.upper().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _tokens(s: Any) -> List[str]:
    """
    Convert a colonia name into a list of significant tokens.

    - Applies _key_norm_str.
    - Splits by spaces.
    - Expands common abbreviations (STA -> SANTA, SN -> SAN, STO -> SANTO).
    - Removes structural words and Roman numerals.
    """
    STOP = {
        "COL",
        "COLONIA",
        "AMPLIACION",
        "AMPLIACIÓN",
        "AMPL",
        "FRACC",
        "FRACCIONAMIENTO",
        "UH",
        "U",
        "H",
        "UNIDAD",
        "HABITACIONAL",
        "DE",
        "DEL",
        "LA",
        "EL",
        "LOS",
        "LAS",
        "SECC",
        "SECCION",
        "SECCIÓN",
        "BARR",
        "BARRIO",
        "PUEBLO",
        "PBLO",
        "LOC",
    }

    ROMAN = {
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "XII",
        "XIII",
        "XIV",
        "XV",
    }

    norm = _key_norm_str(s)
    raw_tokens = norm.split()

    expanded: List[str] = []
    for t in raw_tokens:
        if t == "STA":
            t = "SANTA"
        elif t == "SN":
            t = "SAN"
        elif t == "STO":
            t = "SANTO"
        expanded.append(t)

    return [
        t for t in expanded if t and len(t) > 2 and t not in STOP and t not in ROMAN
    ]


def _group_key(s: Any) -> str:
    """
    Build a group key from a colonia name.

    The group key is a sorted, space-joined list of meaningful tokens.
    Example:
        "CENTRO", "CENTRO II", "CENTRO III"  -> "CENTRO"
        "BARRIO SANTIAGO SUR", "SANTIAGO SUR (BARR)" -> "SANTIAGO SUR"
    """
    toks = _tokens(s)
    if not toks:
        return ""
    return " ".join(sorted(toks))


# ---------------------------------------------------------------------
# Load GeoJSON
# ---------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _load_geojson() -> Dict[str, Any]:
    """Load colonia polygons from GeoJSON."""
    with open(COLONIAS_GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------
# Aggregation by logical colonia group
# ---------------------------------------------------------------------


def _build_colonia_counts(df_filtered: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate incident counts per logical colonia group.

    Source column in dataset: 'colonia_catalogo'.

    Returns:
        DataFrame with columns:
            - group_key
            - incidentes
    """
    if df_filtered is None or df_filtered.empty:
        return pd.DataFrame(columns=["group_key", "incidentes"])

    if "colonia_catalogo" not in df_filtered.columns:
        return pd.DataFrame(columns=["group_key", "incidentes"])

    df = df_filtered.copy()
    df["group_key"] = df["colonia_catalogo"].astype("string").map(_group_key)

    counts = (
        df["group_key"]
        .value_counts()
        .rename_axis("group_key")
        .reset_index(name="incidentes")
    )
    return counts


def _attach_counts_to_geojson(
    geojson_data: Dict[str, Any],
    colonia_counts: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Attach incident counts to each feature in the GeoJSON using the
    token-based group key.

    All polygons whose names share the same group key will receive
    the same incident count (no distribution, only aggregation).
    """
    features = geojson_data.get("features", [])

    if colonia_counts is None or colonia_counts.empty:
        count_dict: Dict[str, int] = {}
    else:
        count_dict = dict(
            zip(
                colonia_counts["group_key"].astype(str),
                colonia_counts["incidentes"].astype(int),
            )
        )

    for feature in features:
        props = feature.setdefault("properties", {})
        raw_name = props.get(GEOJSON_COLONIA_PROP, "")

        group_key = _group_key(raw_name)
        props["colonia_label"] = raw_name  # human label
        props["colonia_group"] = group_key  # logical group
        props["colonia_norm"] = group_key  # key used by choropleth

        props["incidentes"] = int(count_dict.get(group_key, 0))

    return geojson_data


# ---------------------------------------------------------------------
# Bounding boxes and views
# ---------------------------------------------------------------------


def _iter_coords(geom: Dict[str, Any]):
    """
    Yield (lon, lat) pairs from a GeoJSON geometry.

    Supports Polygon and MultiPolygon types.
    """
    gtype = geom.get("type")
    coords = geom.get("coordinates", [])

    if gtype == "Polygon":
        for ring in coords:
            for lon, lat in ring:
                yield lon, lat
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                for lon, lat in ring:
                    yield lon, lat


def _bbox_for_features(
    geojson_data: Dict[str, Any],
    predicate: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> Optional[Tuple[float, float, float, float]]:
    """
    Compute bounding box for a subset of features.

    Returns (min_lat, max_lat, min_lon, max_lon).
    """
    features = geojson_data.get("features", [])
    if predicate is not None:
        features = [f for f in features if predicate(f)]

    min_lat = max_lat = min_lon = max_lon = None

    for feature in features:
        geom = feature.get("geometry", {})
        for lon, lat in _iter_coords(geom):
            if min_lat is None:
                min_lat = max_lat = lat
                min_lon = max_lon = lon
            else:
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)
                min_lon = min(min_lon, lon)
                max_lon = max(max_lon, lon)

    if min_lat is None:
        return None

    return (min_lat, max_lat, min_lon, max_lon)


def _center_from_bbox(bbox: Tuple[float, float, float, float]) -> List[float]:
    """Return [lat, lon] center from bbox."""
    min_lat, max_lat, min_lon, max_lon = bbox
    return [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]


def _view_feature_predicate(
    view_name: str,
) -> Optional[Callable[[Dict[str, Any]], bool]]:
    """
    Return a predicate that identifies which features belong to the
    selected view.

    - For "Vista según filtros": colonias with incidentes > 0.
    - For regional views: colonias whose alcaldía is in REGION_ALCALDIAS.
    - For "CDMX general" or unknown: None (all features are considered).
    """
    if view_name == "Vista según filtros":
        return lambda f: f.get("properties", {}).get("incidentes", 0) > 0

    if view_name in REGION_ALCALDIAS:
        targets = {a.upper() for a in REGION_ALCALDIAS[view_name]}

        def _pred_region(f: Dict[str, Any]) -> bool:
            props = f.get("properties", {})
            alcaldia = props.get(GEOJSON_ALCALDIA_PROP, "")
            alcaldia_norm = _key_norm_str(alcaldia)
            return alcaldia_norm in targets

        return _pred_region

    # CDMX general or unknown → no special subset
    return None


def _compute_view_center(
    geojson_data: Dict[str, Any],
    view_name: str,
) -> Tuple[List[float], int, Optional[Tuple[float, float, float, float]]]:
    """
    Determine map center, zoom, and bbox for the selected view.

    Views:
    - "Vista según filtros": bbox over features with incidentes > 0.
    - "CDMX general": bbox over all features.
    - Regional views: bbox over features whose alcaldía is in REGION_ALCALDIAS.
    """
    default_bbox = _bbox_for_features(geojson_data, None)
    if default_bbox is None:
        default_center = [19.4326, -99.1332]
        default_zoom = 11
    else:
        default_center = _center_from_bbox(default_bbox)
        default_zoom = 11

    # Predicate describing which features belong to this view
    pred = _view_feature_predicate(view_name)

    # CDMX general (no predicate) → use all features
    if pred is None and view_name != "Vista según filtros":
        bbox = default_bbox
    else:
        bbox = _bbox_for_features(geojson_data, pred)

    if bbox is None:
        return default_center, default_zoom, default_bbox

    zoom = 12 if view_name != "CDMX general" else 11
    return _center_from_bbox(bbox), zoom, bbox


# ---------------------------------------------------------------------
# Choropleth data table
# ---------------------------------------------------------------------


def _extract_choropleth_table(geojson_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Build a small table [colonia_norm, incidentes] for Folium.Choropleth.
    """
    rows = []
    for feature in geojson_data.get("features", []):
        props = feature.get("properties", {})
        key = props.get("colonia_norm")
        incidentes = props.get("incidentes", 0)
        if key:
            rows.append({"colonia_norm": key, "incidentes": incidentes})

    if not rows:
        return pd.DataFrame(columns=["colonia_norm", "incidentes"])

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["colonia_norm"])
    return df


# ---------------------------------------------------------------------
# Folium map builder
# ---------------------------------------------------------------------


def _build_folium_map(
    geojson_data: Dict[str, Any],
    view_name: str,
) -> folium.Map:
    """
    Build a Folium map for the given view.

    - Center and zoom are derived from _compute_view_center.
    - Choropleth uses colonia_norm as key.
    - Colonias that belong to the selected view are highlighted with
      a red border, following their exact polygon limits.
    """
    center, zoom, _bbox = _compute_view_center(geojson_data, view_name)

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    MousePosition().add_to(m)

    # Base choropleth
    folium.Choropleth(
        geo_data=geojson_data,
        data=_extract_choropleth_table(geojson_data),
        columns=["colonia_norm", "incidentes"],
        key_on="feature.properties.colonia_norm",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.4,
        nan_fill_color="#333333",
        highlight=True,
        legend_name="Número de incidentes",
    ).add_to(m)

    # Base GeoJson with tooltip
    folium.GeoJson(
        geojson_data,
        name="Colonias",
        tooltip=folium.GeoJsonTooltip(
            fields=["colonia_label", "incidentes"],
            aliases=["Colonia", "Incidentes"],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    # Highlight colonias belonging to the current view using a red border
    pred = _view_feature_predicate(view_name)
    if pred is not None:
        selected_features = [f for f in geojson_data.get("features", []) if pred(f)]

        if selected_features:
            highlight_collection = {
                "type": "FeatureCollection",
                "features": selected_features,
            }

            folium.GeoJson(
                highlight_collection,
                name="Zona seleccionada",
                style_function=lambda feature: {
                    "fillColor": "rgba(255, 0, 0, 0.0)",  # no fill, keep choropleth visible
                    "color": "#FF3B30",  # red border
                    "weight": 3,
                    "fillOpacity": 0.0,
                },
            ).add_to(m)

    return m


# ---------------------------------------------------------------------
# Public entrypoint for pagina5
# ---------------------------------------------------------------------


def render_map_section(df_filtered: pd.DataFrame) -> None:
    """
    High-level wrapper used in pagina5.

    - Respects all filters (df_filtered is already filtered).
    - Allows the user to select a map view.
    - Shows a KPI of incidents represented vs total filtered.
    - Renders the Folium map inside Streamlit.
    """
    st.subheader("Mapa interactivo de incidencia por colonia")

    if df_filtered is None or df_filtered.empty:
        st.info(
            "No hay registros para el conjunto actual de filtros. "
            "Ajusta los criterios para visualizar el mapa."
        )
        return

    view_name = st.selectbox(
        "Vista del mapa",
        [
            "Vista según filtros",
            "CDMX general",
            "Zona Centro",
            "Zona Norte",
            "Zona Sur",
            "Zona Oriente",
            "Zona Poniente",
        ],
        index=0,
    )

    with st.spinner("Generando mapa geoespacial…"):
        geojson_data = _load_geojson()
        colonia_counts = _build_colonia_counts(df_filtered)
        enriched_geojson = _attach_counts_to_geojson(geojson_data, colonia_counts)
        m = _build_folium_map(enriched_geojson, view_name)

        # KPI: incidents in filtered df vs incidents represented in the map
        total_filtrados = int(len(df_filtered))

        if colonia_counts is not None and not colonia_counts.empty:
            keys_in_polygons = {
                feature.get("properties", {}).get("colonia_norm", "")
                for feature in enriched_geojson.get("features", [])
            }
            mapped_counts = colonia_counts[
                colonia_counts["group_key"].isin(keys_in_polygons)
            ]
            total_mapa = int(mapped_counts["incidentes"].sum())
        else:
            total_mapa = 0

        cobertura = (total_mapa / total_filtrados) if total_filtrados > 0 else 0.0

        st.caption(
            f"Incidentes filtrados totales: {total_filtrados:,.0f} — "
            f"Incidentes representados en el mapa: {total_mapa:,.0f} "
            f"({cobertura:0.1%} de cobertura geoespacial)."
        )

        st.components.v1.html(
            m._repr_html_(),
            height=600,
            scrolling=False,
        )
