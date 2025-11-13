# app/EDA/user_eda.py
from __future__ import annotations
from typing import Tuple, Dict, Optional
import re
import unicodedata
import numpy as np
import pandas as pd
from .regex_loader import load_regex_config, RegexConfig


# -------- utils ----------
def robust_read_csv(path: str, **kwargs) -> pd.DataFrame:
    encodings = kwargs.pop("encodings", ["utf-8", "latin1", "cp1252"])
    tried = []
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, engine="python", sep=None, **kwargs)
        except Exception as e:
            tried.append(f"{enc}:{type(e).__name__}")
    raise ValueError(
        f"robust_read_csv() no pudo leer el archivo. Intentos -> {', '.join(tried)}"
    )


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def norm_series(s: pd.Series) -> pd.Series:
    out = s.astype("string").str.strip().str.lower()
    out = out.map(lambda x: _strip_accents(x) if isinstance(x, str) else x)
    out = out.str.replace(r"\s+", " ", regex=True)
    return out


# -------- colonias ----------
def cross_fill_colonias(
    df: pd.DataFrame,
    col_hecho: str = "colonia_hecho",
    col_catalogo: str = "colonia_catalogo",
) -> Tuple[pd.DataFrame, Dict]:
    out = df.copy()
    if col_hecho in out.columns and col_catalogo in out.columns:
        mask_h = out[col_hecho].isna() & out[col_catalogo].notna()
        out.loc[mask_h, col_hecho] = out.loc[mask_h, col_catalogo]
        mask_c = out[col_catalogo].isna() & out[col_hecho].notna()
        out.loc[mask_c, col_catalogo] = out.loc[mask_c, col_hecho]
    else:
        mask_h = pd.Series(False, index=out.index)
        mask_c = pd.Series(False, index=out.index)
    stats = {
        "filled_hecho_from_catalogo": int(mask_h.sum()),
        "filled_catalogo_from_hecho": int(mask_c.sum()),
    }
    return out, stats


# -------- competencia ----------
def fill_competencia(
    df: pd.DataFrame,
    competencia_col: str = "competencia",
    alcaldia_col: str = "alcaldia_hecho",
) -> Tuple[pd.DataFrame, Dict]:
    out = df.copy()
    if competencia_col not in out.columns:
        out[competencia_col] = pd.Series([None] * len(out), dtype="string")
    txt = norm_series(out.get(competencia_col))
    is_na = out[competencia_col].isna() | (
        out[competencia_col].astype("string").str.strip() == ""
    )

    def _rule(x: Optional[str]) -> Optional[str]:
        if not isinstance(x, str):
            return None
        if "federal" in x:
            return "FEDERAL"
        if "local" in x:
            return "LOCAL"
        return None

    out.loc[is_na, competencia_col] = txt[is_na].map(_rule)
    if alcaldia_col in out.columns:
        moda = (
            out.groupby(alcaldia_col)[competencia_col].agg(
                lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else np.nan
            )
        ).to_dict()
        still_na = out[competencia_col].isna()
        out.loc[still_na, competencia_col] = out.loc[still_na, alcaldia_col].map(moda)
    out[competencia_col] = out[competencia_col].fillna("UNKNOWN").astype("string")
    return out, {"counts": out[competencia_col].value_counts(dropna=False).to_dict()}


