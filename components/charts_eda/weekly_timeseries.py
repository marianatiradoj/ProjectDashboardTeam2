# components/charts_eda/weekly_timeseries.py
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

# Orden fijo de días de la semana (en inglés, como viene en tu base)
WEEKDAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _filter_data_for_weekly(
    df: pd.DataFrame,
    hour_range: tuple[int, int] | None,
    mes: str,
    alcaldia: str,
    tipos_crimen: list[str] | None = None,
) -> pd.DataFrame:
    """Filtros para la serie semanal (hora, mes, alcaldía, tipo de crimen)."""
    mask = pd.Series(True, index=df.index)

    # Hora
    if hour_range is not None and HORA_COL in df.columns:
        h_min, h_max = hour_range
        mask &= df[HORA_COL].between(h_min, h_max, inclusive="both")

    # Mes
    if mes != "Todos" and MES_COL in df.columns:
        mask &= df[MES_COL] == mes

    # Alcaldía (zona)
    if alcaldia != "Todas" and ZONA_COL in df.columns:
        mask &= df[ZONA_COL] == alcaldia

    # Tipo(s) de crimen — solo si el usuario seleccionó algo
    if tipos_crimen:
        if DELITO_COL in df.columns:
            mask &= df[DELITO_COL].isin(tipos_crimen)

    return df[mask]


def render_weekly_timeseries(
    hour_range: tuple[int, int] | None,
    mes: str,
    alcaldia: str,
    tipos_crimen: list[str] | None = None,
):
    """
    Serie temporal por día de la semana.
    - X: Monday..Sunday
    - Y: número de incidentes
    - Una línea por tipo de crimen seleccionado (si no hay selección, línea total).
    """
    df = load_crime_data()

    if DIA_SEMANA_COL not in df.columns:
        st.error("No encontré la columna 'weekday' en el dataset.")
        return

    df_f = _filter_data_for_weekly(df, hour_range, mes, alcaldia, tipos_crimen)

    df_f = df_f.dropna(subset=[DIA_SEMANA_COL]).copy()
    if df_f.empty:
        st.info("No hay datos para los filtros seleccionados (serie semanal).")
        return

    # Aseguramos orden de días
    df_f[DIA_SEMANA_COL] = pd.Categorical(
        df_f[DIA_SEMANA_COL],
        categories=WEEKDAY_ORDER,
        ordered=True,
    )

    # == Agrupación ==
    if tipos_crimen:  # una línea por tipo de crimen seleccionado
        grouped = (
            df_f.groupby([DIA_SEMANA_COL, DELITO_COL])
            .size()
            .reset_index(name="conteo")
        )

        # Pivot -> filas = weekday, columnas = delito, valores = conteo
        pivot = grouped.pivot_table(
            index=DIA_SEMANA_COL,
            columns=DELITO_COL,
            values="conteo",
            fill_value=0,
        ).sort_index()
    else:
        # Sin selección de tipo de crimen: una sola serie con el total
        grouped = (
            df_f.groupby(DIA_SEMANA_COL)
            .size()
            .reindex(WEEKDAY_ORDER)
            .fillna(0)
        )
        pivot = pd.DataFrame({"Todos los delitos": grouped})

    if pivot.empty:
        st.info("No hay suficientes datos para construir la serie semanal.")
        return

    # ================== PLOT ==================
    fig, ax = plt.subplots(figsize=(9, 4))

    # Paleta de líneas (todas en tonos azules/teal)
    palette = [
        "#60A5FA",
        "#38BDF8",
        "#22D3EE",
        "#818CF8",
        "#A5B4FC",
        "#7DD3FC",
        "#0EA5E9",
    ]

    x = range(len(pivot.index))

    for i, col in enumerate(pivot.columns):
        y = pivot[col].values
        color = palette[i % len(palette)]
        ax.plot(
            x,
            y,
            marker="o",
            linewidth=2,
            color=color,
            label=str(col),
        )

    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, color="#E5E7EB")

    ax.set_xlabel("Día de la semana", color="#E5E7EB")
    ax.set_ylabel("Número de incidentes", color="#E5E7EB")
    ax.set_title(
        "Serie semanal de delitos por día",
        fontsize=12,
        color="#E5E7EB",
        pad=10,
    )

    # Fondo oscuro y estilo
    ax.set_facecolor("#020617")
    fig.patch.set_alpha(0)
    ax.tick_params(colors="#E5E7EB")
    for spine in ax.spines.values():
        spine.set_color("#1F2937")

    ax.grid(axis="y", alpha=0.25, color="#475569")

    # Leyenda
    ax.legend(
        title="Tipo de delito" if tipos_crimen else None,
        facecolor="#020617",
        edgecolor="#1F2937",
        labelcolor="#E5E7EB",
        fontsize=8,
        title_fontsize=9,
    )

    st.pyplot(fig, clear_figure=True)
