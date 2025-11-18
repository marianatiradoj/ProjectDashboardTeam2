# regex_loader.py
# Carga patrones desde regex_config.jam y aplica clasificación.
# Aquí NO hay patrones quemados: solo funciones + diccionarios de lógica.

import re
from typing import Tuple, Dict, Optional

import pandas as pd

from .update_base import norm_series


# ------------------------------------------------------------
# Carga de patrones desde .jam
# ------------------------------------------------------------


def load_regex_config(path: str) -> Dict[str, re.Pattern]:
    """
    Lee regex_config.jam.
    Formato de cada línea:
        NOMBRE = patron_regex
    Líneas vacías o con # al inicio se ignoran.
    """
    patterns: Dict[str, re.Pattern] = {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, pattern = line.split("=", 1)
                key = key.strip()
                pattern = pattern.strip()
                if not key or not pattern:
                    continue
                patterns[key] = re.compile(pattern)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"regex_config.jam no encontrado en: {path}. "
            "Asegúrate de que el archivo exista y tenga los patrones."
        )

    return patterns


# ------------------------------------------------------------
# Orden de evaluación y lógica de grupos (no es regex)
# ------------------------------------------------------------

GROUP_ORDER = [
    "FEMINICIDIO",
    "HOMICIDIO",
    "PERDIDA_VIDA_SUICIDIO",
    "SECUESTRO",
    "DELITO_SEXUAL",
    "LESIONES_ARMA",
    "AMENAZAS_EXTORSION",
    "VIOLENCIA_FAMILIAR",
    "LESIONES_INTENCIONALES",
    "MALTRATO_ANIMAL",
    "ROBO_CUENTAHABIENTE",
    "ROBO_NEGOCIO",
    "ROBO_CASA",
    "ROBO_REPARTIDOR",
    "ROBO_TRANSEUNTE_PRIORITARIO",
    "ROBO_PASAJERO",
    "ROBO_TRANSEUNTE",
    "ROBO_VEHICULO",
    "ROBO_OBJETOS",
    "NARCOMENUDEO_POSESION",
    "FRAUDE_ABUSO_CONFIANZA",
    "FALSIFICACION_DOCUMENTO",
    "DELITO_ADMINISTRATIVO",
    "DELITO_BAJO_IMPACTO",
    "SIN_DELITO",
    "DESPOJO_VIA_PUBLICA",
]

ALIAS = {
    "ROBO_TRANSEUNTE_PRIORITARIO": "ROBO_TRANSEUNTE",
    "DESPOJO_VIA_PUBLICA": "OTRO",
    "PERDIDA_VIDA_SUICIDIO": "PERDIDA_VIDA_SUICIDIO",
}

GROUP_TO_MACRO = {
    # 1) Violencia letal
    "HOMICIDIO": "VIOLENCIA_LETAL",
    "FEMINICIDIO": "VIOLENCIA_LETAL",
    "PERDIDA_VIDA_SUICIDIO": "VIOLENCIA_LETAL",
    # 2) Violencia no letal
    "SECUESTRO": "VIOLENCIA_NO_LETAL",
    "DELITO_SEXUAL": "VIOLENCIA_NO_LETAL",
    "LESIONES_ARMA": "VIOLENCIA_NO_LETAL",
    "AMENAZAS_EXTORSION": "VIOLENCIA_NO_LETAL",
    "VIOLENCIA_FAMILIAR": "VIOLENCIA_NO_LETAL",
    "LESIONES_INTENCIONALES": "VIOLENCIA_NO_LETAL",
    "MALTRATO_ANIMAL": "VIOLENCIA_NO_LETAL",
    # 3) Robos a persona
    "ROBO_TRANSEUNTE": "ROBO_PERSONA",
    "ROBO_PASAJERO": "ROBO_PERSONA",
    "ROBO_CUENTAHABIENTE": "ROBO_PERSONA",
    "ROBO_OBJETOS": "ROBO_PERSONA",
    "ROBO_TRANSEUNTE_PRIORITARIO": "ROBO_PERSONA",
    # 4) Robos a propiedad / vehículo / reparto
    "ROBO_CASA": "ROBO_PROPIEDAD",
    "ROBO_NEGOCIO": "ROBO_PROPIEDAD",
    "ROBO_VEHICULO": "ROBO_PROPIEDAD",
    "ROBO_REPARTIDOR": "ROBO_PROPIEDAD",
    # 5) Macrogrupo ADMINISTRATIVO
    "SIN_DELITO": "ADMINISTRATIVO",
    "DELITO_BAJO_IMPACTO": "ADMINISTRATIVO",
    "DELITO_ADMINISTRATIVO": "ADMINISTRATIVO",
    "FALSIFICACION_DOCUMENTO": "ADMINISTRATIVO",
    # 6) Bajo impacto / otros
    "NARCOMENUDEO_POSESION": "BAJO_IMPACTO",
    "FRAUDE_ABUSO_CONFIANZA": "BAJO_IMPACTO",
    "DESPOJO_VIA_PUBLICA": "BAJO_IMPACTO",
    "OTRO": "BAJO_IMPACTO",
}

