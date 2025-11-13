# EDA/eda_pipeline.py
from __future__ import annotations
from typing import Dict, Tuple
import pandas as pd
import matplotlib.pyplot as plt

from .user_eda import (
    cross_fill_colonias,
    fill_competencia,
    classify_regex,
    add_weekday_features,
    add_quincena_window,
    fill_latlng_medians,
    add_weather_by_alcaldia_fecha,
)


def _macrogroup_bar(macrogroup_pct: Dict[str, float]):
    df_plot = (
        pd.DataFrame(list(macrogroup_pct.items()), columns=["Macrogrupo", "Porcentaje"])
        .sort_values("Porcentaje", ascending=False)
        .set_index("Macrogrupo")
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    df_plot.plot(kind="bar", legend=False, ax=ax)
    ax.set_ylabel("% del total")
    ax.set_title("Distribución de delitos por macrogrupo")
    fig.tight_layout()
    return fig


def run_eda(
    df: pd.DataFrame, cfg: Dict | None = None
) -> Tuple[pd.DataFrame, Dict, Dict]:
    cfg = cfg or {}
    date_col = cfg.get("date_col", "fecha_hecho")
    alcaldia_col = cfg.get("alcaldia_col", "alcaldia_hecho")
    quincena_days = int(cfg.get("quincena_window", 2))
    with_weather = bool(cfg.get("with_weather", False))
    weather_path = cfg.get("weather_path", "")
    regex_path = cfg.get("regex_path", None)

    stats, figs, tables = {}, {}, {}
    out = df.copy()

    # 1) Colonias
    out, stats["colonias"] = cross_fill_colonias(
        out, "colonia_hecho", "colonia_catalogo"
    )

    # 2) Competencia
    out, stats["competencia"] = fill_competencia(
        out, competencia_col="competencia", alcaldia_col=alcaldia_col
    )

    # 3) Clasificación regex (SOLO una vez)
    out, stats["clasificacion"] = classify_regex(
        out,
        delito_col="delito",
        grupo_col="delito_grupo",
        violencia_col="violencia_class",
        pasajero_col="robo_pasajero",
        regex_path=regex_path,
    )

    # 4) Calendario
    out = add_weekday_features(
        out, date_col=date_col, name_col="weekday", num_col="weekday_num"
    )
    out = add_quincena_window(
        out,
        date_col=date_col,
        window_days=quincena_days,
        out_col="quincena_window",
        in_label="WINDOW",
        out_label="NO_WINDOW",
    )

    # 5) Lat/Lng
    out, stats["latlng"] = fill_latlng_medians(out)

    # 6) Clima (opcional)
    if with_weather and weather_path:
        out, stats["clima"] = add_weather_by_alcaldia_fecha(
            out,
            clima_csv_path=weather_path,
            alcaldia_col=alcaldia_col,
            date_col=date_col,
            out_temp="clima_temp",
            out_cond="clima_conditions",
        )
        cond = (
            out["clima_conditions"]
            .astype("string")
            .str.replace(",", "", regex=False)
            .str.strip()
            .str.lower()
        )
        out["clima_bucket"] = cond.map(
            lambda x: (
                "Rain"
                if isinstance(x, str) and "rain" in x
                else (
                    "Sunny"
                    if isinstance(x, str)
                    and any(k in x for k in ["sun", "clear", "partly"])
                    else None
                )
            )
        )

    # 7) Tablas (útiles en UI)
    if {"delito_grupo_macro", "delito_grupo"}.issubset(out.columns):
        tables["macro_vs_grupo"] = pd.crosstab(
            out["delito_grupo_macro"], out["delito_grupo"]
        )
    if {"delito_grupo", "violencia_class"}.issubset(out.columns):
        tables["grupo_vs_violencia"] = pd.crosstab(
            out["delito_grupo"], out["violencia_class"]
        )
    if {"delito_grupo", "robo_pasajero"}.issubset(out.columns):
        tables["grupo_vs_pasajero"] = pd.crosstab(
            out["delito_grupo"], out["robo_pasajero"]
        )

    # 8) Figura principal
    figs["macrogroup_bar"] = _macrogroup_bar(stats["clasificacion"]["macrogroup_pct"])

    artifacts = {"figs": figs, "tables": tables}
    return out, stats, artifacts