# -------- regex runtime ----------
def _get_regex_runtime(regex_path: Optional[str]) -> RegexConfig:
    if regex_path:
        try:
            return load_regex_config(regex_path)
        except Exception:
            pass
    # fallback embebido (mínimo)
    patterns = {
        "SEXUAL_CRIME": re.compile(
            r"\bVIOLACION\b|\bABUSO\s+SEXUAL\b|\bACOSO\s+SEXUAL\b|\bHOSTIGAMIENTO\s+SEXUAL\b|\bCONTRA\s+LA\s+INTIMIDAD\s+SEXUAL\b",
            re.I,
        ),
        "INJURY_WEAPON": re.compile(
            r"\bLESIONES\b.*\bARMA(?:\s+DE\s+FUEGO)?\b|\bDISPARO\b", re.I
        ),
        "INJURY_INTENTIONAL": re.compile(
            r"\bLESIONES\s+INTENCIONALES?\b|\bGOLPES\b", re.I
        ),
        "THREATS": re.compile(
            r"\bAMENAZAS?\b|\bEXTORSI[OÓ]N\b|\bTENTATIVA\s+DE\s+EXTORSI[OÓ]N\b", re.I
        ),
        "FAMILY_VIOLENCE": re.compile(r"\bVIOLENCIA\s+FAMILIAR\b", re.I),
        "DRUG_POSSESSION": re.compile(
            r"\bNARCOMENUDEO\b|\bPOSESI[OÓ]N\s+SIMPLE\b|\bDROGAS?\b", re.I
        ),
        "FRAUD": re.compile(
            r"\bFRAUDE\b|\bCOBRANZA\s+ILEGITIMA\b|\bENGA[NÑ]O\b|\bESTAFA\b|\bABUSO\s+DE\s+CONFIANZA\b",
            re.I,
        ),
        "FORGERY_DOC": re.compile(
            r"\bFALSIFICACI[OÓ]N\b.*\bDOCUMENTOS?\b|\bFALSIFICACI[OÓ]N\s+DE\s+T[IÍ]TULOS\b|\bUSO\s+DE\s+DOCUMENTO\s+FALSO\b|\bUSO\s+INDEBIDO\s+DE\s+DOCUMENTOS\b|\bFALSEDAD\s+ANTE\s+AUTORIDADES\b",
            re.I,
        ),
        "ADMIN_OFFENSE": re.compile(
            r"\bADMINISTRACI[OÓ]N\s+DE\s+JUSTICIA\b|\bENCUBRIMIENTO\b|\bNEGACI[OÓ]N\s+DEL\s+SERVICIO\s+PUBLICO\b|\bQUEBRANTAMIENTO\s+DE\s+SELLOS\b|\bCONTRA\s+EL\s+CUMPLIMIENTO\s+DE\s+LA\s+OBLIGACION\s+ALIMENTARIA\b|\bDELITOS\s+AMBIENTALES\b|\bDISCRIMINACI[OÓ]N\b|\bATAQUE\s+A\s+LAS\s+VIAS\s+GENERALES\s+DE\s+COMUNICACI[OÓ]N\b|\bOMISI[OÓ]N\s+DE\s+AUXILIO\b|\bOMISI[OÓ]N\s+DE\s+CUIDADO\b",
            re.I,
        ),
        "ROBBERY_ACCOUNT_HOLDER": re.compile(r"\bCUENTAHABIENTE\b|\bCAJERO\b", re.I),
        "ROBBERY_BUSINESS": re.compile(
            r"\bROBO\s+A\s+NEGOCIO\b|\bCOMERCIO\b|\bTIENDA\b|\bROBO\s+S/V\s+DENTRO\s+DE\s+NEGOCIOS?\b|\bAUTOSERVICIOS?\b|\bCONVENIENCIA\b",
            re.I,
        ),
        "ROBBERY_HOME": re.compile(
            r"\bCASA\s+HABITACI[OÓ]N\b|\bDOMICILIO\b|\bVIVIENDA\b|\bALLANAMIENTO\s+DE\s+MORADA\b|\bDESPACHO\b|\bOFICINA\b|\bESTABLECIMIENTO\s+MERCANTIL\b",
            re.I,
        ),
        "ROBBERY_DELIVERY": re.compile(r"\bREPARTIDOR\b", re.I),
        "FORCE_OTHER": re.compile(r"^\s*DE\s+LA\s+VIA\s+PUBLICA\s*$", re.I),
        "ROBBERY_PEDESTRIAN_PRIORITY": re.compile(
            r"(?:\bROBO\s+A\s+TRANSEUNTE\b.*\bA\s+BORDO\s+DE(?:L)?\s+(?:TAXI|METROBUS|METRO|MICROBUS|AUTOBUS|CAMION|PESERO|COMBI|COLECTIVO|RTP|TROLEBUS|UBER|DIDI)\b)|(?:\bROBO\s+A\s+TRANSEUNTE\s+CONDUCTOR\s+DE\s+TAXI\b)",
            re.I,
        ),
    }
    order = [
        "SEXUAL_CRIME",
        "INJURY_WEAPON",
        "INJURY_INTENTIONAL",
        "THREATS",
        "FAMILY_VIOLENCE",
        "ROBBERY_PEDESTRIAN_PRIORITY",
        "ROBBERY_ACCOUNT_HOLDER",
        "ROBBERY_BUSINESS",
        "ROBBERY_HOME",
        "ROBBERY_DELIVERY",
        "FORCE_OTHER",
        "DRUG_POSSESSION",
        "FRAUD",
        "FORGERY_DOC",
        "ADMIN_OFFENSE",
    ]
    macro = {
        "ROBBERY_PEDESTRIAN_PRIORITY": "ROBBERY_PERSON",
        "ROBBERY_ACCOUNT_HOLDER": "ROBBERY_PERSON",
        "ROBBERY_BUSINESS": "ROBBERY_PROPERTY",
        "ROBBERY_HOME": "ROBBERY_PROPERTY",
        "ROBBERY_DELIVERY": "ROBBERY_PROPERTY",
        "SEXUAL_CRIME": "VIOLENT_OTHER",
        "INJURY_WEAPON": "VIOLENT_OTHER",
        "INJURY_INTENTIONAL": "VIOLENT_OTHER",
        "THREATS": "VIOLENT_OTHER",
        "FAMILY_VIOLENCE": "VIOLENT_OTHER",
        "DRUG_POSSESSION": "LOW_IMPACT",
        "FRAUD": "LOW_IMPACT",
        "FORGERY_DOC": "LOW_IMPACT",
        "ADMIN_OFFENSE": "NON_CRIME_OTHER",
        "FORCE_OTHER": "LOW_IMPACT",
    }
    violent = {
        "SEXUAL_CRIME",
        "INJURY_WEAPON",
        "INJURY_INTENTIONAL",
        "THREATS",
        "FAMILY_VIOLENCE",
    }
    return RegexConfig(
        patterns=patterns, order=order, macro_map=macro, violent_set=violent
    )


