import os
import sys
import json

import pandas as pd
import streamlit as st

# ===================================================
# 0. ESTILOS: FONDO OSCURO + TEXTO LEGIBLE
# ===================================================
st.markdown(
    """
    <style>
    /* Fondo principal oscuro (igual que página 3) */
    [data-testid="stAppViewContainer"] {
        background-color: #050816 !important;
    }
    [data-testid="stAppViewContainer"] > .main {
        background-color: #050816 !important;
    }

    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #f9fafb !important;
    }

    /* Labels y texto principal en markdown */
    label,
    [data-testid="stMarkdownContainer"] p {
        color: #e5e7eb !important;
    }

    /* Sliders */
    .stSlider label,
    .stSlider span {
        color: #e5e7eb !important;
    }

    /* Checkbox label */
    .stCheckbox label {
        color: #e5e7eb !important;
    }

    /* Inputs de texto (TextInput) */
    .stTextInput > div > div > input {
        background-color: #020617 !important;
        color: #f9fafb !important;
        border: 1px solid #334155 !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #94a3b8 !important;
    }

    /* File uploader */
    .stFileUploader {
        background-color: #020617 !important;
        padding: 0.75rem !important;
        border-radius: 0.75rem !important;
        border: 1px solid #1f2937 !important;
    }

    /* Botones normales */
    .stButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.45rem 0.9rem !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
    }

    /* Tarjetas tipo panel */
    .panel-card {
        background: rgba(15,23,42,0.96);
        border: 1px solid rgba(148,163,184,0.35);
        box-shadow: 0 18px 45px rgba(15,23,42,0.5);
        border-radius: 0.75rem;
        padding: 0.75rem 1rem;
    }

    /* === Botones de descarga (download button) === */
    [data-testid="stDownloadButton"] > button {
        background-color: #1e293b !important;   /* fondo oscuro */
        color: #f8fafc !important;              /* texto blanco */
        border: 1px solid #334155 !important;   /* borde */
        border-radius: 8px !important;
        padding: 0.5rem 1.1rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background-color: #334155 !important;   /* hover */
        color: #ffffff !important;
        border-color: #475569 !important;
    }

    /* === FIX para captions invisibles (st.caption) === */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #d1d5db !important; /* gris claro legible */
        font-weight: 500 !important;
    }
    /* ============================================= */

    </style>
    """,
    unsafe_allow_html=True,
)

# ===================================================
# 1. RUTAS Y MÓDULOS DEL EDA
# ===================================================
THIS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(THIS_DIR)
DB_PATH = os.path.join(ROOT_DIR, "Database", "FGJ_CLEAN_Final.csv")

EDA_DIR = os.path.join(ROOT_DIR, "EDA")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from EDA.eda_pipeline import run_eda_for_upload
from EDA.eda_streamlit_views import render_eda_dashboard

REGEX_JAM_PATH = os.path.join(EDA_DIR, "regex_config.jam")


# ===================================================
# 2. CARGA CACHEADA DE LA BASE MAESTRA
#    → aquí es donde reducimos carga de I/O
# ===================================================
@st.cache_data(show_spinner="Cargando base maestra (FGJ_CLEAN_Final.csv)...")
def load_master_df() -> pd.DataFrame:
    return pd.read_csv(DB_PATH, low_memory=False)


