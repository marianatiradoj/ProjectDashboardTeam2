# eda_pipeline.py
# Orquesta el EDA completo. Pensado para usarse desde Streamlit.

from pathlib import Path
from typing import Tuple, Dict, Optional

import pandas as pd

from .update_base import (
    robust_read_csv,
    report_missing_values,
    report_duplicates_full,
    cross_fill_colonias,
    fill_competencia,
    fill_latlng_medians,
    preview_drop_sparse,
    add_weekday_features,
    add_quincena_window,
    add_weather_by_alcaldia_fecha,
    asignar_region,
    mes_a_espanol,
    clasificar_hora,
)
from .regex_loader import classify_regex


# ------------------------------------------------------------
# Función principal para Streamlit (recibe DataFrame subido)
# ------------------------------------------------------------


def run_eda_for_upload(
    df_raw: pd.DataFrame,
    clima_csv_path: Optional[str] = None,
    regex_config_path: str = "regex_config.jam",
) -> Tuple[pd.DataFrame, Dict]:
    """
    Ejecuta TODO el EDA sobre un DataFrame nuevo (por ejemplo, subido en Streamlit).

    Parámetros
    ----------
    df_raw : pd.DataFrame
        Datos crudos del nuevo lote.
    clima_csv_path : str | None
        Ruta al CSV de clima (si es None, NO se enriquece con clima).
    regex_config_path : str
        Ruta al archivo regex_config.jam con todos los patrones.

    Retorna
    -------
    df : pd.DataFrame
        Datos limpios / enriquecidos del lote.
    stats_global : dict
        Diccionario con métricas y auditoría del EDA.
    """

    stats_global: Dict = {}

    # Copia para no modificar el original
    df = df_raw.copy()

    # --------------------------------------------------------
    # Diagnóstico inicial
    # --------------------------------------------------------
    stats_global["shape_inicial"] = df.shape
    stats_global["mem_mb_inicial"] = round(
        df.memory_usage(deep=True).sum() / (1024**2), 2
    )
    stats_global["missing_top20"] = report_missing_values(df).head(20)
    stats_global["duplicates_full"] = report_duplicates_full(df)

    # --------------------------------------------------------
    # Cross-fill colonias
    # --------------------------------------------------------
    df, s_col = cross_fill_colonias(df, "colonia_hecho", "colonia_catalogo")
    stats_global["cross_fill_colonias"] = s_col

    # --------------------------------------------------------
    # Imputación competencia
    # --------------------------------------------------------
    df, s_comp = fill_competencia(df)
    stats_global["fill_competencia"] = s_comp

    # --------------------------------------------------------
    # Clasificación por regex (usa regex_config.jam)
    # --------------------------------------------------------
    df, s_regex = classify_regex(
        df,
        delito_col="delito",
        grupo_col="delito_grupo",
        violencia_col="clase_violencia",
        pasajero_col="robo_pasajero",
        regex_config_path=regex_config_path,
    )
    stats_global["regex"] = s_regex

    # --------------------------------------------------------
    # Features de calendario (día de la semana, quincena)
    # --------------------------------------------------------
    if "fecha_hecho" in df.columns:
        df = add_weekday_features(
            df,
            date_col="fecha_hecho",
            name_col="dia_hecho",
            num_col="dia_hecho_num",
        )
        df = add_quincena_window(
            df,
            date_col="fecha_hecho",
            window_days=2,
            out_col="quincena_window",
            in_label="Ventana",
            out_label="No_ventana",
        )

    # --------------------------------------------------------
    # Imputación lat/long por medianas
    # --------------------------------------------------------
    df, s_latlng = fill_latlng_medians(df)
    stats_global["latlng"] = s_latlng

    # --------------------------------------------------------
    # CLIMA (solo si se pasó clima_csv_path != None)
    # --------------------------------------------------------
    if clima_csv_path:
        df, s_clima = add_weather_by_alcaldia_fecha(
            df,
            clima_csv_path=clima_csv_path,
            alcaldia_col="alcaldia_hecho",
            date_col="fecha_hecho",
        )
    else:
        # Si no hay clima, sólo registramos que no se enriqueció
        s_clima = {
            "weather_enriched": False,
            "registros_con_clima": 0,
            "registros_sin_clima": len(df),
        }
    stats_global["clima"] = s_clima

    # Normalizar clima_condicion → Soleado / Lluvia (si existe)
    if "clima_condicion" in df.columns:
        df["clima_condicion"] = (
            df["clima_condicion"]
            .astype("string")
            .str.replace(",", "", regex=False)
            .str.strip()
            .str.lower()
        )

        def _map_weather(x: Optional[str]) -> Optional[str]:
            if x is None or pd.isna(x):
                return None
            if "rain" in x or "snow" in x:
                return "Lluvia"
            if "clear" in x or "overcast" in x or "partly" in x or "partial" in x:
                return "Soleado"
            return None

        df["clima_condicion"] = df["clima_condicion"].map(_map_weather)

    # --------------------------------------------------------
    # Región CDMX
    # --------------------------------------------------------
    if "alcaldia_hecho" in df.columns:
        df["region_cdmx"] = df["alcaldia_hecho"].map(asignar_region)

    # --------------------------------------------------------
    # Meses a español
    # --------------------------------------------------------
    if "mes_inicio" in df.columns:
        df["mes_inicio"] = df["mes_inicio"].map(mes_a_espanol)
    if "mes_hecho" in df.columns:
        df["mes_hecho"] = df["mes_hecho"].map(mes_a_espanol)

    # --------------------------------------------------------
    # Hora → periodo del día
    # --------------------------------------------------------
    if "hora_hecho" in df.columns:
        df["hora_hecho"] = pd.to_datetime(
            df["hora_hecho"],
            format="%H:%M:%S",
            errors="coerce",
        ).dt.time
        df["periodo_hora"] = df["hora_hecho"].apply(clasificar_hora)

    # --------------------------------------------------------
    # Drop columnas poco útiles / redundantes
    # --------------------------------------------------------
    df, sparse_info = preview_drop_sparse(df, col="alcaldia_catalogo", threshold=0.95)
    stats_global["alcaldia_catalogo_sparse"] = sparse_info

    # Ya no necesitamos algunas columnas
    df.drop(columns=["alcaldia_catalogo"], errors="ignore", inplace=True)
    df.drop(columns=["hora_inicio", "violencia_class"], errors="ignore", inplace=True)
    df.drop(columns=["robo_pasajero"], errors="ignore", inplace=True)

    # --------------------------------------------------------
    # Deduplicación exacta
    # --------------------------------------------------------
    dups_before = int(df.duplicated(keep=False).sum())
    if dups_before > 0:
        rows_before = len(df)
        df = df.drop_duplicates(keep="first").reset_index(drop=True)
        rows_after = len(df)
        stats_global["deduplicacion"] = {
            "rows_before": rows_before,
            "rows_after": rows_after,
            "dropped_exact_dups": rows_before - rows_after,
            "dups_after": int(df.duplicated(keep=False).sum()),
        }
    else:
        stats_global["deduplicacion"] = {
            "rows_before": len(df),
            "rows_after": len(df),
            "dropped_exact_dups": 0,
            "dups_after": 0,
        }

    stats_global["shape_final"] = df.shape
    stats_global["mem_mb_final"] = round(
        df.memory_usage(deep=True).sum() / (1024**2), 2
    )

    return df, stats_global


# ------------------------------------------------------------
# Helper opcional: pegar a base existente (NO se usa en Streamlit aún)
# ------------------------------------------------------------


def append_to_base_csv(
    new_clean_df: pd.DataFrame,
    base_clean_csv_path: str,
    output_path: Optional[str] = None,
) -> Dict:
    """
    Toma un df ya procesado por run_eda_for_upload y lo agrega a la base limpia.
    Si output_path es None, sobreescribe base_clean_csv_path.

    Retorna un dict con conteos:
      - n_before
      - n_new
      - n_total
    """
    base_df = robust_read_csv(base_clean_csv_path)
    n_before = len(base_df)
    n_new = len(new_clean_df)

    combined = pd.concat([base_df, new_clean_df], ignore_index=True)
    n_total = len(combined)

    out_path = Path(output_path or base_clean_csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False)

    return {
        "base_path": str(base_clean_csv_path),
        "output_path": str(out_path),
        "n_before": n_before,
        "n_new": n_new,
        "n_total": n_total,
    }