MAP_VIOLENCIA = {
    "SIN_DELITO": "NO_APLICA",
    "DELITO_BAJO_IMPACTO": "NO_APLICA",
    "HOMICIDIO": "CON_VIOLENCIA",
    "FEMINICIDIO": "CON_VIOLENCIA",
    "SECUESTRO": "CON_VIOLENCIA",
    "DELITO_SEXUAL": "CON_VIOLENCIA",
    "LESIONES_ARMA": "CON_VIOLENCIA",
    "AMENAZAS_EXTORSION": "CON_VIOLENCIA",
    "VIOLENCIA_FAMILIAR": "CON_VIOLENCIA",
    "LESIONES_INTENCIONALES": "CON_VIOLENCIA",
    "MALTRATO_ANIMAL": "CON_VIOLENCIA",
    "ROBO_TRANSEUNTE": "CON_VIOLENCIA",
    "ROBO_REPARTIDOR": "CON_VIOLENCIA",
    "ROBO_CUENTAHABIENTE": "CON_VIOLENCIA",
    "ROBO_PASAJERO": "CON_VIOLENCIA",
    "ROBO_NEGOCIO": "DESCONOCIDO",
    "ROBO_CASA": "DESCONOCIDO",
    "ROBO_VEHICULO": "DESCONOCIDO",
    "ROBO_OBJETOS": "DESCONOCIDO",
    "NARCOMENUDEO_POSESION": "NO_APLICA",
    "FRAUDE_ABUSO_CONFIANZA": "NO_APLICA",
    "FALSIFICACION_DOCUMENTO": "NO_APLICA",
    "DELITO_ADMINISTRATIVO": "NO_APLICA",
    "PERDIDA_VIDA_SUICIDIO": "NO_APLICA",
    "OTRO": "DESCONOCIDO",
}


# ------------------------------------------------------------
# Helpers internos
# ------------------------------------------------------------


def _group_from_text(t: pd.Series, rgx: Dict[str, re.Pattern]) -> pd.Series:
    """
    Aplica precedencia de primer match usando GROUP_ORDER; por defecto OTRO.
    """
    out = pd.Series(pd.NA, index=t.index, dtype="string")
    for key in GROUP_ORDER:
        if key not in rgx:
            continue
        mask = t.str.contains(rgx[key], na=False)
        out.loc[mask & out.isna()] = ALIAS.get(key, key)
    out = out.where(t.isna(), out.fillna("OTRO"))
    return out


# ------------------------------------------------------------
# Función principal que se usa desde el pipeline
# ------------------------------------------------------------


def classify_regex(
    df: pd.DataFrame,
    delito_col: str = "delito",
    grupo_col: str = "delito_grupo",
    violencia_col: str = "clase_violencia",
    pasajero_col: str = "robo_pasajero",
    regex_config_path: Optional[str] = "regex_config.jam",
) -> Tuple[pd.DataFrame, dict]:
    """
    Usa patrones de regex_config.jam para estandarizar delitos:
      - 'delito_grupo'
      - 'delito_grupo_macro'
      - 'clase_violencia'
      - 'robo_pasajero' (0/1)
    """

    if regex_config_path is None:
        raise ValueError("Debes indicar la ruta de regex_config.jam")

    rgx = load_regex_config(regex_config_path)

    # Aseguramos que los grupos clave existan
    missing_keys = [k for k in GROUP_ORDER if k not in rgx]
    if missing_keys:
        raise KeyError(f"Faltan patrones en regex_config.jam para: {missing_keys}")

    out = df.copy()

    t = (
        norm_series(out[delito_col])
        if delito_col in out.columns
        else pd.Series("", index=out.index, dtype="string")
    )

    grp = _group_from_text(t, rgx)

    # Forzar algunos OTRO a grupos más informativos usando contexto
    # Para vehículo usamos el mismo patrón de ROBO_VEHICULO
    veh_pat = rgx.get("ROBO_VEHICULO", re.compile(""))

    grp.loc[(grp.isna() | (grp == "OTRO")) & t.str.contains(veh_pat, na=False)] = (
        "ROBO_VEHICULO"
    )

    obj_pat = rgx.get("ROBO_OBJETOS", re.compile(""))
    grp.loc[(grp.isna() | (grp == "OTRO")) & t.str.contains(obj_pat, na=False)] = (
        "ROBO_OBJETOS"
    )

    out[grupo_col] = grp.astype("string")

    out["delito_grupo_macro"] = (
        out[grupo_col].map(GROUP_TO_MACRO).fillna("NO_DELITO_OTROS").astype("string")
    )

    out[violencia_col] = out[grupo_col].map(MAP_VIOLENCIA).astype("string")

    pasajero_pat = rgx.get("ROBO_PASAJERO", re.compile(""))
    out[pasajero_col] = t.str.contains(pasajero_pat, na=False).astype("Int64")

    stats = {
        "n_grupos_despues": int(out[grupo_col].nunique(dropna=False)),
        "n_grupos_macro_despues": int(out["delito_grupo_macro"].nunique(dropna=False)),
        "n_clases_violencia": int(out[violencia_col].nunique(dropna=False)),
        "n_robo_pasajero_1": int(out[pasajero_col].fillna(0).eq(1).sum()),
        "conteos_macrogrupo": (
            out["delito_grupo_macro"].value_counts(dropna=False).to_dict()
        ),
        "porcentaje_macrogrupo": (
            out["delito_grupo_macro"]
            .value_counts(normalize=True, dropna=False)
            .mul(100)
            .round(2)
            .to_dict()
        ),
        "total_registros": len(out),
    }

    return out, stats
