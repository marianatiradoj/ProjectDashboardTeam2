# core/data_loader.py
from pathlib import Path
import json

import pandas as pd
import streamlit as st
import snowflake.connector  # 👈 IMPORTANTE

from config import (
    COLONIAS_GEOJSON,
)


# 🔹 Conexión Snowflake (usando tus secrets)
@st.cache_resource
def get_snowflake_conn():
    conf = st.secrets["snowflake"]
    return snowflake.connector.connect(
        account=conf["account"],
        user=conf["user"],
        password=conf["password"],
        role=conf.get("role"),
        warehouse=conf["warehouse"],
        database=conf["database"],
        schema=conf["schema"],
    )


# 🔹 Cargar dataset central desde Snowflake
@st.cache_data(show_spinner="Cargando dataset desde Snowflake…")
def load_central_dataset() -> pd.DataFrame:
    sql = """
    SELECT
        ANIO_INICIO,
        MES_INICIO,
        FECHA_INICIO,
        ANIO_HECHO,
        MES_HECHO,
        FECHA_HECHO,
        HORA_HECHO,
        DELITO,
        CATEGORIA_DELITO,
        COMPETENCIA,
        FISCALIA,
        AGENCIA,
        UNIDAD_INVESTIGACION,
        COLONIA_HECHO,
        COLONIA_CATALOGO,
        ALCALDIA_HECHO,
        MUNICIPIO_HECHO,
        LATITUD,
        LONGITUD,
        DELITO_GRUPO,
        DELITO_GRUPO_MACRO,
        CLASE_VIOLENCIA,
        NUM_DIA,
        DIA,
        QUINCENA,
        CLIMA_TEMPERATURA,
        CLIMA_CONDICION,
        REGION_CDMX,
        PERIODO_HORA
    FROM CRIMENES
    WHERE ANIO_HECHO BETWEEN 2016 AND 2025
    """

    conn = get_snowflake_conn()
    cur = conn.cursor()

    try:
        # ❌ Antes: df = pd.read_sql(sql, conn)  → daba UserWarning
        # ✅ Ahora: usamos la API nativa de Snowflake para pandas:
        cur.execute(sql)
        df = cur.fetch_pandas_all()
    finally:
        cur.close()
        # Si quieres, puedes también cerrar la conexión aquí:
        # conn.close()

    # 👇 Normalizar nombres para que coincidan con TODO tu código actual
    df.columns = [c.lower() for c in df.columns]

    # Opcional: asegurar fecha_hecho como datetime
    if "fecha_hecho" in df.columns:
        df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")

    return df


# 🔹 Loader de polígonos (igual que antes)
@st.cache_data(show_spinner="Loading colonias polygons…")
def load_colonias_geojson() -> dict:
    with open(COLONIAS_GEOJSON, "r", encoding="utf-8") as f:
        return json.load(f)
