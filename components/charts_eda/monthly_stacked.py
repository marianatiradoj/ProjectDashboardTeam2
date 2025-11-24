# components/charts_eda/monthly_stacked.py
from __future__ import annotations

from typing import Iterable, Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from .base import (
    PALETTE,
    DELITO_MACRO_COL,
    apply_common_filters,
)

# Nombre real de la columna de mes en tu base
MONTH_COL = "mes_hecho"

# Orden deseado de meses en español (usamos esto SOLO si coincide)
MONTH_ORDER_CANON = [
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


def _normalize_month_label(m: str) -> str:
    """Normaliza mínimamente el texto de mes para intentar matchear con MONTH_ORDER_CANON."""
    if not isinstance(m, str):
        return str(m)
    return m.strip().upper()


def render_monthly_stacked_percent(
    df: pd.DataFrame,
    hour_range: Optional[Tuple[int, int]],
    mes: Optional[str],          # se ignora para esta gráfica (porque mostramos TODOS los meses)
    zona: Optional[str],
    tipos_crimen: Optional[Iterable[str]],
) -> None:
    """
    Barras apiladas: composición porcentual de delitos por mes.
    - Eje X: meses (ENERO, FEBRERO, ...)
    - Eje Y: porcentaje (0–100)
    - Colores: grupos de delito (delito_grupo_macro)
    """

    # Para esta gráfica queremos SIEMPRE todos los meses,
    # así que forzamos mes="Todos" al llamar a los filtros comunes.
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

    # Normalizamos una copia de la columna de mes para ordenar mejor
    df_f = df_f.copy()
    df_f["_mes_norm"] = df_f[MONTH_COL].map(_normalize_month_label)

    # ----------------- AGRUPAR -----------------
    grp = (
        df_f.groupby(["_mes_norm", DELITO_MACRO_COL])
        .size()
        .reset_index(name="conteo")
    )

    if grp.empty:
        st.info("No hay datos para los filtros seleccionados (barras apiladas mensuales).")
        return

    # porcentaje dentro de cada mes
    grp["total_mes"] = grp.groupby("_mes_norm")["conteo"].transform("sum")
    grp["porcentaje"] = grp["conteo"] / grp["total_mes"] * 100

    # tabla dinámica: filas = mes, columnas = tipo de delito, valores = %
    pivot = grp.pivot(
        index="_mes_norm",
        columns=DELITO_MACRO_COL,
        values="porcentaje",
    ).fillna(0)

    if pivot.empty:
        st.info("No hay datos para los filtros seleccionados (barras apiladas mensuales).")
        return

    # -------- ORDEN DE MESES ROBUSTO --------
    # Intentamos respetar MONTH_ORDER_CANON, pero si no matchea, usamos el orden de los datos.
    index_norm = list(pivot.index)
    canon_norm = MONTH_ORDER_CANON

    ordered_norm = [m for m in canon_norm if m in index_norm]
    # añadimos cualquier mes "raro" que no esté en la lista canónica
    ordered_norm += [m for m in index_norm if m not in ordered_norm]

    pivot = pivot.loc[ordered_norm]

    delitos = list(pivot.columns)

    # ----------------- FIGURA -----------------
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=150)
    fig.patch.set_facecolor(PALETTE["bg_fig"])
    ax.set_facecolor(PALETTE["bg_axes"])

    # paleta extendida (variaciones de azul)
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

    for i, delito in enumerate(delitos):
        vals = pivot[delito]
        color = color_cycle[i % len(color_cycle)]
        ax.bar(
            pivot.index,
            vals,
            bottom=bottom,
            label=delito,
            color=color,
            edgecolor="#020617",
            linewidth=0.3,
        )
        bottom += vals

    # ----------------- ESTÉTICA -----------------
    ax.set_ylim(0, 100)
    ax.set_ylabel("Porcentaje dentro de cada mes (%)", fontsize=10, color=PALETTE["text"])
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=35, labelsize=8, colors=PALETTE["text"])
    ax.tick_params(axis="y", labelsize=9, colors=PALETTE["text"])

    ax.yaxis.grid(True, linestyle="--", linewidth=0.4, color=PALETTE["grid"], alpha=0.7)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_color(PALETTE["grid"])
        spine.set_linewidth(0.7)

    # Leyenda compacta a la derecha
    ax.legend(
        title="Grupo de delito",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=False,
        fontsize=8,
        title_fontsize=9,
    )

    st.pyplot(fig, clear_figure=True)