def classify_regex(
    df: pd.DataFrame,
    delito_col: str = "delito",
    grupo_col: str = "delito_grupo",
    violencia_col: str = "violencia_class",
    pasajero_col: str = "robo_pasajero",
    regex_path: Optional[str] = None,
) -> Tuple[pd.DataFrame, Dict]:
    out = df.copy()
    if delito_col not in out.columns:
        out[delito_col] = pd.Series([None] * len(out), dtype="string")
    rx = _get_regex_runtime(regex_path)
    texto = norm_series(out[delito_col]).fillna("")

    def _first_match(text: str) -> str:
        t = text or ""
        for key in rx.order:
            if rx.patterns[key].search(t):
                return key
        return "OTHER"

    grupos = texto.map(_first_match)
    out[grupo_col] = grupos.astype("string")
    out["delito_grupo_macro"] = grupos.map(
        lambda k: rx.macro_map.get(k, "NON_CRIME_OTHER")
    ).astype("string")
    out[violencia_col] = grupos.map(
        lambda k: "VIOLENT" if k in rx.violent_set else "NON_VIOLENT"
    ).astype("string")
    pasajero_regex = rx.patterns.get("ROBBERY_PEDESTRIAN_PRIORITY")
    out[pasajero_col] = (
        (grupos == "ROBBERY_PEDESTRIAN_PRIORITY")
        | texto.map(
            lambda x: bool(pasajero_regex.search(x)) if pasajero_regex else False
        )
    ).astype("boolean")
    counts = out[grupo_col].value_counts(dropna=False).to_dict()
    macro_counts = out["delito_grupo_macro"].value_counts(dropna=False).to_dict()
    total = max(int(sum(macro_counts.values())), 1)
    macro_pct = {k: round(v * 100.0 / total, 2) for k, v in macro_counts.items()}
    stats = {
        "group_counts": counts,
        "macrogroup_counts": macro_counts,
        "macrogroup_pct": macro_pct,
        "n_total": int(len(out)),
        "source": ("external" if regex_path else "embedded"),
    }
    return out, stats


# -------- calendario ----------
def add_weekday_features(
    df: pd.DataFrame,
    date_col: str = "fecha_hecho",
    name_col: str = "weekday",
    num_col: str = "weekday_num",
) -> pd.DataFrame:
    out = df.copy()
    dt = pd.to_datetime(out[date_col], errors="coerce")
    out[num_col] = dt.dt.weekday + 1
    nombres = {
        0: "Lunes",
        1: "Martes",
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo",
    }
    out[name_col] = dt.dt.weekday.map(nombres).astype("string")
    return out