# ===================================================
# 3. PÁGINA 4 – MAIN
# ===================================================
def main():
    st.title("Página 4 – EDA e Integración con Base Maestra")

    # ---------- Base maestra activa (CACHEADA) ----------
    master_df = load_master_df()

    col_info, col_upload = st.columns([2, 3])

    with col_info:
        st.markdown(
            f"""
            <div class="panel-card">
              <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:.14em; color:#9ca3af;">
                Base maestra activa
              </div>
              <div style="font-size:1.3rem; font-weight:600; margin-top:0.25rem; color:#f9fafb;">
                {os.path.basename(DB_PATH)}
              </div>
              <div style="font-size:0.9rem; opacity:0.85; margin-top:0.2rem; color:#e5e7eb;">
                {len(master_df):,} registros · {master_df.shape[1]} columnas
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------- Subida de nuevos registros ----------
    with col_upload:
        st.markdown(
            """
            <div class="panel-card">
              <div style="font-size:0.8rem; text-transform:uppercase; letter-spacing:.14em; color:#9ca3af;">
                Subir nuevos registros
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "Archivo de nuevos registros (.csv o .parquet)",
            type=["csv", "parquet"],
            key="uploader_nuevos",
        )

    # ---------- Parámetros del EDA (informativo/config) ----------
    with st.expander("Parámetros del EDA", expanded=False):
        fecha_col = st.text_input(
            "Columna de fecha del incidente",
            "fecha_hecho",
            help="Nombre de la columna de fecha en el archivo subido.",
        )
        alcaldia_col = st.text_input(
            "Columna de alcaldía de ocurrencia",
            "alcaldia_hecho",
            help="Nombre de la columna de alcaldía en el archivo subido.",
        )
        ventana_quincenal = st.slider(
            "Ventana quincenal (± días)",
            0,
            5,
            2,
            help="Días antes y después considerados como 'ventana de quincena'.",
        )

        usar_clima = st.checkbox("Enriquecer con datos de clima", value=False)
        clima_path = st.text_input(
            "Ruta CSV de clima (opcional)",
            "",
            help="Solo aplica si habilitas la opción de clima.",
        )

    # Por ahora no estamos pasando estos parámetros al pipeline,
    # pero los dejamos listos:
    _ = fecha_col, alcaldia_col, ventana_quincenal

    if uploaded is None:
        st.info("Sube un archivo para ejecutar el EDA e integrarlo a la base maestra.")
        return

    # ===================================================
    # 3.1 Leer el archivo subido (CSV / Parquet)
    # ===================================================
    def _read_any(file) -> pd.DataFrame:
        name = file.name.lower()
        if name.endswith(".csv"):
            return pd.read_csv(file)
        return pd.read_parquet(file)

    try:
        nuevos_raw = _read_any(uploaded)
    except Exception as e:
        st.error(f"Error al leer el archivo subido: {e}")
        return

    st.write(
        f"**Nuevos registros crudos:** {len(nuevos_raw):,} filas · "
        f"{nuevos_raw.shape[1]} columnas"
    )

    if not os.path.exists(REGEX_JAM_PATH):
        st.error(f"No se encontró el archivo de patrones: `{REGEX_JAM_PATH}`.")
        return

    clima_csv = None
    if usar_clima:
        p = clima_path.strip()
        if p and os.path.exists(p):
            clima_csv = p
        elif p:
            st.warning(
                f"No se encontró el archivo de clima en la ruta: `{p}`. "
                "Se continuará sin enriquecer con clima."
            )

    # ===================================================
    # 3.2 Ejecutar EDA sobre el lote nuevo
    #    → run_eda_for_upload está separado en EDA/eda_pipeline.py
    # ===================================================
    with st.spinner("Ejecutando EDA sobre los nuevos registros..."):
        nuevos_clean, stats = run_eda_for_upload(
            df_raw=nuevos_raw,
            clima_csv_path=clima_csv,
            regex_config_path=REGEX_JAM_PATH,
        )

    st.success("EDA completado sobre el lote nuevo.")
    st.write(
        f"**Nuevos registros limpios:** {len(nuevos_clean):,} filas · "
        f"{nuevos_clean.shape[1]} columnas"
    )

    # ===================================================
    # 3.3 Integración incremental con base maestra
    #    → aquí es donde “reducimos carga” porque usamos
    #      la base cacheada y solo concatenamos
    # ===================================================
    st.subheader("Integración con base maestra")

    all_cols = sorted(set(master_df.columns) | set(nuevos_clean.columns))
    master_aligned = master_df.reindex(columns=all_cols)
    nuevos_aligned = nuevos_clean.reindex(columns=all_cols)

    combined = pd.concat([master_aligned, nuevos_aligned], ignore_index=True)

    st.write(
        f"**Total combinado (sin deduplicar):** {len(combined):,} registros "
        f"(base maestra: {len(master_df):,} + lote nuevo: {len(nuevos_clean):,})"
    )

    # ===================================================
    # 3.4 Acciones rápidas (guardar / descargar / auditoría)
    # ===================================================
    st.subheader("Acciones rápidas")

    c1, c2, c3, c4 = st.columns(4)

    # Guardar base maestra sobrescrita
    with c1:
        st.caption("Actualizar archivo de base maestra")
        confirm = st.checkbox(
            "Confirmo sobrescribir con la versión combinada",
            key="chk_overwrite",
        )
        if confirm and st.button("Sobrescribir base maestra"):
            try:
                combined.to_csv(DB_PATH, index=False)
                st.success("Base maestra actualizada correctamente.")
            except Exception as e:
                st.error(f"Error al guardar la base maestra: {e}")

    # Descargar lote limpio
    with c2:
        st.caption("Descargar lote limpio")
        st.download_button(
            "Nuevos limpios (CSV)",
            data=nuevos_clean.to_csv(index=False).encode("utf-8"),
            file_name="nuevos_limpios.csv",
            mime="text/csv",
        )

    # Descargar base combinada
    with c3:
        st.caption("Descargar base combinada")
        st.download_button(
            "Base combinada (CSV)",
            data=combined.to_csv(index=False).encode("utf-8"),
            file_name="base_combinada.csv",
            mime="text/csv",
        )

    # Descargar auditoría
    with c4:
        st.caption("Descargar auditoría del EDA")

        stats_json_ready = {}
        for k, v in stats.items():
            if isinstance(v, pd.DataFrame):
                stats_json_ready[k] = v.to_dict(orient="records")
            else:
                stats_json_ready[k] = v

        st.download_button(
            "Auditoría (JSON)",
            data=json.dumps(stats_json_ready, ensure_ascii=False, indent=2).encode(
                "utf-8"
            ),
            file_name="eda_stats_lote_nuevo.json",
            mime="application/json",
        )

    st.divider()

    # ===================================================
    # 3.5 Dashboard del EDA (usa tu módulo de vistas)
    # ===================================================
    st.subheader("Dashboard del EDA para el lote nuevo")
    render_eda_dashboard(nuevos_clean, combined, stats)

    st.divider()
    # Sin “Vistas detalladas”, como pediste.


# ===================================================
# 4. EJECUCIÓN DIRECTA
# ===================================================
if __name__ == "__main__":
    main()
