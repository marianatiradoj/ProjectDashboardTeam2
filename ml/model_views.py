# ml/model_views.py
"""
Helpers de alto nivel para Streamlit.

- Usa CrimeModelBundle + predict_for_datetime
- Devuelve:
  - df_pred: dataframe completo de predicción
  - df_table: vista amigable para tabla
  - df_map: vista lista para pydeck (lat, lon, prob_total, risk_label,
            colores RGB, colonia y prob_tipo_*)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .ml_analysis import CrimeModelBundle, predict_for_datetime


@dataclass
class PredictionOutputs:
    df_pred: pd.DataFrame
    df_table: pd.DataFrame
    df_map: Optional[pd.DataFrame]
    alcaldia_col: Optional[str]
    colonia_col: Optional[str]


def _detect_alcaldia_col(df: pd.DataFrame) -> Optional[str]:
    candidates = ["alcaldia", "ALCALDIA", "alcaldia_hecho", "alcaldia_nombre"]
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _detect_colonia_col(df: pd.DataFrame) -> Optional[str]:
    candidates = [
        "colonia_catalogo",
        "colonia",
        "COLONIA",
        "nom_colonia",
        "NOM_COLONIA",
    ]
    for c in candidates:
        if c in df.columns:
            return c
    return None


def compute_predictions_for_dt(
    dt: datetime,
    bundle: CrimeModelBundle,
    alcaldias_sel: Optional[list[str]] = None,
) -> PredictionOutputs:
    # 1) Inferencia cruda
    df_pred = predict_for_datetime(dt, bundle)

    # 2) Detectar columnas de alcaldía/colonia
    alcaldia_col = _detect_alcaldia_col(df_pred)
    colonia_col = _detect_colonia_col(df_pred)

    # 3) Filtro por alcaldía (si aplica)
    if alcaldia_col and alcaldias_sel:
        df_pred = df_pred[df_pred[alcaldia_col].astype(str).isin(alcaldias_sel)]

    # 4) Orden y etiqueta de riesgo
    if "prob_total" in df_pred.columns:
        df_pred = df_pred.sort_values("prob_total", ascending=False)

        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0001]
        labels = ["Muy bajo", "Bajo", "Medio", "Alto", "Muy alto"]
        df_pred["risk_label"] = pd.cut(
            df_pred["prob_total"].clip(0, 1),
            bins=bins,
            labels=labels,
            include_lowest=True,
        )
    else:
        df_pred["risk_label"] = None

    # 5) Tabla amigable
    cols: List[str] = []
    if colonia_col:
        cols.append(colonia_col)
    if alcaldia_col:
        cols.append(alcaldia_col)
    for c in ["prob_total", "risk_label", "centroid_lat", "centroid_lon"]:
        if c in df_pred.columns:
            cols.append(c)
    cols = list(dict.fromkeys(cols))

    df_table = df_pred[cols].copy() if cols else df_pred.copy()

    # 6) Dataframe para mapa (incluyendo prob_tipo_*)
    lat_col = "centroid_lat"
    lon_col = "centroid_lon"

    if (
        lat_col in df_pred.columns
        and lon_col in df_pred.columns
        and "prob_total" in df_pred.columns
    ):
        # columnas base para el mapa
        map_cols = [lat_col, lon_col, "prob_total", "risk_label"]

        # agregar todas las columnas prob_tipo_*
        prob_tipo_cols = [c for c in df_pred.columns if c.startswith("prob_tipo_")]
        map_cols.extend(prob_tipo_cols)

        # colonia / alcaldía (aunque ya no usaremos alcaldía en el tooltip,
        # la dejamos disponible por si se requiere luego)
        if colonia_col:
            map_cols.append(colonia_col)
        if alcaldia_col:
            map_cols.append(alcaldia_col)

        map_cols = list(dict.fromkeys(map_cols))

        df_map = df_pred[map_cols].copy()

        rename_dict = {lat_col: "lat", lon_col: "lon"}
        if colonia_col and colonia_col in df_map.columns:
            rename_dict[colonia_col] = "colonia"
        if alcaldia_col and alcaldia_col in df_map.columns:
            rename_dict[alcaldia_col] = "alcaldia"

        df_map = df_map.rename(columns=rename_dict)

        # Colores RGB por nivel de riesgo
        color_map = {
            "Muy bajo": (56, 168, 0),
            "Bajo": (139, 209, 0),
            "Medio": (255, 255, 0),
            "Alto": (255, 140, 0),
            "Muy alto": (255, 0, 0),
        }

        def _get_rgb(label):
            if label is None or (isinstance(label, float) and pd.isna(label)):
                return (200, 200, 200)
            return color_map.get(str(label), (200, 200, 200))

        rgb_series = df_map["risk_label"].astype(object).apply(_get_rgb)
        df_map["color_r"] = rgb_series.apply(lambda t: t[0])
        df_map["color_g"] = rgb_series.apply(lambda t: t[1])
        df_map["color_b"] = rgb_series.apply(lambda t: t[2])
    else:
        df_map = None

    return PredictionOutputs(
        df_pred=df_pred,
        df_table=df_table,
        df_map=df_map,
        alcaldia_col=alcaldia_col,
        colonia_col=colonia_col,
    )
