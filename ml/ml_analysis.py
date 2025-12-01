# ml/ml_analysis.py
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from xgboost import XGBClassifier

from .feature_engineering import build_inference_frame


# Relative paths for ML artifacts
ML_DIR = Path(__file__).resolve().parent
MODELS_DIR = ML_DIR / "models"
DATA_DIR = ML_DIR / "data_artifacts"


@dataclass
class CrimeModelBundle:
    """Container for trained models and metadata."""

    model_total: XGBClassifier
    models_tipo: Dict[str, XGBClassifier]
    features_total: List[str]
    tipo_cols: List[str]
    colonias_base: pd.DataFrame


def _load_metadata() -> Tuple[List[str], List[str]]:
    """
    Load model metadata: feature list and tipo columns.
    """
    meta_path = DATA_DIR / "model_v4_2_metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found at {meta_path}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    features_total = meta["features_total"]
    tipo_cols = meta["tipo_cols"]
    return features_total, tipo_cols


def _load_colonias_base() -> pd.DataFrame:
    """
    Load base colonias table from parquet or CSV.
    """
    parquet_path = DATA_DIR / "colonias_base.parquet"
    csv_path = DATA_DIR / "colonias_base.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(
            f"Could not find colonias_base.parquet or colonias_base.csv in {DATA_DIR}"
        )
    return df


def _load_models(
    tipo_cols: List[str],
) -> Tuple[XGBClassifier, Dict[str, XGBClassifier]]:
    """
    Load main model and per-tipo models from disk.
    """
    model_total_path = MODELS_DIR / "model_total_xgb.json"
    if not model_total_path.exists():
        raise FileNotFoundError(f"Main model file not found at {model_total_path}")

    model_total = XGBClassifier()
    model_total.load_model(str(model_total_path))

    models_tipo: Dict[str, XGBClassifier] = {}
    for col in tipo_cols:
        suf = col.replace("count_tipo_", "")
        path = MODELS_DIR / f"model_tipo_{suf}.json"
        if path.exists():
            m = XGBClassifier()
            m.load_model(str(path))
            models_tipo[col] = m
        else:
            print(f"[WARN] Missing per-type model for {col} at {path}")

    return model_total, models_tipo


def load_bundle() -> CrimeModelBundle:
    """
    Load all model artifacts and metadata required for inference.
    """
    features_total, tipo_cols = _load_metadata()
    colonias_base = _load_colonias_base()
    model_total, models_tipo = _load_models(tipo_cols)

    return CrimeModelBundle(
        model_total=model_total,
        models_tipo=models_tipo,
        features_total=features_total,
        tipo_cols=tipo_cols,
        colonias_base=colonias_base,
    )


def predict_for_datetime(
    dt: datetime | str,
    bundle: Optional[CrimeModelBundle] = None,
) -> pd.DataFrame:
    """
    Run prediction for a given datetime over all colonias and return probabilities.
    """
    if bundle is None:
        bundle = load_bundle()

    df_inf = build_inference_frame(dt, bundle.colonias_base)

    missing = [f for f in bundle.features_total if f not in df_inf.columns]
    if missing:
        raise ValueError(f"Missing features in inference frame: {missing}")

    X = df_inf[bundle.features_total]

    # Global probability
    df_inf["prob_total"] = bundle.model_total.predict_proba(X)[:, 1].clip(0, 1)

    # Per-type probabilities
    for col_tipo, model_t in bundle.models_tipo.items():
        suf = col_tipo.replace("count_tipo_", "")
        col_prob = f"prob_tipo_{suf}"
        df_inf[col_prob] = model_t.predict_proba(X)[:, 1].clip(0, 1)

    return df_inf
