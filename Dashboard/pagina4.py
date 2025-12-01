# Dashboard/pagina4.py
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.theme_dark import apply_theme
from config import DATA_PATH, ROOT_DIR
from core.data_loader import load_central_dataset
from EDA.eda_pipeline import run_eda_for_upload
from EDA.eda_streamlit_views import render_eda_dashboard


# Page config (title + layout + global theme)
st.set_page_config(
    page_title="Integración & EDA de Datos",
    layout="wide",
)
apply_theme()

# Path to regex configuration file used in the EDA pipeline
REGEX_JAM_PATH: Path = ROOT_DIR / "EDA" / "regex_config.jam"


def main() -> None:
    """Main entrypoint for the EDA & data integration page."""
    st.title("Integración & EDA de Datos")
    st.caption("Carga incremental, limpieza y validación del dataset histórico.")
    st.divider()

    # Load central historical dataset (cached in core.data_loader)
    central_df = load_central_dataset()

    col_info, col_upload = st.columns([2, 3])

    # Left card: dataset overview (current active base)
    with col_info:
        st.markdown(
            f"""
            <div class="panel-card">
              <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:.14em; opacity:.8;">
                Dataset histórico activo
              </div>
              <div style="font-size:1.3rem; font-weight:600; margin-top:0.25rem;">
                {DATA_PATH.name}
              </div>
              <div style="font-size:0.9rem; opacity:0.85; margin-top:0.2rem;">
                {len(central_df):,} registros · {central_df.shape[1]} columnas
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Right card: file upload for new batch
    with col_upload:
        st.markdown(
            """
            <div class="panel-card">
              <div style="font-size:0.8rem; text-transform:uppercase; letter-spacing:.14em; opacity:.8;">
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

    # Optional EDA parameters (currently not wired into pipeline)
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

    # Reserved for future use (kept to avoid unused variable warnings)
    _ = fecha_col, alcaldia_col, ventana_quincenal

    # Require a file before running EDA
    if uploaded is None:
        st.info(
            "Sube un archivo para ejecutar el EDA e integrarlo al dataset histórico."
        )
        return

    # Generic file reader (CSV / Parquet) for the uploaded batch
    def _read_any(file) -> pd.DataFrame:
        """Read uploaded file as CSV or Parquet based on file extension."""
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

    # Ensure regex config file exists before running the pipeline
    if not REGEX_JAM_PATH.exists():
        st.error(f"No se encontró el archivo de patrones: `{REGEX_JAM_PATH}`.")
        return

    # Optional weather enrichment (path validation only)
    clima_csv = None
    if usar_clima:
        p = clima_path.strip()
        if p:
            clima_file = Path(p)
            if clima_file.exists():
                clima_csv = str(clima_file)
            else:
                st.warning(
                    f"No se encontró el archivo de clima en la ruta: `{p}`. "
                    "Se continuará sin enriquecer con clima."
                )

    # Run full EDA pipeline for the new batch
    with st.spinner("Ejecutando EDA sobre los nuevos registros…"):
        nuevos_clean, stats = run_eda_for_upload(
            df_raw=nuevos_raw,
            clima_csv_path=clima_csv,
            regex_config_path=str(REGEX_JAM_PATH),
        )

    st.success("EDA completado sobre el lote nuevo.")
    st.write(
        f"**Nuevos registros limpios:** {len(nuevos_clean):,} filas · "
        f"{nuevos_clean.shape[1]} columnas"
    )

    # Incremental integration with central historical dataset (no deduplication here)
    st.subheader("Integración con el dataset histórico")

    all_cols = sorted(set(central_df.columns) | set(nuevos_clean.columns))
    central_aligned = central_df.reindex(columns=all_cols)
    nuevos_aligned = nuevos_clean.reindex(columns=all_cols)

    combined_df = pd.concat([central_aligned, nuevos_aligned], ignore_index=True)

    st.write(
        f"**Total combinado (sin deduplicar):** {len(combined_df):,} registros "
        f"(dataset histórico: {len(central_df):,} + lote nuevo: {len(nuevos_clean):,})"
    )

    # Quick actions: save updated base, download batch, download combined base, audit
    st.subheader("Acciones rápidas")

    c1, c2, c3, c4 = st.columns(4)

    # Overwrite central dataset on disk (FGJ_CLEAN_Final.csv)
    with c1:
        st.caption("Actualizar archivo del dataset histórico")
        confirm = st.checkbox(
            "Confirmo sobrescribir con la versión combinada",
            key="chk_overwrite",
        )
        if confirm and st.button("Sobrescribir dataset histórico"):
            try:
                combined_df.to_csv(DATA_PATH, index=False)
                st.success("Dataset histórico actualizado correctamente.")
            except Exception as e:
                st.error(f"Error al guardar el dataset histórico: {e}")

    # Download cleaned new batch
    with c2:
        st.caption("Descargar lote limpio")
        st.download_button(
            "Nuevos limpios (CSV)",
            data=nuevos_clean.to_csv(index=False).encode("utf-8"),
            file_name="nuevos_limpios.csv",
            mime="text/csv",
        )

    # Download combined dataset
    with c3:
        st.caption("Descargar dataset combinado")
        st.download_button(
            "Dataset combinado (CSV)",
            data=combined_df.to_csv(index=False).encode("utf-8"),
            file_name="dataset_combinado.csv",
            mime="text/csv",
        )

    # Download EDA audit (JSON with stats + diagnostics)
    with c4:
        st.caption("Descargar auditoría del EDA")

        stats_json_ready = {}
        for key, value in stats.items():
            if isinstance(value, pd.DataFrame):
                stats_json_ready[key] = value.to_dict(orient="records")
            else:
                stats_json_ready[key] = value

        st.download_button(
            "Auditoría (JSON)",
            data=json.dumps(
                stats_json_ready,
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8"),
            file_name="eda_stats_lote_nuevo.json",
            mime="application/json",
        )

    st.divider()

    # Visual EDA dashboard for the new batch
    st.subheader("Dashboard del EDA para el lote nuevo")
    render_eda_dashboard(nuevos_clean, combined_df, stats)

    st.divider()


# Streamlit entrypoint (for local execution)
if __name__ == "__main__":
    main()
