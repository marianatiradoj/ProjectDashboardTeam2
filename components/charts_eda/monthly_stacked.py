# components/charts_eda/monthly_stacked.py
from typing import Optional, Tuple, List

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from .base import (
    PALETTE,
    MONTH_COL,          # normalmente "mes_hecho"
    DELITO_MACRO_COL,   # normalmente "delito_grupo_macro"
    apply_common_filters,
)


# Orden “bonito” de meses en español; usaremos sólo los que existan en el df
MESES_ORDENADOS: List[str] = [
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


def render_monthly_stacked_percent(
    df: pd.DataFrame,
    hour_range: Optional[Tuple[int, int]],
    mes: str,
    dia_semana: str,
    zona: str,
    tipos_crimen: Optional[list],
) -> None:
    """
    Barras apiladas: porcentaje de cada delito_grupo_macro dentro de cada mes.

    - Respeta los mismos filtros globales (hora, mes, día, zona, tipos_crimen).
    - Si 'mes' = "Todos", usa todos los meses.
    - Si no hay datos, muestra un mensaje amigable.
    """

    # 1) Aplicar filtros comunes (misma función que usan las otras gráficas)
    df_f = apply_common_filters(
        df,
        hour_range=hour_range,
        mes=mes,
        dia_semana=dia_semana,
        zona=zona,
        tipos_crimen=tipos_crimen,
    )

    if df_f.empty or MONTH_COL not in df_f.columns or DELITO_MACRO_COL not in df_f.columns:
        st.info("No hay datos para los filtros seleccionados (barras apiladas mensuales).")
        return

    # 2) Agrupar por mes y tipo de delito
    grouped = (
        df_f.groupby([MONTH_COL, DELITO_MACRO_COL])
        .size()
        .reset_index(name="conteo")
    )

    if grouped["conteo"].sum() == 0:
        st.info("No hay datos para los filtros seleccionados (barras apiladas mensuales).")
        return

    # 3) Calcular porcentaje dentro de cada mes
    grouped["total_mes"] = grouped.groupby(MONTH_COL)["conteo"].transform("sum")
    grouped["porcentaje"] = grouped["conteo"] / grouped["total_mes"] * 100

    # 4) Pivotear a tabla ancho: filas = mes, columnas = delito_grupo_macro
    pivot = (
        grouped
        .pivot(index=MONTH_COL, columns=DELITO_MACRO_COL, values="porcentaje")
        .fillna(0.0)
    )

    # 5) Ordenar meses de forma lógica (sólo los que existan en el df)
    meses_presentes = [m for m in MESES_ORDENADOS if m in pivot.index]
    if meses_presentes:
        pivot = pivot.loc[meses_presentes]
    else:
        # fallback: orden alfabético
        pivot = pivot.sort_index()

    if pivot.empty:
        st.info("No hay datos para los filtros seleccionados (barras apiladas mensuales).")
        return

    # 6) Construir la gráfica de barras apiladas
    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=150)
    fig.patch.set_facecolor(PALETTE["bg_fig"])
    ax.set_facecolor(PALETTE["bg_axes"])

    # Paleta para cada categoría de delito
    base_colors = [
        PALETTE["bar_light"],
        PALETTE["bar_main"],
        PALETTE["bar_dark"],
        "#1E3A8A",
        "#1D4ED8",
        "#60A5FA",
        "#93C5FD",
    ]
    n_cols = len(pivot.columns)
    colors = (base_colors * ((n_cols // len(base_colors)) + 1))[:n_cols]

    bottom = None
    for idx, (col, color) in enumerate(zip(pivot.columns, colors)):
        values = pivot[col].values
        if idx == 0:
            bottom = None
        ax.bar(
            pivot.index,
            values,
            bottom=bottom,
            label=col,
            color=color,
            edgecolor="white",
            linewidth=0.6,
        )
        if bottom is None:
            bottom = values
        else:
            bottom = bottom + values

    # 7) Estética
    ax.set_ylim(0, 100)
    ax.set_ylabel("Porcentaje dentro de cada mes (%)", color=PALETTE["text"], fontsize=10)
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=35, labelsize=9, colors=PALETTE["text"])
    ax.tick_params(axis="y", labelsize=9, colors=PALETTE["text"])

    ax.yaxis.grid(True, linestyle="--", linewidth=0.4, color=PALETTE["grid"], alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(PALETTE["grid"])
        spine.set_linewidth(0.7)

    # Leyenda fuera, estilo dashboard
    ax.legend(
        title="Grupo de delito",
        fontsize=8,
        title_fontsize=9,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        frameon=False,
    )

    st.pyplot(fig, clear_figure=True)
