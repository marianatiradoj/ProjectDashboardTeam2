# EDA/update_base.py
# General utilities for the EDA pipeline (IO, dates, weather, regions, etc.)

import re
import unicodedata
from typing import Dict, Tuple

import pandas as pd


# IO and diagnostics
def robust_read_csv(
    path: str, try_encodings=("utf-8", "latin-1", "cp1252"), **kwargs
) -> pd.DataFrame:
    """
    Read a CSV trying multiple encodings and raise a clear error if all fail.
    """
    last_err = None
    if "encoding" in kwargs:
        kwargs = {k: v for k, v in kwargs.items() if k != "encoding"}

    for enc in try_encodings:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except Exception as e:
            last_err = e

    raise RuntimeError(f"Could not read {path}. Last error: {last_err}")


def report_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return absolute and percentage missing values per column, sorted descending.
    """
    counts = df.isna().sum().astype(int)
    pct = (counts / len(df) * 100) if len(df) else 0.0
    return pd.DataFrame({"missing": counts, "missing_%": pct}).sort_values(
        "missing_%", ascending=False
    )


def report_duplicates_full(df: pd.DataFrame) -> Dict[str, int]:
    """
    Count exact duplicate rows across all columns.
    """
    return {"duplicate_rows_full": int(df.duplicated(keep=False).sum())}


# Text normalization
def _strip_accents(s: str) -> str:
    """Remove accents from a string."""
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", str(s))
        if unicodedata.category(ch) != "Mn"
    )


def norm_series(s: pd.Series) -> pd.Series:
    """
    Normalize text to uppercase, trim spaces, collapse whitespace and remove accents.
    """
    s = s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    s = s.map(_strip_accents).str.upper()
    return s.astype("string")


# Cross-fill colonias (strict 1→1 mapping)
def _strict_map(df: pd.DataFrame, src: str, tgt: str) -> Tuple[Dict[str, str], int]:
    """
    Build a src→tgt map only for sources that map to exactly one target.
    """
    sub = df[[src, tgt]].dropna().copy()
    if sub.empty:
        return {}, 0

    sub["src_norm"] = norm_series(sub[src])
    sub["tgt_norm"] = norm_series(sub[tgt])

    distinct = sub.groupby("src_norm")["tgt_norm"].nunique()
    strict_src = distinct[distinct == 1].index

    choice = (
        sub[sub["src_norm"].isin(strict_src)]
        .groupby("src_norm")[tgt]
        .agg(lambda s: s.value_counts(dropna=True).index[0])
    )
    return choice.to_dict(), int((distinct > 1).sum())


def cross_fill_colonias(
    df: pd.DataFrame,
    hecho_col: str = "colonia_hecho",
    cat_col: str = "colonia_catalogo",
) -> Tuple[pd.DataFrame, dict]:
    """
    Cross-fill catalog and incident colonias when the mapping is strictly 1→1.
    """
    out = df.copy()
    if (hecho_col not in out.columns) or (cat_col not in out.columns):
        return out, {
            "catalogo_desde_hecho": 0,
            "hecho_desde_catalogo": 0,
            "fuentes_ambiguas_hecho": 0,
            "fuentes_ambiguas_catalogo": 0,
        }

    map_h2c, amb_h2c = _strict_map(out, hecho_col, cat_col)
    map_c2h, amb_c2h = _strict_map(out, cat_col, hecho_col)

    h_norm = norm_series(out[hecho_col])
    c_norm = norm_series(out[cat_col])

    m1 = out[cat_col].isna() & h_norm.notna() & h_norm.map(lambda x: x in map_h2c)
    m2 = out[hecho_col].isna() & c_norm.notna() & c_norm.map(lambda x: x in map_c2h)

    out.loc[m1, cat_col] = h_norm[m1].map(map_h2c)
    out.loc[m2, hecho_col] = c_norm[m2].map(map_c2h)

    stats = {
        "catalogo_desde_hecho": int(m1.sum()),
        "hecho_desde_catalogo": int(m2.sum()),
        "fuentes_ambiguas_hecho": amb_h2c,
        "fuentes_ambiguas_catalogo": amb_c2h,
    }
    return out, stats


# Imputation: competencia
def fill_competencia(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Fill 'competencia' using token rules, mode by borough and a DESCONOCIDO fallback.
    """
    out = df.copy()

    if "competencia" not in out.columns:
        out["competencia"] = pd.NA

    def g(c):
        return (
            norm_series(out[c])
            if c in out.columns
            else pd.Series("", index=out.index, dtype="string")
        )

    contexto = (
        g("fiscalia") + " " + g("agencia") + " " + g("unidad_investigacion")
    ).str.strip()

    federal_pat = re.compile(r"(?:\bFGR\b|\bPGR\b|\bREPUBLICA\b|\bSEIDO\b|\bFEDERAL\b)")
    local_pat = re.compile(
        r"(?:\bFGJ\b|\bPGJ\b|\bCDMX\b|\bLOCAL\b|FUERO COMUN|JUSTICIA)"
    )

    # Token-based rules
    m_fed = out["competencia"].isna() & contexto.str.contains(federal_pat, na=False)
    out.loc[m_fed, "competencia"] = "FEDERAL"

    m_loc = out["competencia"].isna() & contexto.str.contains(local_pat, na=False)
    out.loc[m_loc, "competencia"] = "LOCAL"

    before_na = int(out["competencia"].isna().sum())

    # Mode by alcaldía
    if "alcaldia_hecho" in out.columns:
        modes = out.groupby("alcaldia_hecho", dropna=False)["competencia"].agg(
            lambda s: (
                s.mode(dropna=True).iloc[0] if not s.mode(dropna=True).empty else pd.NA
            )
        )
        out["competencia"] = out["competencia"].fillna(out["alcaldia_hecho"].map(modes))

    after_mode_na = int(out["competencia"].isna().sum())

    # Remaining values to DESCONOCIDO
    m_unk = out["competencia"].isna()
    out.loc[m_unk, "competencia"] = "DESCONOCIDO"

    stats = {
        "desde_tokens_federal": int(m_fed.sum()),
        "desde_tokens_local": int(m_loc.sum()),
        "rellenos_por_moda_alcaldia": before_na - after_mode_na,
        "asignados_desconocido": int(m_unk.sum()),
    }
    return out, stats


