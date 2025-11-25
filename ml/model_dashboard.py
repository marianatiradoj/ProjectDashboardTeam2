# ml/model_dashboard.py

import time
from datetime import datetime, timedelta

import streamlit as st
import pydeck as pdk
import altair as alt
import pandas as pd

from ml.model_views import compute_predictions_for_dt
from ml.ml_kpis import get_tipo_options, resolve_prob_column, compute_kpis


# -------------------------------------------------
# Helper: encontrar la columna de colonia
# -------------------------------------------------
def _find_colonia_col(df: pd.DataFrame | None) -> str | None:
    if df is None:
        return None

    candidates = [
        "colonia",
        "COLONIA",
        "colonia_catalogo",
        "COLONIA_CATALOGO",
        "nom_colonia",
        "NOMUT",
    ]
    for c in candidates:
        if c in df.columns:
            return c

    for c in df.columns:
        if "colonia" in str(c).lower():
            return c

    return None


# -------------------------------------------------
# Mapeos a español
# -------------------------------------------------
SPANISH_COL_NAMES = {
    "prob_total": "Total (todos los delitos)",
    "prob_tipo_NON_CRIME_OTHER": "Administrativo",
    "prob_tipo_LOW_IMPACT": "Bajo Impacto",
    "prob_tipo_ROBBERY_PERSON": "Robo Persona",
    "prob_tipo_ROBBERY_PROPERTY": "Robo Propiedad",
    "prob_tipo_LETHAL_VIOLENT": "Violencia Letal",
    "prob_tipo_VIOLENT_OTHER": "Violencia No Letal",
}


def fmt_dec4(x):
    try:
        return float(f"{float(x):.4f}")
    except Exception:
        return x


