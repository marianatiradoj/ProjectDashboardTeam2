# components/charts_eda/hourly_heatmap.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from .top5_crimes import (
    load_crime_data,
    HORA_COL,
    MES_COL,
    DIA_SEMANA_COL,
    ZONA_COL,
    DELITO_COL,
)

# Orden de los días para el eje Y (en inglés, como viene en tu base)
WEEKDAY_ORDER = [
    "Lunes",
    "Martes",
    "Miercoles",
    "Jueves",
    "Viernes",
    "Sabado",
    "Domingo",
]


def _filter_data_for_heatmap(
    df: pd.DataFrame,
    hour_range: tuple[int, int] | None,
    mes: str,
    dia_semana: str,
    alcaldia: str,
    tipos_crimen: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica filtros para el heatmap (hora, mes, día, alcaldía, tipo de crimen)."""
    mask = pd.Series(True, index=df.index)

    # Hora
    if hour_range is not None and HORA_COL in df.columns:
        h_min, h_max = hour_range
        mask &= df[HORA_COL].between(h_min, h_max, inclusive="both")

    # Mes
    if mes != "Todos" and MES_COL in df.columns:
        mask &= df[MES_COL] == mes

    # Día semana
    if dia_semana != "Todos" and DIA_SEMANA_COL in df.columns:
        mask &= df[DIA_SEMANA_COL] == dia_semana

    # Alcaldía (zona)
    if alcaldia != "Todas" and ZONA_COL in df.columns:
        mask &= df[ZONA_COL] == alcaldia

    # Tipo(s) de crimen — solo si el usuario seleccionó algo
    if tipos_crimen:
        if DELITO_COL in df.columns:
            mask &= df[DELITO_COL].isin(tipos_crimen)

    return df[mask]


def render_hourly_heatmap(
    hour_range: tuple[int, int] | None,
    mes: str,
    dia_semana: str,
    alcaldia: str,
    tipos_crimen: list[str] | None = None,
):
    """
    Heatmap de frecuencia de delitos por hora del día (columnas) y día de la semana (filas),
    usando los mismos filtros que la página.
    """
    df = load_crime_data()

    if HORA_COL not in df.columns or DIA_SEMANA_COL not in df.columns:
        st.error("Faltan columnas 'hora_hecho' o 'weekday' en el dataset.")
        return

    df_f = _filter_data_for_heatmap(df, hour_range, mes, dia_semana, alcaldia, tipos_crimen)

    # Limpiar nulos y asegurar tipos
    df_f = df_f.dropna(subset=[HORA_COL, DIA_SEMANA_COL]).copy()
    if df_f.empty:
        st.info("No hay datos para los filtros seleccionados (heatmap).")
        return

    df_f[HORA_COL] = df_f[HORA_COL].astype(int)

    # Ordenar días de la semana en el orden correcto
    df_f[DIA_SEMANA_COL] = pd.Categorical(
        df_f[DIA_SEMANA_COL],
        categories=WEEKDAY_ORDER,
        ordered=True,
    )

    # Pivot: filas = weekday, columnas = hora, valores = conteo
    pivot = (
        df_f.pivot_table(
            index=DIA_SEMANA_COL,
            columns=HORA_COL,
            values=DELITO_COL,  # cualquier col, solo se usa para contar
            aggfunc="count",
            fill_value=0,
        )
        .sort_index(axis=0)          # orden de weekdays
        .sort_index(axis=1)          # horas 0–23
    )

    if pivot.empty:
        st.info("No hay suficientes datos para construir el heatmap.")
        return

    # ================== PLOT ==================
    fig, ax = plt.subplots(figsize=(9, 4))

    # Blues para mantener coherencia con tu paleta
    im = ax.imshow(pivot.values, aspect="auto", cmap="Blues")

    # Ejes
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, color="#E5E7EB")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, color="#E5E7EB", fontsize=7, rotation=0)

    ax.set_xlabel("Hora del día", color="#E5E7EB")
    ax.set_ylabel("Día de la semana", color="#E5E7EB")
    ax.set_title(
        "Heatmap de delitos por hora y día de la semana",
        color="#E5E7EB",
        fontsize=12,
        pad=10,
    )

    # Fondo oscuro
    ax.set_facecolor("#020617")
    fig.patch.set_alpha(0)
    for spine in ax.spines.values():
        spine.set_color("#1F2937")

    # Colorbar
    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.yaxis.set_tick_params(color="#E5E7EB")
    for label in cbar.ax.get_yticklabels():
        label.set_color("#E5E7EB")
    cbar.set_label("Número de incidentes", color="#E5E7EB")

    st.pyplot(fig, clear_figure=True)
