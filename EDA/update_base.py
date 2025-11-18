# update_base.py
# Utilidades generales para el EDA (IO, fechas, clima, regiones, etc.)

import re
import unicodedata
from typing import Dict, Tuple

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# IO & diagnósticos
# ------------------------------------------------------------


def robust_read_csv(
    path: str, try_encodings=("utf-8", "latin-1", "cp1252"), **kwargs
) -> pd.DataFrame:
    """
    Lee un CSV probando varios encodings comunes.
    Lanza un error claro si ninguno funciona.
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
    Tabla con NA absolutos y porcentaje, ordenada desc.
    """
    counts = df.isna().sum().astype(int)
    pct = (counts / len(df) * 100) if len(df) else 0.0
    return pd.DataFrame({"missing": counts, "missing_%": pct}).sort_values(
        "missing_%", ascending=False
    )


def report_duplicates_full(df: pd.DataFrame) -> Dict[str, int]:
    """
    Cuenta duplicados exactos en todas las columnas.
    """
    return {"duplicate_rows_full": int(df.duplicated(keep=False).sum())}


# ------------------------------------------------------------
# Normalización de texto
# ------------------------------------------------------------


def _strip_accents(s: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", str(s))
        if unicodedata.category(ch) != "Mn"
    )


def norm_series(s: pd.Series) -> pd.Series:
    """
    Mayúsculas, recorte, colapso de espacios, sin acentos; devuelve dtype 'string'.
    """
    s = s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    s = s.map(_strip_accents).str.upper()
    return s.astype("string")


# ------------------------------------------------------------
# Cross-fill colonias (mapeo estricto 1→1)
# ------------------------------------------------------------


def _strict_map(df: pd.DataFrame, src: str, tgt: str) -> Tuple[Dict[str, str], int]:
    """
    Construye mapa src→tgt SOLO para fuentes que mapean a exactamente un único destino.
    Regresa (mapping, conteo_de_fuentes_ambiguas).
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
    Rellena catálogo desde hecho y hecho desde catálogo SOLO cuando el mapeo es 1→1 estricto.
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


# ------------------------------------------------------------
# Imputación: competencia
# ------------------------------------------------------------


def fill_competencia(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Compleción conservadora de 'competencia':
      1) Reglas por tokens en contexto institucional,
      2) moda por 'alcaldia_hecho',
      3) residuales a 'DESCONOCIDO'.
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

    # Reglas por tokens
    m_fed = out["competencia"].isna() & contexto.str.contains(federal_pat, na=False)
    out.loc[m_fed, "competencia"] = "FEDERAL"

    m_loc = out["competencia"].isna() & contexto.str.contains(local_pat, na=False)
    out.loc[m_loc, "competencia"] = "LOCAL"

    before_na = int(out["competencia"].isna().sum())

    # Moda por alcaldía
    if "alcaldia_hecho" in out.columns:
        modes = out.groupby("alcaldia_hecho", dropna=False)["competencia"].agg(
            lambda s: (
                s.mode(dropna=True).iloc[0] if not s.mode(dropna=True).empty else pd.NA
            )
        )
        out["competencia"] = out["competencia"].fillna(out["alcaldia_hecho"].map(modes))

    after_mode_na = int(out["competencia"].isna().sum())

    # Residuales a DESCONOCIDO
    m_unk = out["competencia"].isna()
    out.loc[m_unk, "competencia"] = "DESCONOCIDO"

    stats = {
        "desde_tokens_federal": int(m_fed.sum()),
        "desde_tokens_local": int(m_loc.sum()),
        "rellenos_por_moda_alcaldia": before_na - after_mode_na,
        "asignados_desconocido": int(m_unk.sum()),
    }
    return out, stats


# ------------------------------------------------------------
# Imputación: coordenadas
# ------------------------------------------------------------


def fill_latlng_medians(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Imputa 'latitud' y 'longitud' usando medianas a nivel 'colonia_hecho';
    recurre a medianas por 'alcaldia_hecho' cuando no hay mediana de colonia.
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

    # Nivel colonia
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

    # Nivel alcaldía
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


# ------------------------------------------------------------
# Drop de columnas muy escasas
# ------------------------------------------------------------


def preview_drop_sparse(df: pd.DataFrame, col: str, threshold: float = 0.95):
    """
    Previsualiza el efecto de eliminar `col` si % de NA ≥ threshold.
    No muta el dataframe original.
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


# ------------------------------------------------------------
# Manejo de fechas y features calendario
# ------------------------------------------------------------


def _parse_date_flex(s: pd.Series) -> pd.Series:
    """
    Parse robusto: intenta ISO estricto (YYYY-MM-DD); si no, dayfirst=True.
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
    Deriva número de día (Lun=1..Dom=7) y nombre de día en español desde `date_col`.
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
    Marca fechas dentro de ±window_days de:
      15 del mes, fin de mes actual, o fin de mes anterior.
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


# ------------------------------------------------------------
# Enriquecimiento con clima
# ------------------------------------------------------------


def add_weather_by_alcaldia_fecha(
    df: pd.DataFrame,
    clima_csv_path: str,
    alcaldia_col: str = "alcaldia_hecho",
    date_col: str = "fecha_hecho",
    out_temp: str = "clima_temperatura",
    out_cond: str = "clima_condicion",
) -> Tuple[pd.DataFrame, dict]:
    """
    LEFT join de clima diario (temp, condición) por alcaldía normalizada + fecha (YYYY-MM-DD)
    sobre el dataset de delitos.
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


# ------------------------------------------------------------
# Regiones CDMX
# ------------------------------------------------------------

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
    Devuelve región CDMX (Centro, Norte, Sur, Oriente, Poniente) o 'Desconocido'.
    """
    alc_norm = _norm_simple(alcaldia)
    if alc_norm is None:
        return None
    for region, lista_alcs in REGIONES_NORM.items():
        if alc_norm in lista_alcs:
            return region
    return "Desconocido"


# ------------------------------------------------------------
# Meses en español
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Clasificar hora en mañana / tarde / noche
# ------------------------------------------------------------


def clasificar_hora(h) -> str:
    """
    Devuelve Mañana / Tarde / Noche según hora (objeto datetime.time).
    """
    if pd.isna(h):
        return None

    minutos = h.hour * 60 + h.minute

    if 5 * 60 <= minutos < 12 * 60:  # 05:00 - 11:59
        return "Mañana"
    elif 12 * 60 <= minutos < 19 * 60:  # 12:00 - 18:59
        return "Tarde"
    else:  # 19:00 - 04:59
        return "Noche"
