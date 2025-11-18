# components/charts_eda/top5_crimes.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# === Columnas reales del CSV ===
DELITO_COL     = "delito_grupo_macro"
HORA_COL       = "hora_hecho"
MES_COL        = "mes_hecho"
DIA_SEMANA_COL = "dia"
ZONA_COL       = "alcaldia_hecho"

# Ruta al CSV (relativa al proyecto)
DATA_PATH = Path("Database") / "FGJ_CLEAN_Final.csv"


@st.cache_data(show_spinner="Cargando base de delitos...")
def load_crime_data() -> pd.DataFrame:
    """Carga el CSV de delitos con cache. Asumimos que la base ya viene limpia."""
    df = pd.read_csv(DATA_PATH)

    # Nos aseguramos de que la hora sea numérica (0–23)
    if HORA_COL in df.columns:
        df[HORA_COL] = pd.to_numeric(df[HORA_COL], errors="coerce").astype("Int64")

    return df


def _filter_data(
    df: pd.DataFrame,
    hour_range: tuple[int, int] | None,
    mes: str,
    dia_semana: str,
    alcaldia: str,
) -> pd.DataFrame:
    """Aplica filtros básicos sobre hora, mes, día y alcaldía."""
    mask = pd.Series(True, index=df.index)

    # Filtro por hora
    if hour_range is not None and HORA_COL in df.columns:
        h_min, h_max = hour_range
        mask &= df[HORA_COL].between(h_min, h_max, inclusive="both")

    # Filtro por mes (si el usuario no eligió 'Todos')
    if mes != "Todos" and MES_COL in df.columns:
        mask &= df[MES_COL] == mes

    # Filtro por día de la semana
    if dia_semana != "Todos" and DIA_SEMANA_COL in df.columns:
        mask &= df[DIA_SEMANA_COL] == dia_semana

    # Filtro por alcaldía (mientras no hay zona)
    if alcaldia != "Todas" and ZONA_COL in df.columns:
        mask &= df[ZONA_COL] == alcaldia

    return df[mask]


def render_top5_crimes_bar(
    hour_range: tuple[int, int] | None,
    mes: str,
    dia_semana: str,
    alcaldia: str,
):
    """
    Renderiza una gráfica de barras con los 5 grupos de delitos más comunes,
    en porcentaje, usando filtros de hora, mes, día y alcaldía.

    Nota: el filtro de tipo de crimen NO se aplica aquí (por diseño).
    """
    df = load_crime_data()

    if DELITO_COL not in df.columns:
        st.error(f"No encontré la columna '{DELITO_COL}' en el CSV.")
        return

    # 1) Filtrar datos
    df_f = _filter_data(df, hour_range, mes, dia_semana, alcaldia)

    if df_f.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return

    # 2) Agrupar y calcular Top 5
    total = len(df_f)

    counts = (
        df_f.groupby(DELITO_COL)
        .size()
        .sort_values(ascending=False)
        .head(5)
        .reset_index(name="conteo")
    )

    if counts.empty:
        st.info("No hay delitos suficientes para mostrar el Top 5.")
        return

    # 3) Calcular porcentaje
    counts["porcentaje"] = (counts["conteo"] / total) * 100

    # 4) Graficar en modo oscuro, tonos azules y contorno blanco suave
    fig, ax = plt.subplots(figsize=(8, 4))

    # Paleta monocromática azul
    colors = [
        "#1E40AF",
        "#2563EB",
        "#3B82F6",
        "#60A5FA",
        "#93C5FD",
    ]
    colors = colors[: len(counts)]

    # --- Crear las barras ---
    rects = ax.bar(counts[DELITO_COL], counts["porcentaje"], color=colors)

    # --- Contorno blanco suave ---
    for r in rects:
        r.set_edgecolor("white")
        r.set_linewidth(0.8)
        r.set_alpha(0.92)

    # --- Etiquetas encima del barplot (% con 1 decimal) ---
    for i, value in enumerate(counts["porcentaje"]):
        ax.text(
            i,
            value + 0.5,
            f"{value:.1f}%",
            ha="center",
            color="#E5E7EB",
            fontsize=10,
        )

    # --- Estilo del gráfico ---
    ax.set_title(
        "Distribución de grupo de delitos (Top 5)",
        fontsize=12,
        color="#E5E7EB",
        pad=10,
    )
    ax.set_ylabel("Porcentaje (%)", color="#E5E7EB")
    ax.set_xlabel("Tipo de delito", color="#E5E7EB")

    ax.set_xticklabels(counts[DELITO_COL], rotation=20, ha="right", color="#E5E7EB")

    # Fondo oscuro y ejes
    ax.set_facecolor("#020617")
    fig.patch.set_alpha(0)
    ax.tick_params(colors="#E5E7EB")
    for spine in ax.spines.values():
        spine.set_color("#1F2937")

    ax.grid(axis="y", alpha=0.25, color="#475569")

    st.pyplot(fig, clear_figure=True)
