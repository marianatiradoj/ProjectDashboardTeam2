# components/charts_eda/hourly_heatmap.py
from __future__ import annotations

from typing import Iterable, Optional, Tuple

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
    mes: Optional[str],
    dia_semana: Optional[str],
    zona: Optional[str],
    tipos_crimen: Optional[Iterable[str]],
) -> None:
    """
    Render weekday vs hour heatmap with global filters.
    """
    # Apply common filters
    df_f = apply_common_filters(
        df,
        hour_range=hour_range,
        mes=mes,
        dia_semana=dia_semana,
        zona=zona,
        tipos_crimen=tipos_crimen,
    )

    if df_f.empty or HOUR_COL not in df_f.columns or DIA_COL not in df_f.columns:
        st.info("No hay datos para los filtros seleccionados (heatmap).")
        return

    # Group by weekday and hour
    grp = df_f.groupby([DIA_COL, HOUR_COL]).size().reset_index(name="conteo")

    if grp.empty:
        st.info("No hay datos para los filtros seleccionados (heatmap).")
        return

    # Pivot table: rows = weekday, columns = hour
    pivot = grp.pivot(
        index=DIA_COL,
        columns=HOUR_COL,
        values="conteo",
    ).fillna(0)

    # Order weekdays
    ordered_days = [d for d in DAY_ORDER if d in pivot.index]
    pivot = pivot.loc[ordered_days]

    # Limit columns to selected hour range
    if hour_range is not None:
        h0, h1 = hour_range
        cols = [h for h in range(h0, h1 + 1)]
        pivot = pivot.reindex(columns=cols, fill_value=0)
    else:
        cols = sorted(pivot.columns)
        pivot = pivot[cols]

    if pivot.empty:
        st.info("No hay datos para los filtros seleccionados (heatmap).")
        return

    # Build figure
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=150)
    fig.patch.set_facecolor(PALETTE["bg_fig"])
    ax.set_facecolor(PALETTE["bg_axes"])

    data = pivot.values

    im = ax.imshow(
        data,
        aspect="auto",
        cmap="Blues",
        origin="upper",
    )

    # Title and axes
    ax.set_title(
        "Mapa de Calor Horario – Delitos por día y hora",
        fontsize=13,
        color=PALETTE["text"],
        pad=10,
    )

    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=11, color=PALETTE["text"])

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=9, rotation=35, color=PALETTE["text"])

    ax.set_xlabel("Hora del día", fontsize=12, color=PALETTE["text"])
    ax.set_ylabel("Día de la semana", fontsize=12, color=PALETTE["text"])

    for spine in ax.spines.values():
        spine.set_color(PALETTE["grid"])
        spine.set_linewidth(0.6)

    # Colorbar
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Número de delitos", fontsize=11, color=PALETTE["text"])
    cbar.ax.tick_params(labelsize=9, colors=PALETTE["text"])

    st.pyplot(fig, clear_figure=True)
