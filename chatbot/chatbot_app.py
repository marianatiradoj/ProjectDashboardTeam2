import textwrap
import os

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai


# ============================================================
#  Cargar variables de entorno (.env)
# ============================================================
load_dotenv()  # carga GEMINI_API_KEY desde .env


# ============================================================
#  GEMINI (usa .env primero, luego secrets)
# ============================================================
@st.cache_resource
def get_gemini_model():
    """
    Inicializa el modelo de Gemini usando:
    1) .env (GEMINI_API_KEY=xxxxx)
    2) secrets (si existiera)

    Modelo correcto: models/gemini-1.5-flash
    """

    # 1) Leer desde .env
    api_key = os.getenv("GEMINI_API_KEY")

    # 2) Leer desde secrets raíz
    if not api_key and "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]

    # 3) Leer desde bloque [snowflake]
    if (
        not api_key
        and "snowflake" in st.secrets
        and "GEMINI_API_KEY" in st.secrets["snowflake"]
    ):
        api_key = st.secrets["snowflake"]["GEMINI_API_KEY"]

    # 4) Validación final
    if not api_key:
        st.error(
            "❌ No encontré GEMINI_API_KEY ni en .env ni en secrets.\n\n"
            "Agrega en tu archivo .env:\n"
            "   GEMINI_API_KEY=tu_api_key\n\n"
            "Y reinicia Streamlit."
        )
        st.stop()

    # Configurar google generative AI
    genai.configure(api_key=api_key)

    # Modelo correcto (NO usar gemini-1.5-flash-latest ni sin prefijo)
    return genai.GenerativeModel("models/gemini-2.5-flash")


# ============================================================
#  SNOWFLAKE
# ============================================================
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


def run_sql(sql: str) -> pd.DataFrame:
    conn = get_snowflake_conn()
    return pd.read_sql(sql, conn)


# ============================================================
#  LÓGICA DEL CHATBOT
# ============================================================

TABLE_NAME = "crimenes"  # tu tabla real en Snowflake

SCHEMA_COLUMNS = [
    "ANIO_INICIO (NUMBER)",
    "MES_INICIO (VARCHAR)",
    "FECHA_INICIO (VARCHAR)",
    "ANIO_HECHO (NUMBER)",
    "MES_HECHO (VARCHAR)",
    "FECHA_HECHO (VARCHAR)",
    "HORA_HECHO (VARCHAR)",
    "DELITO (VARCHAR)",
    "CATEGORIA_DELITO (VARCHAR)",
    "COMPETENCIA (VARCHAR)",
    "FISCALIA (VARCHAR)",
    "AGENCIA (VARCHAR)",
    "UNIDAD_INVESTIGACION (VARCHAR)",
    "COLONIA_HECHO (VARCHAR)",
    "COLONIA_CATALOGO (VARCHAR)",
    "ALCALDIA_HECHO (VARCHAR)",
    "MUNICIPIO_HECHO (VARCHAR)",
    "LATITUD (FLOAT)",
    "LONGITUD (FLOAT)",
    "DELITO_GRUPO (VARCHAR)",
    "DELITO_GRUPO_MACRO (VARCHAR)",
    "CLASE_VIOLENCIA (VARCHAR)",
    "NUM_DIA (NUMBER)",
    "DIA (VARCHAR)",
    "QUINCENA (VARCHAR)",
    "CLIMA_TEMPERATURA (FLOAT)",
    "CLIMA_CONDICION (VARCHAR)",
    "REGION_CDMX (VARCHAR)",
    "PERIODO_HORA (VARCHAR)",
]

SCHEMA_TEXT = "\n".join(SCHEMA_COLUMNS)


