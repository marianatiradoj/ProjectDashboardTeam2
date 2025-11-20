# components/charts_eda/top5_crimes.py
from typing import Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from .base import (
    PALETTE,
    DELITO_MACRO_COL,
    apply_common_filters,
)


def render_top5_crimes_bar(
    df: pd.DataFrame,
    hour_range: Optional[Tuple[int, int]],
    mes: str,
    dia_semana: str,
    zona: str,
):
    """
    Barplot corporativo TOP 5 de delito_grupo_macro (porcentaje),
    filtrado por hora/mes/día/zona, pero IGNORANDO tipo de crimen.
    """
    df_f = apply_common_filters(
        df,
        hour_range=hour_range,
        mes=mes,
        dia_semana=dia_semana,
        zona=zona,
        tipos_crimen=None,  # 👈 clave: no filtramos por tipo de crimen aquí
    )

    if df_f.empty or DELITO_MACRO_COL not in df_f.columns:
        st.info("No hay datos para los filtros seleccionados (Top 5).")
        return

    counts = (
        df_f[DELITO_MACRO_COL]
        .value_counts(normalize=False)
        .head(5)
        .reset_index()
    )
    counts.columns = [DELITO_MACRO_COL, "conteo"]

    total = counts["conteo"].sum()
    if total == 0:
        st.info("No hay datos para los filtros seleccionados (Top 5).")
        return

    counts["porcentaje"] = counts["conteo"] / total * 100
    st.caption(f"Registros tras filtros (Top 5): {total:,.0f}".replace(",", " "))

    # -------- FIGURA --------
    counts = counts.sort_values("porcentaje", ascending=False)

    fig, ax = plt.subplots(figsize=(6, 3.4), dpi=150)
    fig.patch.set_facecolor(PALETTE["bg_fig"])
    ax.set_facecolor(PALETTE["bg_axes"])

    colors = [
        PALETTE["bar_light"],
        PALETTE["bar_main"],
        PALETTE["bar_dark"],
        "#1E3A8A",
        "#1D4ED8",
    ][: len(counts)]

    bars = ax.bar(
        counts[DELITO_MACRO_COL],
        counts["porcentaje"],
        color=colors,
        edgecolor="white",
        linewidth=0.8,
    )

    for bar, pct in zip(bars, counts["porcentaje"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            f"{pct:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            color=PALETTE["text"],
        )

    ax.set_ylabel("Porcentaje de delitos (%)", fontsize=10, color=PALETTE["text"])
    ax.set_xlabel("")
    ax.tick_params(axis="x", labelrotation=20, labelsize=9, colors=PALETTE["text"])
    ax.tick_params(axis="y", labelsize=9, colors=PALETTE["text"])

    # Grid sutil
    ax.yaxis.grid(True, linestyle="--", linewidth=0.4, color=PALETTE["grid"], alpha=0.7)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_color(PALETTE["grid"])
        spine.set_linewidth(0.7)

    st.pyplot(fig, clear_figure=True)
