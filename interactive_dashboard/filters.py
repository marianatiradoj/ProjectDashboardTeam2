# interactive_dashboard/filters.py

from __future__ import annotations

from typing import Tuple, Dict, Any, List

import pandas as pd
import streamlit as st


# Mapping used only for display purposes in the UI.
# Internal dataframe column names remain unchanged.
DISPLAY_NAMES: Dict[str, str] = {
    "fecha_hecho": "Fecha del hecho",
    "anio_hecho": "Año del hecho",
    "mes_hecho": "Mes del hecho",
    "dia": "Día de la semana",
    "periodo_hora": "Periodo del día",
    "delito_grupo_macro": "Tipo principal de delito",
    "delito_grupo": "Grupo del delito",
    "alcaldia_hecho": "Alcaldía",
    "region_cdmx": "Región de la ciudad",
    "colonia_hecho": "Colonia",
    "clase_violencia": "Tipo de violencia",
    "clima_condicion": "Condición climática",
    "quincena": "Ventana de quincena",
    "latitud": "Latitud",
    "longitud": "Longitud",
}


# Reference orders for months and weekdays in Spanish.
_MONTH_ORDER = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]

_DAY_ORDER = [
    "LUNES",
    "MARTES",
    "MIERCOLES",
    "MIÉRCOLES",
    "JUEVES",
    "VIERNES",
    "SABADO",
    "SÁBADO",
    "DOMINGO",
]