def generate_sql(model, question: str) -> str:
    """
    Pide a Gemini que genere UN SOLO SELECT válido sobre la tabla `crimenes`,
    usando únicamente las columnas que realmente existen.
    """
    prompt = textwrap.dedent(
        f"""
        Eres un experto en SQL para Snowflake.

        Solo puedes consultar la tabla {TABLE_NAME}.

        Esquema de la tabla (columnas reales):
        {SCHEMA_TEXT}

        Reglas IMPORTANTES:
        - Usa EXCLUSIVAMENTE los nombres de columna listados arriba.
        - Para filtros de año, usa SIEMPRE ANIO_HECHO (NO uses YEAR(FECHA_HECHO)).
        - Para agrupar o filtrar por alcaldía, usa SIEMPRE ALCALDIA_HECHO (NO 'alcaldia').
        - No inventes nombres genéricos como 'alcaldia', 'fecha', 'anio', etc.
        - Solo SELECT, NUNCA INSERT/UPDATE/DELETE/CREATE.

        Ejemplos:
        - Si el usuario pregunta: "¿Cuántos crímenes hubo por alcaldía en 2023?"
          Debes generar algo como:
          SELECT ALCALDIA_HECHO, COUNT(*) AS total
          FROM {TABLE_NAME}
          WHERE ANIO_HECHO = 2023
          GROUP BY ALCALDIA_HECHO
          ORDER BY total DESC;

        - Si el usuario pregunta: "¿Qué tipo de delitos son más frecuentes?"
          Puedes agrupar por DELITO o por CATEGORIA_DELITO.

        Devuelve SOLO el SQL (un único SELECT), sin explicaciones ni comentarios.

        Pregunta del usuario:
        \"\"\"{question}\"\"\"
        """
    )

    response = model.generate_content(prompt)
    sql = response.text.strip()

    # limpiar bloques ```sql ... ```
    if sql.startswith("```"):
        sql = sql.replace("```sql", "").replace("```", "").strip()

    # quitar ; final por seguridad
    sql = sql.rstrip(";").strip()

    return sql


def generate_natural_answer(model, question: str, df: pd.DataFrame) -> str:
    """
    Pide a Gemini una explicación del resultado en español.
    """
    if df.empty:
        preview = "La consulta no devolvió filas."
    else:
        preview = df.head(20).to_markdown(index=False)

    prompt = textwrap.dedent(
        f"""
        Eres un analista de datos que explica resultados de crímenes en CDMX.

        Pregunta del usuario:
        {question}

        Primeras filas del resultado:
        {preview}

        Instrucciones:
        - Responde en español.
        - Sé claro, breve y profesional.
        - Explica tendencias o insights.
        - Si no hay filas, explica por qué.
        """
    )

    response = model.generate_content(prompt)
    return response.text.strip()


# ============================================================
#  INTERFAZ STREAMLIT
# ============================================================
def run_chatbot_page():
    st.title("💬 Chatbot de Datos (Gemini + Snowflake)")
    st.caption("Pregunta en lenguaje natural sobre la tabla `crimenes`.")

    model = get_gemini_model()

    # inicializar historial
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # mostrar historial
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # input del usuario
    user_input = st.chat_input("Escribe tu pregunta...")

    if not user_input:
        return

    # guardar mensaje usuario
    st.session_state.chat_messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Procesando consulta..."):
            try:
                # SQL con Gemini
                sql = generate_sql(model, user_input)

                # Snowflake
                df = run_sql(sql)

                # respuesta en lenguaje natural
                answer = generate_natural_answer(model, user_input, df)

                # mensaje final completo
                final_msg = answer + "\n\n**SQL generado:**\n```sql\n" + sql + "\n```"

                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": final_msg}
                )

                st.markdown(answer)

                # expanders extras
                with st.expander("SQL generado"):
                    st.code(sql, language="sql")

                with st.expander("Resultados (primeras filas)"):
                    st.dataframe(df.head(50), use_container_width=True)

            except Exception as e:
                error_msg = f"❌ Error al procesar la consulta: {e}"
                st.error(error_msg)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": error_msg}
                )
