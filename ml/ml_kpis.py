# ml/ml_kpis.py
from __future__ import annotations

from collections import OrderedDict
from typing import Dict

import pandas as pd

# Mapping: UI label → internal probability column
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
    """Return the list of Spanish labels for the UI selector."""
    return list(TIPO_MAP.keys())


def resolve_prob_column(tipo_label: str, df_map: pd.DataFrame) -> str:
    """Return the corresponding probability column or fallback to prob_total."""
    internal = TIPO_MAP.get(tipo_label)
    if internal is None or internal not in df_map.columns:
        return "prob_total"
    return internal


def compute_kpis(df_map: pd.DataFrame, prob_col: str) -> Dict[str, float]:
    """Compute KPI metrics given a probability column."""
    if prob_col not in df_map.columns:
        raise ValueError(f"Probability column '{prob_col}' not found in df_map")

    serie = df_map[prob_col].astype(float).clip(0, 1)
    total_colonias = int(len(df_map))
    mean_prob = float(serie.mean()) if total_colonias > 0 else 0.0
    max_prob = float(serie.max()) if total_colonias > 0 else 0.0

    # Risk counts
    if "risk_label" in df_map.columns:
        high_mask = df_map["risk_label"].isin(["Alto", "Muy alto"])
        high_risk_count = int(high_mask.sum())
    else:
        high_risk_count = 0

    high_risk_pct = (
        (high_risk_count / total_colonias * 100.0) if total_colonias > 0 else 0.0
    )

    # Top colonia by probability
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
