import os
import sys
import pandas as pd
import streamlit as st

# ============================
# 1. Resolver rutas del proyecto
# ============================
THIS_DIR = os.path.dirname(__file__)  # .../dashboard
ROOT_DIR = os.path.dirname(THIS_DIR)  # raíz del proyecto
DB_PATH = os.path.join(ROOT_DIR, "Database", "FGJ_CLEAN_Final.csv")

# Ruta al código del EDA: EDA/app/EDA/eda_pipeline.py
EDA_APP_DIR = os.path.join(ROOT_DIR, "EDA", "app")
if EDA_APP_DIR not in sys.path:
    sys.path.insert(0, EDA_APP_DIR)

from EDA.eda_pipeline import run_eda  # ← IMPORTA DESPUÉS de agregar EDA_APP_DIR

REGEX_JAM_PATH = os.path.join(EDA_APP_DIR, "EDA", "regex_config.jam")


# ============================
# 2. Cachear la base maestra
# ============================
@st.cache_data(show_spinner="Cargando base maestra (FGJ_CLEAN_Final)...")
def load_master_df() -> pd.DataFrame:
    # Si puedes convertirla a parquet antes, aún mejor, pero por ahora usamos CSV
    df = pd.read_csv(DB_PATH, low_memory=False)
    return df


# ============================
# 3. Página 4 – EDA incremental
# ============================
def main():
    st.title("Página 4 – EDA e Integración con Base Maestra")

    # 3.1. Cargar base maestra desde cache
    master_df = load_master_df()

    st.markdown(
        f"**Base maestra cargada:** `{os.path.basename(DB_PATH)}`  "
        f"({len(master_df):,} registros, {master_df.shape[1]} columnas)"
    )

    st.divider()

    # 3.2. Subir lote nuevo crudo
    st.subheader("1) Subir nuevos registros crudos")
    uploaded = st.file_uploader(
        "Sube un archivo con nuevos registros (.csv o .parquet)",
        type=["csv", "parquet"],
        key="uploader_nuevos",
    )

    # Configuración del EDA (puedes exponer más parámetros si quieres)
    with st.expander("Parámetros del EDA", expanded=False):
        date_col = st.text_input("Columna de fecha", "fecha_hecho")
        alcaldia_col = st.text_input("Columna de alcaldía", "alcaldia_hecho")
        quincena_window = st.slider("± días ventana quincena", 0, 5, 2)
        usar_clima = st.checkbox("Enriquecer con clima", value=False)
        weather_path = st.text_input(
            "Ruta CSV de clima (solo si usas clima)",
            "",
            help="Por ahora puede quedar vacío; se usa solo si marcas 'Enriquecer con clima'.",
        )

    if uploaded is None:
        st.info(
            "Sube un archivo de nuevos registros para correr el EDA e integrarlo a la base."
        )
        return

    # 3.3. Leer el lote nuevo
    def _read_any(file) -> pd.DataFrame:
        name = file.name.lower()
        if name.endswith(".csv"):
            return pd.read_csv(file)
        return pd.read_parquet(file)

    try:
        nuevos_raw = _read_any(uploaded)
    except Exception as e:
        st.error(f"Error leyendo el archivo subido: {e}")
        return

    st.write(
        f"**Nuevos registros crudos:** {len(nuevos_raw):,} filas, {nuevos_raw.shape[1]} columnas"
    )

    # 3.4. Ejecutar EDA sobre el lote nuevo
    cfg = {
        "regex_path": REGEX_JAM_PATH if os.path.exists(REGEX_JAM_PATH) else None,
        "with_weather": usar_clima and bool(weather_path),
        "weather_path": weather_path,
        "date_col": date_col,
        "alcaldia_col": alcaldia_col,
        "quincena_window": quincena_window,
    }

    with st.spinner("Ejecutando EDA sobre los nuevos registros..."):
        nuevos_clean, stats, artifacts = run_eda(nuevos_raw, cfg)

    st.success("EDA completado sobre los nuevos registros.")
    st.write(
        f"**Nuevos registros limpios:** {len(nuevos_clean):,} filas, {nuevos_clean.shape[1]} columnas"
    )

    # 3.5. Alinear columnas y combinar con la base maestra
    st.subheader("2) Integración con la base maestra")

    all_cols = sorted(set(master_df.columns) | set(nuevos_clean.columns))
    master_aligned = master_df.reindex(columns=all_cols)
    new_aligned = nuevos_clean.reindex(columns=all_cols)

    combined = pd.concat([master_aligned, new_aligned], ignore_index=True)

    st.write(
        f"**Total combinado (sin deduplicar):** {len(combined):,} registros "
        f"(maestra: {len(master_df):,} + nuevos: {len(nuevos_clean):,})"
    )

    # Si tienes una columna ID para evitar duplicados, cámbiala aquí:
    id_cols = []  # ejemplo: ["id_registro"] o ["id_carpeta", "id_registro"]

    if id_cols:
        st.caption(f"Eliminando duplicados usando columnas ID: {id_cols}")
        combined_before = len(combined)
        combined = combined.drop_duplicates(subset=id_cols, keep="last").reset_index(
            drop=True
        )
        st.write(
            f"**Total combinado tras deduplicar:** {len(combined):,} "
            f"(se eliminaron {combined_before - len(combined):,} duplicados)"
        )

    # 3.6. Vista rápida
    with st.expander(
        "Vista previa de nuevos registros limpios (primeras 200 filas)", expanded=False
    ):
        st.dataframe(nuevos_clean.head(200))

    with st.expander(
        "Vista previa de la base combinada (últimas 200 filas)", expanded=False
    ):
        st.dataframe(combined.tail(200))

    # 3.7. Figura de macrogrupos (solo de los nuevos)
    if "macrogroup_bar" in artifacts["figs"]:
        st.subheader("Distribución de macrogrupos (solo lote nuevo)")
        st.pyplot(artifacts["figs"]["macrogroup_bar"])

    # 3.8. Descargas
    st.subheader("3) Descargas")

    # Nuevos limpios
    st.download_button(
        "Descargar nuevos registros limpios (CSV)",
        data=nuevos_clean.to_csv(index=False).encode("utf-8"),
        file_name="nuevos_limpios.csv",
        mime="text/csv",
    )

    # Base combinada (no sobreescribimos tu archivo original)
    st.download_button(
        "Descargar base maestra + nuevos (CSV)",
        data=combined.to_csv(index=False).encode("utf-8"),
        file_name="base_maestra_actualizada.csv",
        mime="text/csv",
    )

    # Auditoría del EDA
    import json

    st.download_button(
        "Descargar auditoría del EDA (JSON, solo lote nuevo)",
        data=json.dumps(stats, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="eda_stats_nuevos.json",
        mime="application/json",
    )


if __name__ == "__main__":
    main()