def _ensure_datetime_fecha_hecho(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure that 'fecha_hecho' is parsed as datetime."""
    if "fecha_hecho" not in df.columns:
        return df
    if pd.api.types.is_datetime64_any_dtype(df["fecha_hecho"]):
        return df
    df_copy = df.copy()
    df_copy["fecha_hecho"] = pd.to_datetime(df_copy["fecha_hecho"], errors="coerce")
    return df_copy


def _sorted_unique(df: pd.DataFrame, column: str) -> List[Any]:
    """Return sorted unique non-null values."""
    if column not in df.columns:
        return []
    return sorted(df[column].dropna().unique().tolist())


def _sorted_months(df: pd.DataFrame, column: str = "mes_hecho") -> List[Any]:
    """Sort Spanish month labels in natural order."""
    if column not in df.columns:
        return []
    values = df[column].dropna().unique().tolist()
    month_index = {m: i for i, m in enumerate(_MONTH_ORDER)}

    def sort_key(val):
        t = str(val)
        return (month_index.get(t.upper(), 99), t)

    return sorted(values, key=sort_key)


def _sorted_days(df: pd.DataFrame, column: str = "dia") -> List[Any]:
    """Sort Spanish weekday labels in natural order."""
    if column not in df.columns:
        return []
    values = df[column].dropna().unique().tolist()
    day_index = {d: i for i, d in enumerate(_DAY_ORDER)}

    def sort_key(val):
        t = str(val)
        return (day_index.get(t.upper(), 99), t)

    return sorted(values, key=sort_key)


def _prettify(t: Any) -> str:
    """Replace underscores and apply title formatting."""
    if t is None:
        return ""
    return str(t).replace("_", " ").title()


def _format_choice(v: Any) -> str:
    """Format for selectboxes, keeping 'Totalidad' literal."""
    if v == "Totalidad":
        return "Totalidad"
    return _prettify(v)


# =======================================================================
# MAIN FILTER SYSTEM
# =======================================================================


def render_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Build and apply hierarchical filters for the interactive dashboard.

    Time filters (year, month, weekday) define the temporal scope.
    Crime filters (macro and micro) define the thematic scope.
    Remaining filters (alcaldía, región, periodo, violencia, clima, quincena)
    are computed hierarchically based on the selected temporal and crime scope.
    """
    df_prepared = _ensure_datetime_fecha_hecho(df)
    df_work = df_prepared.copy()

    # ---------------------------------------------------------------
    # 0. Build mapping group → macro for logical synchronization
    # ---------------------------------------------------------------
    macro_by_group: Dict[Any, Any] = {}
    if {"delito_grupo", "delito_grupo_macro"}.issubset(df_work.columns):
        tmp = (
            df_work[["delito_grupo", "delito_grupo_macro"]]
            .dropna()
            .drop_duplicates(subset=["delito_grupo"])
        )
        macro_by_group = dict(zip(tmp["delito_grupo"], tmp["delito_grupo_macro"]))

    # ---------------------------------------------------------------
    # 1. Initialize session_state keys for macro and group selections
    # ---------------------------------------------------------------
    macro_key = "filter_macro_delito_value"
    grupo_key = "filter_grupo_delito_value"

    if macro_key not in st.session_state:
        st.session_state[macro_key] = "Totalidad"
    if grupo_key not in st.session_state:
        st.session_state[grupo_key] = "Totalidad"

    st.sidebar.markdown("## Filtros del dashboard")

    selections: Dict[str, Any] = {}

    # ==================================================================
    # 2. Time filters (year, month, weekday) and temporal scope
    # ==================================================================

    # Ensure a temporary year column and limit to 2016+
    year_range = None
    df_work["anio_tmp"] = (
        df_work["fecha_hecho"].dt.year if "fecha_hecho" in df_work.columns else None
    )

    if "anio_tmp" in df_work.columns:
        df_work = df_work[df_work["anio_tmp"] >= 2016]

        year_opts = (
            df_work["anio_tmp"].dropna().astype(int).sort_values().unique().tolist()
        )
    else:
        year_opts = []

    if year_opts:
        year_range = st.sidebar.select_slider(
            "Año del hecho",
            options=year_opts,
            value=(year_opts[0], year_opts[-1]),
        )
        selections["anio_hecho"] = year_range

    # Month options from current temporal dataset (2016+)
    month_opts = _sorted_months(df_work, "mes_hecho")
    month_range = None
    if month_opts:
        month_range = st.sidebar.select_slider(
            DISPLAY_NAMES["mes_hecho"],
            options=month_opts,
            value=(month_opts[0], month_opts[-1]),
        )
        selections["mes_hecho"] = month_range

    # Weekday options from current temporal dataset (2016+)
    day_opts = _sorted_days(df_work, "dia")
    day_range = None
    if day_opts:
        day_range = st.sidebar.select_slider(
            DISPLAY_NAMES["dia"],
            options=day_opts,
            value=(day_opts[0], day_opts[-1]),
        )
        selections["dia"] = day_range

    # ---------------------------------------------------------------
    # Build temporal scope dataframe for downstream filters
    # ---------------------------------------------------------------
    df_time_scope = df_work.copy()

    # Apply year range
    if year_range and "anio_tmp" in df_time_scope.columns:
        y1, y2 = year_range
        df_time_scope = df_time_scope[
            (df_time_scope["anio_tmp"] >= y1) & (df_time_scope["anio_tmp"] <= y2)
        ]

    # Apply month range
    if month_range and "mes_hecho" in df_time_scope.columns and month_opts:
        m1, m2 = month_range
        i1, i2 = month_opts.index(m1), month_opts.index(m2)
        allowed_months = month_opts[min(i1, i2) : max(i1, i2) + 1]
        df_time_scope = df_time_scope[df_time_scope["mes_hecho"].isin(allowed_months)]

    # Apply weekday range
    if day_range and "dia" in df_time_scope.columns and day_opts:
        d1, d2 = day_range
        i1, i2 = day_opts.index(d1), day_opts.index(d2)
        allowed_days = day_opts[min(i1, i2) : max(i1, i2) + 1]
        df_time_scope = df_time_scope[df_time_scope["dia"].isin(allowed_days)]

    # ==================================================================
    # 3. Crime filters (macro and micro) with callbacks
    # ==================================================================

    # Crime lists are now based on temporal scope (hierarchy by time)
    macro_list = _sorted_unique(df_time_scope, "delito_grupo_macro")
    grupo_all = _sorted_unique(df_time_scope, "delito_grupo")

    def _on_macro_change():
        """
        When macro changes:
        - If macro is 'Totalidad', reset micro filter to 'Totalidad'.
        """
        if st.session_state[macro_key] == "Totalidad":
            st.session_state[grupo_key] = "Totalidad"

    def _on_grupo_change():
        """
        When group changes:
        - If a specific group is chosen and macro is 'Totalidad',
          infer macro from the mapping.
        - If group is 'Totalidad', do not modify macro.
        """
        grupo_val = st.session_state[grupo_key]
        macro_val = st.session_state[macro_key]

        if grupo_val != "Totalidad" and grupo_val in macro_by_group:
            if macro_val == "Totalidad":
                st.session_state[macro_key] = macro_by_group[grupo_val]

    # ------------------------
    # Macro delito picklist
    # ------------------------
    macro_choices = ["Totalidad"] + macro_list
    if st.session_state[macro_key] not in macro_choices:
        st.session_state[macro_key] = "Totalidad"

    macro_value = st.sidebar.selectbox(
        DISPLAY_NAMES["delito_grupo_macro"],
        options=macro_choices,
        key=macro_key,
        format_func=_format_choice,
        on_change=_on_macro_change,
    )
    selections["delito_grupo_macro"] = macro_value

    # ------------------------
    # Micro delito picklist
    # ------------------------
    # Limit groups to temporal scope and macro selection
    macro_value = st.session_state[macro_key]
    if macro_value == "Totalidad":
        grupo_opts = grupo_all
    else:
        df_for_groups = df_time_scope[
            df_time_scope["delito_grupo_macro"] == macro_value
        ]
        grupo_opts = _sorted_unique(df_for_groups, "delito_grupo")

    grupo_choices = ["Totalidad"] + grupo_opts
    if st.session_state[grupo_key] not in grupo_choices:
        st.session_state[grupo_key] = "Totalidad"

    grupo_value = st.sidebar.selectbox(
        DISPLAY_NAMES["delito_grupo"],
        options=grupo_choices,
        key=grupo_key,
        format_func=_format_choice,
        on_change=_on_grupo_change,
    )
    selections["delito_grupo"] = grupo_value

    # ==================================================================
    # 4. Build crime+time scope for remaining hierarchical filters
    # ==================================================================
    df_scope = df_time_scope.copy()

    if macro_value != "Totalidad" and "delito_grupo_macro" in df_scope.columns:
        df_scope = df_scope[df_scope["delito_grupo_macro"] == macro_value]

    if grupo_value != "Totalidad" and "delito_grupo" in df_scope.columns:
        df_scope = df_scope[df_scope["delito_grupo"] == grupo_value]

    # ==================================================================
    # 5. Remaining filters (hierarchical on temporal + crime scope)
    # ==================================================================

    # Alcaldía
    alcaldia_choices = ["Totalidad"] + _sorted_unique(df_scope, "alcaldia_hecho")
    alcaldia_val = st.sidebar.selectbox(
        DISPLAY_NAMES["alcaldia_hecho"],
        alcaldia_choices,
        format_func=_format_choice,
        key="filter_alcaldia",
    )
    selections["alcaldia_hecho"] = alcaldia_val

    # Región
    region_choices = ["Totalidad"] + _sorted_unique(df_scope, "region_cdmx")
    region_val = st.sidebar.selectbox(
        DISPLAY_NAMES["region_cdmx"],
        region_choices,
        format_func=_format_choice,
        key="filter_region",
    )
    selections["region_cdmx"] = region_val

    # Periodo del día
    per_choices = ["Totalidad"] + _sorted_unique(df_scope, "periodo_hora")
    per_val = st.sidebar.selectbox(
        DISPLAY_NAMES["periodo_hora"],
        per_choices,
        format_func=_format_choice,
        key="filter_periodo",
    )
    selections["periodo_hora"] = per_val

    # Tipo de violencia
    vio_choices = ["Totalidad"] + _sorted_unique(df_scope, "clase_violencia")
    vio_val = st.sidebar.selectbox(
        DISPLAY_NAMES["clase_violencia"],
        vio_choices,
        format_func=_format_choice,
        key="filter_violencia",
    )
    selections["clase_violencia"] = vio_val

    # Condición climática
    clima_choices = ["Totalidad"] + _sorted_unique(df_scope, "clima_condicion")
    clima_val = st.sidebar.selectbox(
        DISPLAY_NAMES["clima_condicion"],
        clima_choices,
        format_func=_format_choice,
        key="filter_clima",
    )
    selections["clima_condicion"] = clima_val

    # Ventana de quincena
    quin_choices = ["Totalidad"] + _sorted_unique(df_scope, "quincena")
    quin_val = st.sidebar.selectbox(
        DISPLAY_NAMES["quincena"],
        quin_choices,
        format_func=_format_choice,
        key="filter_quincena",
    )
    selections["quincena"] = quin_val

    # ==================================================================
    # 6. Apply all filters to original working dataframe
    # ==================================================================
    df_final = df_work.copy()

    # Year
    if year_range and "anio_tmp" in df_final.columns:
        y1, y2 = year_range
        df_final = df_final[(df_final["anio_tmp"] >= y1) & (df_final["anio_tmp"] <= y2)]

    # Month
    if month_range and "mes_hecho" in df_final.columns and month_opts:
        m1, m2 = month_range
        i1, i2 = month_opts.index(m1), month_opts.index(m2)
        allowed_months = month_opts[min(i1, i2) : max(i1, i2) + 1]
        df_final = df_final[df_final["mes_hecho"].isin(allowed_months)]

    # Weekday
    if day_range and "dia" in df_final.columns and day_opts:
        d1, d2 = day_range
        i1, i2 = day_opts.index(d1), day_opts.index(d2)
        allowed_days = day_opts[min(i1, i2) : max(i1, i2) + 1]
        df_final = df_final[df_final["dia"].isin(allowed_days)]

    # Macro
    if macro_value != "Totalidad" and "delito_grupo_macro" in df_final.columns:
        df_final = df_final[df_final["delito_grupo_macro"] == macro_value]

    # Micro
    if grupo_value != "Totalidad" and "delito_grupo" in df_final.columns:
        df_final = df_final[df_final["delito_grupo"] == grupo_value]

    # Alcaldía
    if alcaldia_val != "Totalidad" and "alcaldia_hecho" in df_final.columns:
        df_final = df_final[df_final["alcaldia_hecho"] == alcaldia_val]

    # Región
    if region_val != "Totalidad" and "region_cdmx" in df_final.columns:
        df_final = df_final[df_final["region_cdmx"] == region_val]

    # Periodo del día
    if per_val != "Totalidad" and "periodo_hora" in df_final.columns:
        df_final = df_final[df_final["periodo_hora"] == per_val]

    # Tipo de violencia
    if vio_val != "Totalidad" and "clase_violencia" in df_final.columns:
        df_final = df_final[df_final["clase_violencia"] == vio_val]

    # Condición climática
    if clima_val != "Totalidad" and "clima_condicion" in df_final.columns:
        df_final = df_final[df_final["clima_condicion"] == clima_val]

    # Quincena
    if quin_val != "Totalidad" and "quincena" in df_final.columns:
        df_final = df_final[df_final["quincena"] == quin_val]

    return df_final, selections