# -------------------------------------------------
# FUNCIÓN PRINCIPAL DEL DASHBOARD (llamar desde página 1)
# -------------------------------------------------
def run_model_dashboard(bundle) -> None:
    # ================= SIDEBAR ==================
    st.sidebar.header("🎛 Parámetros de predicción")

    fecha = st.sidebar.date_input("Fecha")

    modo_tiempo = st.sidebar.selectbox(
        "Modo de tiempo",
        [
            "Punto en el tiempo",
            "Serie 24 horas",
            "Serie 48 horas",
            "Serie personalizada",
        ],
    )

    dt_inicio = None
    total_steps = 1

    if modo_tiempo == "Punto en el tiempo":
        hora = st.sidebar.time_input("Hora", key="hora_punto")
    else:
        hora_inicio = st.sidebar.time_input("Hora inicial", key="hora_inicio_serie")

        if modo_tiempo == "Serie 24 horas":
            total_steps = 24
        elif modo_tiempo == "Serie 48 horas":
            total_steps = 48
        else:
            total_steps = int(
                st.sidebar.number_input(
                    "Total de horas a simular",
                    min_value=1,
                    max_value=72,
                    value=24,
                    step=1,
                )
            )

        dt_inicio = datetime.combine(fecha, hora_inicio)

    # Filtro de tipo/delito
    tipo_label = st.sidebar.selectbox(
        "Tipo de probabilidad / delito",
        get_tipo_options(),
    )

    # ================= TÍTULO + DESCRIPCIÓN ==================
    st.title("🔮 Panel de predicción de riesgo delictivo por colonia")

    st.markdown(
        """
Este panel muestra la **probabilidad esperada de incidentes delictivos por colonia**  
para una fecha y hora específicas.  

- Los **KPIs** resumen el comportamiento general del riesgo.  
- Los **tacómetros** permiten comparar los macrogrupos de delito.  
- La **tabla y el mapa** muestran, colonia por colonia, cómo se distribuye el riesgo  
  bajo los filtros seleccionados (tiempo, tipo de delito y nivel de riesgo).
        """
    )

    # ================= CONTROL DE TIEMPO ==================
    if modo_tiempo == "Punto en el tiempo":
        dt_actual = datetime.combine(fecha, hora)
    else:
        idx = st.slider(
            "Hora dentro de la serie",
            min_value=0,
            max_value=total_steps - 1,
            value=0,
            key="slider_serie",
        )
        dt_actual = dt_inicio + timedelta(hours=idx)

    # ================= CÁLCULO INICIAL ==================
    with st.spinner("Calculando predicción del modelo..."):
        outputs_initial = compute_predictions_for_dt(
            dt=dt_actual,
            bundle=bundle,
            alcaldias_sel=[],
        )

    df_map_initial = outputs_initial.df_map.copy()
    if df_map_initial is None or df_map_initial.empty:
        st.error("No se pudieron obtener datos del modelo para este instante.")
        return

    colonia_col_map = _find_colonia_col(df_map_initial)

    # ================= FILTROS DINÁMICOS ==================
    risk_filter = st.sidebar.selectbox(
        "Escala de riesgo (nivel global)",
        ["Todos", "Muy bajo", "Bajo", "Medio", "Alto", "Muy alto"],
        index=0,
    )

    if colonia_col_map:
        colonias = sorted(df_map_initial[colonia_col_map].astype(str).unique())
        colonia_busqueda = st.selectbox(
            "Colonia",
            ["Todas las colonias"] + colonias,
            index=0,
        )
    else:
        colonia_busqueda = "Todas las colonias"

    # ================= REPRODUCCIÓN AUTOMÁTICA ==================
    reproducir = False
    velocidad = 0.5
    if modo_tiempo != "Punto en el tiempo":
        velocidad = st.sidebar.slider(
            "Velocidad de reproducción (seg/frame)",
            min_value=0.1,
            max_value=2.0,
            value=0.5,
            step=0.1,
        )
        reproducir = st.sidebar.button("▶ Iniciar reproducción")

    # =====================================================
    # RENDER INTERNO
    # =====================================================
    placeholder = st.empty()

    def render_frame(
        dt: datetime,
        tipo_label: str,
        colonia_busqueda: str,
        risk_filter: str,
        precomputed=None,
    ):
        # ---- obtener datos ----
        if precomputed is None:
            outputs_local = compute_predictions_for_dt(dt, bundle, [])
        else:
            outputs_local = precomputed

        df_map = outputs_local.df_map.copy()
        df_table = outputs_local.df_table.copy()
        col_map = _find_colonia_col(df_map)

        # asegurar lat/lon
        if "lat" not in df_map.columns and "centroid_lat" in df_map.columns:
            df_map["lat"] = df_map["centroid_lat"]
        if "lon" not in df_map.columns and "centroid_lon" in df_map.columns:
            df_map["lon"] = df_map["centroid_lon"]

        # ---- FILTROS ----
        if risk_filter != "Todos" and "risk_label" in df_map.columns:
            df_map = df_map[df_map["risk_label"] == risk_filter]

        if colonia_busqueda != "Todas las colonias" and col_map:
            df_map = df_map[df_map[col_map] == colonia_busqueda]

        if df_map.empty:
            with placeholder.container():
                st.warning("No hay datos después de aplicar los filtros.")
            return

        with placeholder.container():
            # ======================
            # ENCABEZADO: FECHA + HORA
            # ======================
            st.markdown(
                f"""
                <h3 style="margin-top:8px; margin-bottom:4px; color:#e2e8f0;">
                    Predicción para:
                    <span style="color:#38bdf8;">{dt.strftime("%d-%m-%Y %H:%M")}</span>
                </h3>
                """,
                unsafe_allow_html=True,
            )

            # ======================
            # KPIs
            # ======================
            prob_col = resolve_prob_column(tipo_label, df_map)
            kpis = compute_kpis(df_map, prob_col)

            st.markdown(
                f"""
                <div class="kpi-grid-row1">

                  <div class="kpi-card">
                    <div class="kpi-label">Colonias analizadas</div>
                    <div class="kpi-value">{kpis['total_colonias']}</div>
                    <div class="kpi-subtext">
                      {'Colonia: ' + colonia_busqueda if colonia_busqueda != 'Todas las colonias' else 'Todas las colonias'}
                      &nbsp;|&nbsp;
                      {'Riesgo: ' + risk_filter if risk_filter != 'Todos' else 'Todos los riesgos'}
                    </div>
                  </div>

                  <div class="kpi-card alt-1">
                    <div class="kpi-label">Promedio ({tipo_label})</div>
                    <div class="kpi-value">{kpis['mean_prob']:.4f}</div>
                    <div class="kpi-subtext">Promedio de probabilidad en el conjunto filtrado</div>
                  </div>

                  <div class="kpi-card alt-2">
                    <div class="kpi-label">Máximo ({tipo_label})</div>
                    <div class="kpi-value">{kpis['max_prob']:.4f}</div>
                    <div class="kpi-subtext">Valor más alto del conjunto filtrado</div>
                  </div>

                  <div class="kpi-card alt-3">
                    <div class="kpi-label">Colonias riesgo alto/muy alto</div>
                    <div class="kpi-value">{kpis['high_risk_count']}</div>
                    <div class="kpi-subtext">{kpis['high_risk_pct']:.1f}% del conjunto filtrado</div>
                  </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            # =====================================================
            # EXPANDER TACÓMETROS (sin el total)
            # =====================================================
            with st.expander("📊 Ver detalle por tipo de delito (tacómetros)"):
                st.markdown("#### Probabilidad por tipo de delito")

                prob_cols = [
                    "prob_tipo_NON_CRIME_OTHER",
                    "prob_tipo_LOW_IMPACT",
                    "prob_tipo_ROBBERY_PERSON",
                    "prob_tipo_ROBBERY_PROPERTY",
                    "prob_tipo_LETHAL_VIOLENT",
                    "prob_tipo_VIOLENT_OTHER",
                ]
                prob_cols = [c for c in prob_cols if c in df_map.columns]

                gauge_data = []
                if colonia_busqueda == "Todas las colonias":
                    for col in prob_cols:
                        gauge_data.append(
                            {
                                "grupo": SPANISH_COL_NAMES.get(col, col),
                                "prob": float(df_map[col].mean()),
                            }
                        )
                else:
                    row0 = df_map.iloc[0]
                    for col in prob_cols:
                        gauge_data.append(
                            {
                                "grupo": SPANISH_COL_NAMES.get(col, col),
                                "prob": float(row0[col]),
                            }
                        )

                df_g = pd.DataFrame(gauge_data)

                cols_t = st.columns(2)
                for i, row in enumerate(df_g.itertuples()):
                    col_ui = cols_t[i % 2]
                    with col_ui:
                        st.markdown(
                            f"<div style='font-size:1.1rem;font-weight:700;"
                            f"color:#93c5fd;text-align:center;margin-bottom:4px;'>{row.grupo}</div>",
                            unsafe_allow_html=True,
                        )

                        df_seg = pd.DataFrame(
                            {
                                "segment": ["Probabilidad", "Restante"],
                                "value": [row.prob, 1 - row.prob],
                            }
                        )

                        base = (
                            alt.Chart(df_seg)
                            .mark_arc(innerRadius=35, outerRadius=70)
                            .encode(
                                theta=alt.Theta("value:Q"),
                                color=alt.Color(
                                    "segment:N",
                                    scale=alt.Scale(
                                        range=[
                                            "#38bdf8",  # azul claro
                                            "#020617",  # fondo
                                        ]
                                    ),
                                    legend=None,
                                ),
                            )
                            .properties(width=200, height=200)
                        )

                        text1 = (
                            alt.Chart(pd.DataFrame({"t": [f"{row.prob:.2%}"]}))
                            .mark_text(
                                fontSize=22,
                                fontWeight="bold",
                                color="#F9FAFB",
                            )
                            .encode(text="t:N")
                        )

                        text2 = (
                            alt.Chart(pd.DataFrame({"t": [f"{row.prob:.4f}"]}))
                            .mark_text(
                                dy=20,
                                fontSize=11,
                                color="#E5E7EB",
                            )
                            .encode(text="t:N")
                        )

                        st.altair_chart(base + text1 + text2, use_container_width=False)

            # =====================================================
            # TABLA + MAPA (side-by-side)
            # =====================================================
            st.markdown("### 📋 Colonias con probabilidad y mapa de riesgo")

            tabla_col, mapa_col = st.columns([1.1, 1.9])

            # ---------- TABLA ----------
            with tabla_col:
                col_name = SPANISH_COL_NAMES.get(prob_col, prob_col)

                if col_map is None:
                    st.warning("No se identificó la columna de colonia.")
                else:
                    df_show = df_map[[col_map, prob_col]].rename(
                        columns={col_map: "Colonia", prob_col: col_name}
                    )

                    # formato porcentaje
                    df_show[col_name] = df_show[col_name].map(
                        lambda x: f"{float(x) * 100:.2f}%"
                    )

                    styled = df_show.style.set_table_styles(
                        [
                            {
                                "selector": "th",
                                "props": [
                                    ("background-color", "#1e3a8a"),
                                    ("color", "white"),
                                    ("font-size", "16px"),
                                    ("font-weight", "bold"),
                                ],
                            }
                        ]
                    )

                    st.dataframe(
                        styled,
                        hide_index=True,
                        use_container_width=True,
                    )

            # ---------- MAPA ----------
            with mapa_col:
                df_map["proba_mapa"] = df_map[prob_col].clip(0, 1)

                # tamaño según prob
                df_map["size"] = 50 + (df_map["proba_mapa"] ** 2) * 800

                # colores tipo heatmap
                df_map["color_r"] = (df_map["proba_mapa"] * 255).astype(int)
                df_map["color_g"] = (150 - df_map["proba_mapa"] * 150).astype(int)
                df_map["color_b"] = 40

                # 🔍 ZOOM MÁS ABIERTO PARA VER MEJOR LA CIUDAD
                zoom = 11 if colonia_busqueda == "Todas las colonias" else 13

                view = pdk.ViewState(
                    latitude=float(df_map["lat"].mean()),
                    longitude=float(df_map["lon"].mean()),
                    zoom=zoom,
                    pitch=0,
                )

                df_map["prob_pct"] = (df_map["proba_mapa"] * 100).round(2)

                tooltip_html = (
                    "<b>Colonia:</b> {" + (col_map or "colonia") + "}<br>"
                    f"<b>{SPANISH_COL_NAMES.get(prob_col, prob_col)}:</b> {{prob_pct}}%"
                )

                layer = pdk.Layer(
                    "ScatterplotLayer",
                    df_map,
                    get_position="[lon, lat]",
                    get_radius="size",
                    get_fill_color="[color_r, color_g, color_b, 220]",
                    pickable=True,
                    auto_highlight=True,
                )

                deck = pdk.Deck(
                    layers=[layer],
                    initial_view_state=view,
                    tooltip={
                        "html": tooltip_html,
                        "style": {
                            "backgroundColor": "#020617",
                            "color": "#F9FAFB",
                            "fontSize": "12px",
                        },
                    },
                    map_style="mapbox://styles/mapbox/dark-v11",
                )

                st.pydeck_chart(deck, use_container_width=True, height=550)

    # ================= PRIMER FRAME ==================
    render_frame(
        dt_actual,
        tipo_label,
        colonia_busqueda,
        risk_filter,
        precomputed=outputs_initial,
    )

    # ================= REPRODUCCIÓN ==================
    if modo_tiempo != "Punto en el tiempo" and reproducir:
        for step in range(total_steps):
            dt_step = dt_inicio + timedelta(hours=step)
            render_frame(dt_step, tipo_label, colonia_busqueda, risk_filter)
            time.sleep(velocidad)
