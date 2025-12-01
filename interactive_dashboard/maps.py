# interactive_dashboard/maps.py
"""
Motor de mapa geoespacial para el dashboard interactivo.

- Carga el GeoJSON de colonias CDMX.
- Normaliza nombres de colonia con reglas de tokens.
- Agrega conteos de incidentes por grupo lógico de colonia
  usando 'colonia_catalogo' en el dataset y 'NOMUT' en el GeoJSON.
- Soporta vistas predefinidas (CDMX general, zonas) y una vista
  basada en los filtros actuales.
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

# GeoJSON property names
GEOJSON_ALCALDIA_PROP = "NOMDT"
GEOJSON_COLONIA_PROP = "NOMUT"

# Regional views by alcaldía (used for centering and highlight)
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
    Normalize colonia name into a canonical key.
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
    Tokenize colonia name and drop structural tokens / Roman numerals.
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
    Build group key from colonia name (sorted tokens).
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

    Uses 'colonia_catalogo' from the dataset.
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
    Add incident counts to each feature using the group key.

    All polygons sharing the group key receive the same count.
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
        props["colonia_norm"] = group_key  # key for choropleth

        props["incidentes"] = int(count_dict.get(group_key, 0))

    return geojson_data


# ---------------------------------------------------------------------
# Bounding boxes and views
# ---------------------------------------------------------------------
def _iter_coords(geom: Dict[str, Any]):
    """
    Yield (lon, lat) pairs from a GeoJSON geometry.
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
    Compute bbox for a subset of features.

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
    Build predicate selecting features for current view.
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

    # CDMX general or unknown → all features
    return None


def _compute_view_center(
    geojson_data: Dict[str, Any],
    view_name: str,
) -> Tuple[List[float], int, Optional[Tuple[float, float, float, float]]]:
    """
    Determine map center, zoom, and bbox for selected view.
    """
    default_bbox = _bbox_for_features(geojson_data, None)
    if default_bbox is None:
        default_center = [19.4326, -99.1332]
        default_zoom = 11
    else:
        default_center = _center_from_bbox(default_bbox)
        default_zoom = 11

    pred = _view_feature_predicate(view_name)

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
    Build small table [colonia_norm, incidentes] for Choropleth.
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
    Build Folium map for current view.
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

    # Highlight features belonging to view with a red border
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
                    "fillColor": "rgba(255, 0, 0, 0.0)",
                    "color": "#FF3B30",
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
    High-level wrapper for pagina5: applies filters and renders map.
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
