# ml/ml_kpis.py
from __future__ import annotations

from collections import OrderedDict
from typing import Dict

import pandas as pd

# Mapeo: etiqueta en español -> nombre de columna interna
TIPO_MAP = OrderedDict(
    [
        ("Total (todos los delitos)", None),
        ("Administrativo", "prob_tipo_NON_CRIME_OTHER"),
        ("Bajo Impacto", "prob_tipo_LOW_IMPACT"),
        ("Robo Persona", "prob_tipo_ROBBERY_PERSON"),
        ("Robo Propiedad", "prob_tipo_ROBBERY_PROPERTY"),
        ("Violencia Letal", "prob_tipo_LETHAL_VIOLENT"),
        ("Violencia No Letal", "prob_tipo_VIOLENT_OTHER"),
    ]
)


def get_tipo_options():
    """
    Devuelve la lista de etiquetas en español para usar en el selectbox.
    """
    return list(TIPO_MAP.keys())


def resolve_prob_column(tipo_label: str, df_map: pd.DataFrame) -> str:
    """
    A partir de la etiqueta en español, devuelve el nombre de columna interna
    que se usará para el tamaño del círculo y KPIs.

    Si no existe en df_map, usa 'prob_total'.
    """
    internal = TIPO_MAP.get(tipo_label)
    if internal is None or internal not in df_map.columns:
        return "prob_total"
    return internal


def compute_kpis(df_map: pd.DataFrame, prob_col: str) -> Dict[str, float]:
    """
    Calcula KPIs básicos a partir de df_map y la columna de probabilidad elegida.
    Devuelve un diccionario con:
        - total_colonias
        - mean_prob
        - max_prob
        - high_risk_count
        - high_risk_pct
        - top_colonia
    """
    if prob_col not in df_map.columns:
        raise ValueError(f"La columna de probabilidad '{prob_col}' no existe en df_map")

    serie = df_map[prob_col].astype(float).clip(0, 1)
    total_colonias = int(len(df_map))
    mean_prob = float(serie.mean()) if total_colonias > 0 else 0.0
    max_prob = float(serie.max()) if total_colonias > 0 else 0.0

    # Colonias en riesgo ALTO o MUY ALTO
    if "risk_label" in df_map.columns:
        high_mask = df_map["risk_label"].isin(["Alto", "Muy alto"])
        high_risk_count = int(high_mask.sum())
    else:
        high_risk_count = 0

    high_risk_pct = (
        (high_risk_count / total_colonias * 100.0) if total_colonias > 0 else 0.0
    )

    # Colonia con mayor probabilidad para ese tipo
    try:
        idxmax = serie.idxmax()
        row = df_map.loc[idxmax]
        top_colonia = str(row.get("colonia", "N/D"))
    except Exception:
        top_colonia = "N/D"

    return {
        "total_colonias": total_colonias,
        "mean_prob": mean_prob,
        "max_prob": max_prob,
        "high_risk_count": high_risk_count,
        "high_risk_pct": high_risk_pct,
        "top_colonia": top_colonia,
    }
