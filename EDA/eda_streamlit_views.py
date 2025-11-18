# EDA/eda_streamlit_views.py
# Dashboard EDA incremental – vistas en Streamlit

from typing import Dict

import pandas as pd
import streamlit as st
import plotly.express as px

# ===================================================
# 1. Estilo visual (sin alterar el tema global)
# ===================================================


def inject_dashboard_css():
    """
    Estilo para tarjetas KPI y tablas.
    No tocamos el fondo global de la app (usamos el tema oscuro de Streamlit).
    """
    st.markdown(
        """
        <style>
        .metric-card {
            padding: 0.75rem 1rem;
            border-radius: 0.75rem;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(148,163,184,0.45);
            box-shadow: 0 18px 40px rgba(15,23,42,0.75);
        }
        .metric-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: .14em;
            color: #9ca3af;
            margin-bottom: 0.2rem;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 600;
            color: #f9fafb;
        }
        .metric-sub {
            font-size: 0.8rem;
            color: #e5e7eb;
            opacity: .90;
        }

        h3, h4 {
            color: #e5e7eb;
        }

        .stDataFrame {
            border-radius: 0.5rem;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title: str, value: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{title}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===================================================
# 2. Nombres formales de columnas
# ===================================================

PRETTY_LABELS = {
    "delito_grupo_macro": "Macrogrupo de delito",
    "region_cdmx": "Región de la Ciudad de México",
    "alcaldia_hecho": "Alcaldía de ocurrencia",
    "fecha_hecho": "Fecha del incidente",
    "periodo_hora": "Periodo del día",
}


def pretty_col(col: str) -> str:
    if col in PRETTY_LABELS:
        return PRETTY_LABELS[col]
    return col.replace("_", " ").capitalize()


# ===================================================
# 3. KPIs y tabla de nulos
# ===================================================


def _kpi_calidad_datos(df: pd.DataFrame, stats: Dict):
    """
    KPIs de calidad de datos + tabla de columnas con más nulos.
    """
    n_rows, n_cols = df.shape
    total_cells = n_rows * n_cols
    n_missing_cells = int(df.isna().sum().sum())
    pct_missing = (n_missing_cells / total_cells * 100) if total_cells else 0

    empty_cols_mask = df.isna().all()
    n_empty_cols = int(empty_cols_mask.sum())

    missing_by_col = df.isna().sum().sort_values(ascending=False)
    top_col = missing_by_col.index[0] if not missing_by_col.empty else "N/D"
    top_col_n = int(missing_by_col.iloc[0]) if not missing_by_col.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Nuevos registros", f"{n_rows:,}", f"{n_cols} columnas")
    with c2:
        metric_card(
            "Celdas vacías", f"{n_missing_cells:,}", f"{pct_missing:.2f}% del lote"
        )
    with c3:
        metric_card("Columnas vacías", f"{n_empty_cols:,}", "Todas las filas son nulas")
    with c4:
        metric_card(
            "Variable con más valores faltantes",
            pretty_col(top_col),
            f"{top_col_n:,} valores nulos",
        )

    # --- Tabla de columnas con más nulos ---

    missing_df = stats.get("missing_top20", None)

    if isinstance(missing_df, pd.DataFrame) and not missing_df.empty:
        tabla = missing_df.copy()
        tabla = tabla.reset_index()
        col_names = list(tabla.columns)

        rename_map = {}
        if len(col_names) >= 1:
            rename_map[col_names[0]] = "columna"
        if len(col_names) >= 2:
            rename_map[col_names[1]] = "n_nulos"
        if len(col_names) >= 3:
            rename_map[col_names[2]] = "porcentaje"

        tabla = tabla.rename(columns=rename_map)
    else:
        tabla = (
            df.isna()
            .sum()
            .rename("n_nulos")
            .to_frame()
            .sort_values("n_nulos", ascending=False)
        )
        tabla["porcentaje"] = (tabla["n_nulos"] / max(n_rows, 1) * 100).round(2)
        tabla = tabla.reset_index().rename(columns={"index": "columna"})

    tabla["columna"] = tabla["columna"].astype(str).map(pretty_col)

    st.markdown("**Columnas con mayor cantidad de valores faltantes (lote nuevo)**")
    st.dataframe(tabla.head(15), use_container_width=True)


# ===================================================
# 4. Filtros
# ===================================================


def _aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtros por alcaldía, macrogrupo y región.
    """
    with st.expander("Filtros del dashboard", expanded=False):
        col1, col2, col3 = st.columns(3)

        if "alcaldia_hecho" in df.columns:
            alc_opts = sorted(df["alcaldia_hecho"].dropna().unique().tolist())
            sel_alc = col1.multiselect(
                "Alcaldía de ocurrencia",
                options=alc_opts,
                default=alc_opts,
            )
        else:
            sel_alc = None

        if "delito_grupo_macro" in df.columns:
            macro_opts = sorted(df["delito_grupo_macro"].dropna().unique().tolist())
            sel_macro = col2.multiselect(
                "Macrogrupo de delito",
                options=macro_opts,
                default=macro_opts,
            )
        else:
            sel_macro = None

        if "region_cdmx" in df.columns:
            reg_opts = sorted(df["region_cdmx"].dropna().unique().tolist())
            sel_reg = col3.multiselect(
                "Región de la Ciudad de México",
                options=reg_opts,
                default=reg_opts,
            )
        else:
            sel_reg = None

    df_f = df.copy()
    if sel_alc:
        df_f = df_f[df_f["alcaldia_hecho"].isin(sel_alc)]
    if sel_macro:
        df_f = df_f[df_f["delito_grupo_macro"].isin(sel_macro)]
    if sel_reg:
        df_f = df_f[df_f["region_cdmx"].isin(sel_reg)]

    return df_f


# ===================================================
# 5. Gráficas con Plotly
# ===================================================

COLOR_SEQ = px.colors.qualitative.Set2  # paleta neutra pero viva


def _grafica_macrogrupo(df: pd.DataFrame):
    if "delito_grupo_macro" not in df.columns:
        st.info("No se encontró la variable de macrogrupo de delito.")
        return

    counts = (
        df["delito_grupo_macro"]
        .value_counts()
        .sort_values(ascending=False)
        .reset_index()
    )
    counts.columns = ["Macrogrupo de delito", "Incidentes"]

    fig = px.bar(
        counts,
        x="Macrogrupo de delito",
        y="Incidentes",
        template="plotly_dark",
        color="Macrogrupo de delito",
        color_discrete_sequence=COLOR_SEQ,
    )
    fig.update_layout(
        title="Incidentes por macrogrupo de delito",
        xaxis_title="Macrogrupo de delito",
        yaxis_title="Número de incidentes",
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
    )
    fig.update_xaxes(tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)


def _grafica_region(df: pd.DataFrame):
    if "region_cdmx" not in df.columns:
        st.info("No se encontró la variable de región de la Ciudad de México.")
        return

    counts = df["region_cdmx"].value_counts().reset_index()
    counts.columns = ["Región de la Ciudad de México", "Incidentes"]

    fig = px.pie(
        counts,
        names="Región de la Ciudad de México",
        values="Incidentes",
        template="plotly_dark",
        color="Región de la Ciudad de México",
        color_discrete_sequence=COLOR_SEQ,
        hole=0.35,
    )
    fig.update_layout(
        title="Distribución de incidentes por región de la Ciudad de México",
        height=360,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafica_categorica_dinamica(df: pd.DataFrame):
    st.markdown("**Distribución por variable categórica (configurable)**")

    candidates = []
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object":
            nunique = df[col].nunique(dropna=True)
            if 2 <= nunique <= 40:
                candidates.append(col)

    if not candidates:
        st.info("No se encontraron variables categóricas adecuadas para graficar.")
        return

    col_sel = st.selectbox(
        "Selecciona la variable categórica",
        options=sorted(candidates),
    )

    top_n = st.slider(
        "Número máximo de categorías (Top N)",
        3,
        30,
        min(10, df[col_sel].nunique(dropna=True)),
    )

    vc = df[col_sel].value_counts(dropna=False).head(top_n).reset_index()
    vc.columns = [pretty_col(col_sel), "Incidentes"]

    fig = px.bar(
        vc,
        x=pretty_col(col_sel),
        y="Incidentes",
        template="plotly_dark",
        color=pretty_col(col_sel),
        color_discrete_sequence=COLOR_SEQ,
    )
    fig.update_layout(
        title=f"Distribución de {pretty_col(col_sel)} (Top {top_n})",
        xaxis_title=pretty_col(col_sel),
        yaxis_title="Número de incidentes",
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
        showlegend=False,
    )
    fig.update_xaxes(tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)


def _grafica_temporal(df: pd.DataFrame):
    if "fecha_hecho" not in df.columns:
        st.info("No se encontró la variable de fecha del incidente.")
        return

    st.markdown("**Serie temporal de incidentes**")

    tmp = df.copy()
    tmp["fecha_hecho"] = pd.to_datetime(tmp["fecha_hecho"], errors="coerce")
    tmp = tmp.dropna(subset=["fecha_hecho"])

    if tmp.empty:
        st.info("No hay fechas válidas para construir la serie temporal.")
        return

    modo = st.selectbox(
        "Agrupación temporal",
        options=["Día", "Mes", "Día de la semana"],
        index=0,
    )

    if modo == "Día":
        serie = (
            tmp.groupby(tmp["fecha_hecho"].dt.date)
            .size()
            .rename("Incidentes")
            .reset_index()
        )
        serie.columns = ["Fecha del incidente", "Incidentes"]

        fig = px.line(
            serie,
            x="Fecha del incidente",
            y="Incidentes",
            template="plotly_dark",
            markers=True,
        )
        fig.update_layout(
            title="Incidentes diarios",
            xaxis_title="Fecha del incidente",
            yaxis_title="Número de incidentes",
            height=360,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    elif modo == "Mes":
        serie = (
            tmp.groupby(tmp["fecha_hecho"].dt.to_period("M"))
            .size()
            .rename("Incidentes")
            .reset_index()
        )
        serie["Mes"] = serie["fecha_hecho"].dt.to_timestamp()
        serie = serie.drop(columns=["fecha_hecho"])

        fig = px.line(
            serie,
            x="Mes",
            y="Incidentes",
            template="plotly_dark",
            markers=True,
        )
        fig.update_layout(
            title="Incidentes mensuales",
            xaxis_title="Mes",
            yaxis_title="Número de incidentes",
            height=360,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        mapa = {
            0: "Lunes",
            1: "Martes",
            2: "Miércoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sábado",
            6: "Domingo",
        }
        serie = (
            tmp.groupby(tmp["fecha_hecho"].dt.dayofweek)
            .size()
            .rename("Incidentes")
            .reindex(range(7), fill_value=0)
            .reset_index()
        )
        serie["index"] = serie["index"].map(mapa)
        serie.columns = ["Día de la semana", "Incidentes"]

        fig = px.bar(
            serie,
            x="Día de la semana",
            y="Incidentes",
            template="plotly_dark",
            color="Día de la semana",
            color_discrete_sequence=COLOR_SEQ,
        )
        fig.update_layout(
            title="Incidentes por día de la semana",
            xaxis_title="Día de la semana",
            yaxis_title="Número de incidentes",
            height=360,
            margin=dict(l=10, r=10, t=40, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ===================================================
# 6. Render principal llamado desde pagina4
# ===================================================


def render_eda_dashboard(
    nuevos_clean: pd.DataFrame,
    combined: pd.DataFrame,
    stats: Dict,
):
    """
    Dashboard principal para el lote nuevo.
    Se pinta entre “Acciones rápidas” y “Vistas detalladas”.
    """
    inject_dashboard_css()

    st.subheader("3) Exploración del lote nuevo (dashboard)")

    # KPIs de calidad de datos
    _kpi_calidad_datos(nuevos_clean, stats)

    # Filtros
    df_f = _aplicar_filtros(nuevos_clean)
    st.caption(
        f"Registros considerados en las gráficas: {len(df_f):,} "
        f"de {len(nuevos_clean):,} registros del lote nuevo."
    )

    st.markdown("---")

    # Layout tipo BI: 2 gráficas arriba, 2 abajo
    col_top_left, col_top_right = st.columns([2, 1.6])
    with col_top_left:
        _grafica_macrogrupo(df_f)
    with col_top_right:
        _grafica_region(df_f)

    st.markdown("---")

    col_bottom_left, col_bottom_right = st.columns(2)
    with col_bottom_left:
        _grafica_categorica_dinamica(df_f)
    with col_bottom_right:
        _grafica_temporal(df_f)