# Imputation: coordinates
def fill_latlng_medians(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Impute 'latitud' and 'longitud' with medians by neighborhood and borough.
    """
    out = df.copy()
    rep = {
        "lat_desde_colonia": 0,
        "lng_desde_colonia": 0,
        "lat_desde_alcaldia": 0,
        "lng_desde_alcaldia": 0,
    }

    if not all(c in out.columns for c in ["latitud", "longitud"]):
        return out, rep

    # Neighborhood level
    if "colonia_hecho" in out.columns:
        med = out.groupby("colonia_hecho")[["latitud", "longitud"]].median(
            numeric_only=True
        )
        m1 = out["latitud"].isna() & out["colonia_hecho"].map(med["latitud"]).notna()
        m2 = out["longitud"].isna() & out["colonia_hecho"].map(med["longitud"]).notna()
        rep["lat_desde_colonia"], rep["lng_desde_colonia"] = int(m1.sum()), int(
            m2.sum()
        )
        out.loc[m1, "latitud"] = out.loc[m1, "colonia_hecho"].map(med["latitud"])
        out.loc[m2, "longitud"] = out.loc[m2, "colonia_hecho"].map(med["longitud"])

    # Borough level
    if "alcaldia_hecho" in out.columns:
        med2 = out.groupby("alcaldia_hecho")[["latitud", "longitud"]].median(
            numeric_only=True
        )
        m3 = out["latitud"].isna() & out["alcaldia_hecho"].map(med2["latitud"]).notna()
        m4 = (
            out["longitud"].isna() & out["alcaldia_hecho"].map(med2["longitud"]).notna()
        )
        rep["lat_desde_alcaldia"], rep["lng_desde_alcaldia"] = int(m3.sum()), int(
            m4.sum()
        )
        out.loc[m3, "latitud"] = out["alcaldia_hecho"].map(med2["latitud"])
        out.loc[m4, "longitud"] = out["alcaldia_hecho"].map(med2["longitud"])

    return out, rep


# Drop sparse columns
def preview_drop_sparse(df: pd.DataFrame, col: str, threshold: float = 0.95):
    """
    Preview effect of dropping a column if NA share is above a threshold.
    """
    if col not in df.columns:
        return df, {"se_eliminaria": 0, "razon": "no_presente"}

    miss_pct = float(df[col].isna().mean())
    if miss_pct >= threshold:
        return df.drop(columns=[col]), {
            "se_eliminaria": 1,
            "porcentaje_na": miss_pct,
        }
    return df, {"se_eliminaria": 0, "porcentaje_na": miss_pct}


# Date handling and calendar features
def _parse_date_flex(s: pd.Series) -> pd.Series:
    """
    Parse dates trying strict ISO first and then a flexible day-first parser.
    """
    txt = s.astype("string")
    is_iso = txt.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
    d0 = pd.to_datetime(txt.where(is_iso), errors="coerce", format="%Y-%m-%d")
    d1 = pd.to_datetime(txt.where(~is_iso), errors="coerce", dayfirst=True)
    return d0.fillna(d1).dt.normalize()


def add_weekday_features(
    df: pd.DataFrame,
    date_col: str = "fecha_hecho",
    name_col: str = "dia_semana",
    num_col: str = "dia_semana_num",
) -> pd.DataFrame:
    """
    Add weekday number (Mon=1..Sun=7) and weekday name in Spanish.
    """
    out = df.copy()
    dt = _parse_date_flex(out[date_col])
    wnum = (dt.dt.weekday + 1).astype("Int64")
    nombres = {
        1: "LUNES",
        2: "MARTES",
        3: "MIERCOLES",
        4: "JUEVES",
        5: "VIERNES",
        6: "SABADO",
        7: "DOMINGO",
    }
    out[num_col] = wnum
    out[name_col] = wnum.map(nombres).astype("string")
    return out


def add_quincena_window(
    df: pd.DataFrame,
    date_col: str = "fecha_hecho",
    window_days: int = 2,
    out_col: str = "quincena",
    in_label: str = "Ventana",
    out_label: str = "No_ventana",
) -> pd.DataFrame:
    """
    Flag dates within ±window_days of mid-month and month-end reference dates.
    """
    out = df.copy()
    dt = _parse_date_flex(out[date_col])

    eom = dt + pd.offsets.MonthEnd(0)
    first_dom = dt.dt.to_period("M").dt.to_timestamp()
    day15 = (first_dom + pd.Timedelta(days=14)).dt.normalize()
    prev_eom = dt + pd.offsets.MonthEnd(-1)

    dist = pd.concat(
        [
            (dt - day15).abs().dt.days.rename("D15"),
            (dt - eom).abs().dt.days.rename("DEOM"),
            (dt - prev_eom).abs().dt.days.rename("DPEOM"),
        ],
        axis=1,
    )
    nearest = dist.min(axis=1)
    in_win = nearest <= window_days

    out[out_col] = (
        in_win.fillna(False).map({True: in_label, False: out_label}).astype("string")
    )
    return out


# Weather enrichment
def add_weather_by_alcaldia_fecha(
    df: pd.DataFrame,
    clima_csv_path: str,
    alcaldia_col: str = "alcaldia_hecho",
    date_col: str = "fecha_hecho",
    out_temp: str = "clima_temperatura",
    out_cond: str = "clima_condicion",
) -> Tuple[pd.DataFrame, dict]:
    """
    Join daily weather by normalized borough and date (YYYY-MM-DD).
    """
    out = df.copy()

    clima = robust_read_csv(clima_csv_path)

    need = {"name", "datetime", "temp", "conditions"}
    if not need.issubset(clima.columns):
        raise KeyError(f"Weather CSV must contain: {sorted(need)}")

    clima = clima[["name", "datetime", "temp", "conditions"]].copy()
    clima["name_key"] = norm_series(clima["name"])
    clima["date_key"] = (
        pd.to_datetime(clima["datetime"], errors="coerce", dayfirst=False)
        .dt.strftime("%Y-%m-%d")
        .astype("string")
    )
    clima = clima.rename(columns={"temp": out_temp, "conditions": out_cond})
    clima[out_cond] = clima[out_cond].astype("string").str.strip().str.split().str[0]

    out["alcaldia_key"] = norm_series(out[alcaldia_col])
    out["date_key"] = (
        pd.to_datetime(out[date_col], errors="coerce")
        .dt.strftime("%Y-%m-%d")
        .astype("string")
    )

    out = out.merge(
        clima[["name_key", "date_key", out_temp, out_cond]],
        left_on=["alcaldia_key", "date_key"],
        right_on=["name_key", "date_key"],
        how="left",
    ).drop(columns=["alcaldia_key", "name_key"], errors="ignore")

    stats = {
        "registros_con_clima": int(out[out_temp].notna().sum()),
        "registros_sin_clima": int(len(out) - out[out_temp].notna().sum()),
    }

    out.drop(columns=["date_key"], errors="ignore", inplace=True)
    return out, stats


# CDMX regions
REGIONES_CDMX = {
    "Centro": [
        "Cuauhtémoc",
        "Benito Juárez",
        "Venustiano Carranza",
    ],
    "Norte": [
        "Gustavo A. Madero",
        "Azcapotzalco",
    ],
    "Sur": [
        "Coyoacán",
        "Tlalpan",
        "Xochimilco",
        "Magdalena Contreras",
        "La Magdalena Contreras",
    ],
    "Oriente": [
        "Iztapalapa",
        "Iztacalco",
        "Tláhuac",
        "Milpa Alta",
    ],
    "Poniente": [
        "Miguel Hidalgo",
        "Álvaro Obregón",
        "Cuajimalpa",
        "Cuajimalpa de Morelos",
    ],
}


def _norm_simple(s):
    """Simple lowercase + accent stripping for borough names."""
    if pd.isna(s):
        return None
    s = str(s).strip().lower()
    s = (
        s.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )
    return s


REGIONES_NORM = {
    region: [_norm_simple(a) for a in alcs] for region, alcs in REGIONES_CDMX.items()
}


def asignar_region(alcaldia: str) -> str:
    """
    Return CDMX region (Centro, Norte, Sur, Oriente, Poniente) or 'Desconocido'.
    """
    alc_norm = _norm_simple(alcaldia)
    if alc_norm is None:
        return None
    for region, lista_alcs in REGIONES_NORM.items():
        if alc_norm in lista_alcs:
            return region
    return "Desconocido"


# Month names in Spanish
MESES_ENG_TO_ES = {
    "january": "Enero",
    "february": "Febrero",
    "march": "Marzo",
    "april": "Abril",
    "may": "Mayo",
    "june": "Junio",
    "july": "Julio",
    "august": "Agosto",
    "september": "Septiembre",
    "october": "Octubre",
    "november": "Noviembre",
    "december": "Diciembre",
}

_MESES_ES = {
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
}


def mes_a_espanol(s):
    """Normalize month label to Spanish name or return 'Desconocido'."""
    if pd.isna(s):
        return None
    s_norm = str(s).strip().lower()
    s_norm = (
        s_norm.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

    if s_norm in _MESES_ES:
        return s_norm.capitalize()

    if s_norm in MESES_ENG_TO_ES:
        return MESES_ENG_TO_ES[s_norm]

    return "Desconocido"


# Time-of-day classification
def clasificar_hora(h) -> str:
    """
    Classify time into Mañana / Tarde / Noche.
    """
    if pd.isna(h):
        return None

    minutos = h.hour * 60 + h.minute

    if 5 * 60 <= minutos < 12 * 60:
        return "Mañana"
    elif 12 * 60 <= minutos < 19 * 60:
        return "Tarde"
    else:
        return "Noche"
