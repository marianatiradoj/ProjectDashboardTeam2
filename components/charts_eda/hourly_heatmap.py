# components/charts_eda/hourly_heatmap.py
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from .base import (
    PALETTE,
    HOUR_COL,
    DIA_COL,
    DAY_ORDER,
    apply_common_filters,
)


def render_hourly_heatmap(
    df: pd.DataFrame,
    hour_range: Optional[Tuple[int, int]],
    mes: str,
    dia_semana: str,   # lo ignoramos porque el eje ya es día completo
    zona: str,
    tipos_crimen: Optional[List[str]],
):
    """
    Heatmap de número de delitos por (día de la semana, hora).
    Sí respeta tipo de crimen.
    """
    df_f = apply_common_filters(
        df,
        hour_range=hour_range,
        mes=mes,
        dia_semana="Todos",  # eje es toda la semana
        zona=zona,
        tipos_crimen=tipos_crimen,
    )

    if df_f.empty or HOUR_COL not in df_f.columns or DIA_COL not in df_f.columns:
        st.info("No hay datos para los filtros seleccionados (heatmap).")
        return

    # Conteos por día x hora
    table = (
        df_f.groupby([DIA_COL, HOUR_COL])
        .size()
        .reset_index(name="conteo")
    )

    # Reindexar días en orden lógico
    table[DIA_COL] = table[DIA_COL].astype(str).str.upper()
    pivot = (
        table.pivot(index=DIA_COL, columns=HOUR_COL, values="conteo")
        .reindex(index=DAY_ORDER)
        .fillna(0)
    )

    # Asegurarnos de tener columnas 0–23
    hours = list(range(24))
    pivot = pivot.reindex(columns=hours, fill_value=0)

    fig, ax = plt.subplots(figsize=(6, 3.4), dpi=150)
    fig.patch.set_facecolor(PALETTE["bg_fig"])
    ax.set_facecolor(PALETTE["bg_axes"])

    im = ax.imshow(
        pivot.values,
        aspect="auto",
        cmap="Blues",
        origin="upper",
    )

    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels(hours, fontsize=7, rotation=45, color=PALETTE["text"])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9, color=PALETTE["text"])

    ax.set_xlabel("Hora del día", fontsize=9, color=PALETTE["text"])
    ax.set_ylabel("Día de la semana", fontsize=9, color=PALETTE["text"])

    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Número de delitos", fontsize=8, color=PALETTE["text"])
    cbar.ax.tick_params(labelsize=7, colors=PALETTE["text"])

    st.pyplot(fig, clear_figure=True)