def add_quincena_window(
    df: pd.DataFrame,
    date_col: str = "fecha_hecho",
    window_days: int = 2,
    out_col: str = "quincena_window",
    in_label: str = "WINDOW",
    out_label: str = "NO_WINDOW",
) -> pd.DataFrame:
    out = df.copy()
    dt = pd.to_datetime(out[date_col], errors="coerce")
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


# -------- lat/lng ----------
def fill_latlng_medians(
    df: pd.DataFrame,
    lat_col: str = "latitud",
    lng_col: str = "longitud",
    colonia_col: str = "colonia_hecho",
    alcaldia_col: str = "alcaldia_hecho",
) -> Tuple[pd.DataFrame, Dict]:
    out = df.copy()
    lat0 = int(out[lat_col].isna().sum()) if lat_col in out.columns else 0
    lng0 = int(out[lng_col].isna().sum()) if lng_col in out.columns else 0
    med_col = out.groupby(colonia_col)[[lat_col, lng_col]].median(numeric_only=True)
    med_alc = out.groupby(alcaldia_col)[[lat_col, lng_col]].median(numeric_only=True)
    missing_lat = (
        out[lat_col].isna()
        if lat_col in out.columns
        else pd.Series(False, index=out.index)
    )
    missing_lng = (
        out[lng_col].isna()
        if lng_col in out.columns
        else pd.Series(False, index=out.index)
    )
    if colonia_col in out.columns:
        out.loc[missing_lat, lat_col] = out.loc[missing_lat, colonia_col].map(
            med_col[lat_col]
        )
        out.loc[missing_lng, lng_col] = out.loc[missing_lng, colonia_col].map(
            med_col[lng_col]
        )
    missing_lat = (
        out[lat_col].isna()
        if lat_col in out.columns
        else pd.Series(False, index=out.index)
    )
    missing_lng = (
        out[lng_col].isna()
        if lng_col in out.columns
        else pd.Series(False, index=out.index)
    )
    if alcaldia_col in out.columns:
        out.loc[missing_lat, lat_col] = out.loc[missing_lat, alcaldia_col].map(
            med_alc[lat_col]
        )
        out.loc[missing_lng, lng_col] = out.loc[missing_lng, alcaldia_col].map(
            med_alc[lng_col]
        )
    stats = {
        "lat_na_before": lat0,
        "lng_na_before": lng0,
        "lat_na_after": (
            int(out[lat_col].isna().sum()) if lat_col in out.columns else lat0
        ),
        "lng_na_after": (
            int(out[lng_col].isna().sum()) if lng_col in out.columns else lng0
        ),
    }
    return out, stats


# -------- clima ----------
def add_weather_by_alcaldia_fecha(
    df: pd.DataFrame,
    clima_csv_path: str,
    alcaldia_col: str = "alcaldia_hecho",
    date_col: str = "fecha_hecho",
    out_temp: str = "clima_temp",
    out_cond: str = "clima_conditions",
) -> Tuple[pd.DataFrame, Dict]:
    out = df.copy()
    clima = robust_read_csv(clima_csv_path)
    need = {"name", "datetime", "temp", "conditions"}
    if not need.issubset(set(clima.columns)):
        raise KeyError(f"Weather CSV must contain: {sorted(need)}")
    clima = clima[["name", "datetime", "temp", "conditions"]].copy()
    clima["name_key"] = norm_series(clima["name"])
    clima["date_key"] = (
        pd.to_datetime(clima["datetime"], errors="coerce", dayfirst=True)
        .dt.strftime("%Y-%m-%d")
        .astype("string")
    )
    clima = clima.rename(columns={"temp": out_temp, "conditions": out_cond})
    clima[out_cond] = clima[out_cond].astype("string").str.strip()
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
        "matched": int(out[out_temp].notna().sum()),
        "unmatched": int(len(out) - out[out_temp].notna().sum()),
        "total": int(len(out)),
    }
    return out, stats


if __name__ == "__main__":
    pass
