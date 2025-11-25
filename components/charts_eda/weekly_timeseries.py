# components/charts_eda/weekly_timeseries.py
from typing import Optional, Tuple, List

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from .base import (
    PALETTE,
    DIA_COL,
    DAY_ORDER,
    apply_common_filters,
)


def render_weekly_timeseries(
    df: pd.DataFrame,
    hour_range: Optional[Tuple[int, int]],
    mes: str,
    zona: str,
    tipos_crimen: Optional[List[str]],
):
    """
    Serie: total de delitos por día de la semana.
    Respeta tipo de crimen, hora, mes y zona.
    """
    df_f = apply_common_filters(
        df,
        hour_range=hour_range,
        mes=mes,
        dia_semana="Todos",
        zona=zona,
        tipos_crimen=tipos_crimen,
    )

    if df_f.empty or DIA_COL not in df_f.columns:
        st.info("No hay datos para los filtros seleccionados (serie semanal).")
        return

    df_f[DIA_COL] = df_f[DIA_COL].astype(str).str.upper()

    counts = (
        df_f.groupby(DIA_COL)
        .size()
        .reindex(DAY_ORDER)
        .fillna(0)
        .reset_index(name="conteo")
    )

    fig, ax = plt.subplots(figsize=(6, 3.4), dpi=150)
    fig.patch.set_facecolor(PALETTE["bg_fig"])
    ax.set_facecolor(PALETTE["bg_axes"])

    ax.plot(
        counts[DIA_COL],
        counts["conteo"],
        marker="o",
        linewidth=2.2,
        markersize=6,
        color=PALETTE["line"],
    )

    for x, y in zip(counts[DIA_COL], counts["conteo"]):
        ax.text(
            x,
            y + counts["conteo"].max() * 0.02,
            f"{int(y):,}".replace(",", " "),
            ha="center",
            va="bottom",
            fontsize=8,
            color=PALETTE["text"],
        )

    ax.set_xlabel("Día de la semana", fontsize=10, color=PALETTE["text"])
    ax.set_ylabel("Número de delitos", fontsize=10, color=PALETTE["text"])
    ax.tick_params(axis="x", labelrotation=20, labelsize=10, colors=PALETTE["text"])
    ax.tick_params(axis="y", labelsize=10, colors=PALETTE["text"])

    ax.yaxis.grid(True, linestyle="--", linewidth=0.4, color=PALETTE["grid"], alpha=0.7)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_color(PALETTE["grid"])
        spine.set_linewidth(0.7)

    st.pyplot(fig, clear_figure=True)
