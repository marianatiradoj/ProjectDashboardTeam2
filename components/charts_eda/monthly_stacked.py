# components/charts_eda/monthly_stacked.py
from __future__ import annotations

from typing import Iterable, Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import unicodedata

from .base import (
    PALETTE,
    DELITO_MACRO_COL,
    MONTH_COL,
    apply_common_filters,
)


# Mapeo robusto: cualquier variante --> mes oficial
MONTH_MAP = {
    "enero": "ENERO",
    "febrero": "FEBRERO",
    "marzo": "MARZO",
    "abril": "ABRIL",
    "mayo": "MAYO",
    "junio": "JUNIO",
    "julio": "JULIO",
    "agosto": "AGOSTO",
    "septiembre": "SEPTIEMBRE",
    "setiembre": "SEPTIEMBRE",   
    "octubre": "OCTUBRE",
    "noviembre": "NOVIEMBRE",
    "diciembre": "DICIEMBRE",
}

MONTH_ORDER = list(MONTH_MAP.values())


def normalize_month(m: str) -> str:
    """Convierte texto de mes en forma estándar ENERO–DICIEMBRE."""
    if not isinstance(m, str):
        return m

    # quitar acentos y lowercase
    m_clean = unicodedata.normalize("NFKD", m).encode("ascii", "ignore").decode("utf-8")
    m_clean = m_clean.lower().strip()

    return MONTH_MAP.get(m_clean, m)  # si no coincide, lo deja igual


def render_monthly_stacked_percent(
    df: pd.DataFrame,
    hour_range: Optional[Tuple[int, int]],
    mes: Optional[str],
    zona: Optional[str],
    tipos_crimen: Optional[Iterable[str]],
) -> None:

    df_f = apply_common_filters(
        df,
        hour_range=hour_range,
        mes="Todos",
        dia_semana=None,
        zona=zona,
        tipos_crimen=tipos_crimen,
    )

    if df_f.empty:
        st.info("No hay datos para los filtros seleccionados (barras apiladas mensuales).")
        return

    if MONTH_COL not in df_f.columns or DELITO_MACRO_COL not in df_f.columns:
        st.info("Faltan columnas necesarias para la composición mensual.")
        return

    # Normalizar nombres de meses
    df_f[MONTH_COL] = df_f[MONTH_COL].astype(str).apply(normalize_month)

    grp = (
        df_f.groupby([MONTH_COL, DELITO_MACRO_COL])
        .size()
        .reset_index(name="conteo")
    )

    if grp.empty:
        st.info("No hay datos para los filtros seleccionados (barras apiladas mensuales).")
        return

    grp["total_mes"] = grp.groupby(MONTH_COL)["conteo"].transform("sum")
    grp["porcentaje"] = grp["conteo"] / grp["total_mes"] * 100

    pivot = grp.pivot(index=MONTH_COL, columns=DELITO_MACRO_COL, values="porcentaje").fillna(0)

    # ORDEN REAL
    ordered = [m for m in MONTH_ORDER if m in pivot.index]
    pivot = pivot.loc[ordered]

    fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
    fig.patch.set_facecolor(PALETTE["bg_fig"])
    ax.set_facecolor(PALETTE["bg_axes"])

    color_cycle = [
        PALETTE["bar_light"],
        PALETTE["bar_main"],
        PALETTE["bar_dark"],
        "#3B82F6",
        "#60A5FA",
        "#93C5FD",
        "#1D4ED8",
    ]

    bottom = pd.Series(0, index=pivot.index, dtype=float)

    for i, delito in enumerate(pivot.columns):
        vals = pivot[delito]
        ax.bar(
            pivot.index,
            vals,
            bottom=bottom,
            label=delito,
            color=color_cycle[i % len(color_cycle)],
            edgecolor="#020617",
            linewidth=0.3,
        )
        bottom += vals

    ax.set_ylim(0, 100)
    ax.set_ylabel("Porcentaje dentro de cada mes (%)", fontsize=20, color=PALETTE["text"])
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=60, labelsize=18, colors=PALETTE["text"])
    ax.tick_params(axis="y", labelsize=20, colors=PALETTE["text"])
    ax.yaxis.grid(True, linestyle="--", linewidth=0.5, color=PALETTE["grid"], alpha=0.6)

    for spine in ax.spines.values():
        spine.set_color(PALETTE["grid"])
        spine.set_linewidth(0.8)

    leg = ax.legend(
        title="Grupo de delito",
        title_fontsize=11,
        fontsize=10,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.25),
        ncol=3,
        frameon=False,
    )

    for text in leg.get_texts():
        text.set_color(PALETTE["text"])
    leg.get_title().set_color(PALETTE["text"])

    st.pyplot(fig, clear_figure=True)
