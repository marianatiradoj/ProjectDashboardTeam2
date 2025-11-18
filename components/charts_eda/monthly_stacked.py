# components/charts_eda/monthly_stacked.py
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

# Orden sugerido de meses (por si vienen como texto)
MONTH_ORDER = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _filter_data_for_monthly(
    df: pd.DataFrame,
    hour_range: tuple[int, int] | None,
    mes: str,
    dia_semana: str,
    alcaldia: str,
    tipos_crimen: list[str] | None = None,
) -> pd.DataFrame:
    """Filtros para la barra apilada mensual."""
    mask = pd.Series(True, index=df.index)

    # Hora
    if hour_range is not None and HORA_COL in df.columns:
        h_min, h_max = hour_range
        mask &= df[HORA_COL].between(h_min, h_max, inclusive="both")

    # Mes: aquí respetamos el filtro si NO es "Todos"
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


def render_monthly_stacked_percent(
    hour_range: tuple[int, int] | None,
    mes: str,
    dia_semana: str,
    alcaldia: str,
    tipos_crimen: list[str] | None = None,
    top_n: int = 4,
):
    """
    Gráfica 4:
    Barras 100% apiladas del porcentaje de delitos por mes.
    - X: mes_hecho
    - Y: 100% (composición)
    - Segmentos: grupos de delito (Top N + 'Otros')
    """
    df = load_crime_data()

    if MES_COL not in df.columns or DELITO_COL not in df.columns:
        st.error("Faltan columnas 'mes_hecho' o 'delito_grupo_macro' en el dataset.")
        return

    df_f = _filter_data_for_monthly(df, hour_range, mes, dia_semana, alcaldia, tipos_crimen)

    df_f = df_f.dropna(subset=[MES_COL, DELITO_COL]).copy()
    if df_f.empty:
        st.info("No hay datos para los filtros seleccionados (barras apiladas mensuales).")
        return

    # Normalizamos el orden de meses usando MONTH_ORDER cuando sea posible
    df_f[MES_COL] = pd.Categorical(
        df_f[MES_COL],
        categories=MONTH_ORDER,
        ordered=True,
    )

    # === Top N delitos ===
    total_por_delito = (
        df_f.groupby(DELITO_COL)
        .size()
        .sort_values(ascending=False)
    )

    top_delitos = total_por_delito.head(top_n).index.tolist()

    # Reetiquetar delitos fuera del top como "Otros"
    df_f["delito_simplificado"] = df_f[DELITO_COL].where(
        df_f[DELITO_COL].isin(top_delitos),
        other="Otros",
    )

    # Pivot: filas = mes, columnas = delito_simplificado, valores = conteo
    pivot = (
        df_f.groupby([MES_COL, "delito_simplificado"])
        .size()
        .reset_index(name="conteo")
        .pivot_table(
            index=MES_COL,
            columns="delito_simplificado",
            values="conteo",
            fill_value=0,
        )
        .sort_index(axis=0)
    )

    if pivot.empty:
        st.info("No hay suficientes datos para construir la composición mensual.")
        return

    # Convertir a porcentajes por fila (mes)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # ================== PLOT ==================
    fig, ax = plt.subplots(figsize=(9, 4))

    # Paleta en tonos azules/teal
    palette = [
        "#1E40AF",  # navy
        "#2563EB",  # blue
        "#38BDF8",  # sky
        "#22D3EE",  # cyan
        "#64748B",  # gris-azulado para "Otros"
    ]

    meses = list(pivot_pct.index)
    x = range(len(meses))

    bottom = [0] * len(meses)

    for i, col in enumerate(pivot_pct.columns):
        valores = pivot_pct[col].values
        color = palette[i % len(palette)]
        ax.bar(
            x,
            valores,
            bottom=bottom,
            color=color,
            label=str(col),
            edgecolor="white",
            linewidth=0.6,
        )
        # Actualizar base para el siguiente segmento
        bottom = [b + v for b, v in zip(bottom, valores)]

    ax.set_xticks(x)
    ax.set_xticklabels(meses, rotation=20, ha="right", color="#E5E7EB")

    ax.set_ylabel("Porcentaje (%)", color="#E5E7EB")
    ax.set_xlabel("Mes", color="#E5E7EB")
    ax.set_title(
        "Composición mensual de delitos (Top grupos + Otros)",
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
        title="Grupo de delito",
        facecolor="#020617",
        edgecolor="#1F2937",
        labelcolor="#E5E7EB",
        fontsize=8,
        title_fontsize=9,
        loc="upper right",
    )

    st.pyplot(fig, clear_figure=True)
