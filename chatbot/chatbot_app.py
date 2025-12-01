import textwrap
import os

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables for local dev
load_dotenv()


@st.cache_resource
def get_gemini_model():
    """Init Gemini model using Streamlit secrets or .env as fallback."""
    api_key = None

    # 1) Root-level secret: GEMINI_API_KEY
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]

    # 2) [gemini] block with key api_key
    if api_key is None and "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
        api_key = st.secrets["gemini"]["api_key"]

    # 3) [snowflake] block with GEMINI_API_KEY (legacy)
    if (
        api_key is None
        and "snowflake" in st.secrets
        and "GEMINI_API_KEY" in st.secrets["snowflake"]
    ):
        api_key = st.secrets["snowflake"]["GEMINI_API_KEY"]

    # 4) Local .env fallback
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        st.error(
            "No se encontró GEMINI_API_KEY. "
            "Configura la clave en Streamlit Secrets o en un archivo .env."
        )
        st.stop()

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("models/gemini-2.5-flash")


@st.cache_resource
def get_snowflake_conn():
    """Create Snowflake connection using Streamlit secrets."""
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
    """Run SQL on Snowflake and return a DataFrame."""
    conn = get_snowflake_conn()
    return pd.read_sql(sql, conn)


# Snowflake table metadata
TABLE_NAME = "crimenes"

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


# ---------------------------------------------------------------------
# Filter → prompt helpers
# ---------------------------------------------------------------------
def _format_filters_interactive(filters: dict) -> str:
    """Format filters from pagina5 (interactive dashboard)."""
    parts: list[str] = []

    year_range = filters.get("anio_hecho")
    if isinstance(year_range, (list, tuple)) and len(year_range) == 2:
        y1, y2 = year_range
        if y1 == y2:
            parts.append(f"- Año del hecho: {y1}")
        else:
            parts.append(f"- Años del hecho: {y1} a {y2}")

    month_range = filters.get("mes_hecho")
    if isinstance(month_range, (list, tuple)) and len(month_range) == 2:
        m1, m2 = month_range
        if m1 == m2:
            parts.append(f"- Mes del hecho: {m1}")
        else:
            parts.append(f"- Meses del hecho: {m1} a {m2}")

    day_range = filters.get("dia")
    if isinstance(day_range, (list, tuple)) and len(day_range) == 2:
        d1, d2 = day_range
        if d1 == d2:
            parts.append(f"- Día de la semana: {d1}")
        else:
            parts.append(f"- Días de la semana: {d1} a {d2}")

    macro = filters.get("delito_grupo_macro")
    if macro and macro != "Totalidad":
        parts.append(f"- Tipo principal de delito: {macro}")

    grupo = filters.get("delito_grupo")
    if grupo and grupo != "Totalidad":
        parts.append(f"- Grupo de delito: {grupo}")

    alc = filters.get("alcaldia_hecho")
    if alc and alc != "Totalidad":
        parts.append(f"- Alcaldía de ocurrencia: {alc}")

    region = filters.get("region_cdmx")
    if region and region != "Totalidad":
        parts.append(f"- Región CDMX: {region}")

    periodo = filters.get("periodo_hora")
    if periodo and periodo != "Totalidad":
        parts.append(f"- Periodo del día: {periodo}")

    violencia = filters.get("clase_violencia")
    if violencia and violencia != "Totalidad":
        parts.append(f"- Tipo de violencia: {violencia}")

    clima = filters.get("clima_condicion")
    if clima and clima != "Totalidad":
        parts.append(f"- Condición climática: {clima}")

    quincena = filters.get("quincena")
    if quincena and quincena != "Totalidad":
        parts.append(f"- Ventana de quincena: {quincena}")

    if not parts:
        return ""

    return "Filtros activos del dashboard:\n" + "\n".join(parts)


def _format_filters_legacy(filters: dict) -> str:
    """Format filters from older dashboard (zona, hour_range, etc.)."""
    parts: list[str] = []

    zona = filters.get("zona")
    if zona and zona not in ("Todas", "Todos"):
        parts.append(f"- Zona: {zona}")

    hour_range = filters.get("hour_range")
    if isinstance(hour_range, (list, tuple)) and len(hour_range) == 2:
        parts.append(
            f"- Rango horario: de {hour_range[0]:02d}:00 a {hour_range[1]:02d}:00"
        )

    mes = filters.get("mes")
    if mes and mes != "Todos":
        parts.append(f"- Mes: {mes}")

    dia_semana = filters.get("dia_semana")
    if dia_semana and dia_semana != "Todos":
        parts.append(f"- Día de la semana: {dia_semana}")

    tipos_crimen = filters.get("tipos_crimen")
    if tipos_crimen:
        tipos_list = ", ".join(tipos_crimen)
        parts.append(f"- Grupos de delito: {tipos_list}")

    if not parts:
        return ""

    return "Filtros activos del dashboard:\n" + "\n".join(parts)


def format_filters_for_prompt(filter_context: dict | None) -> str:
    """Format dashboard filters as a text block for the LLM prompt."""
    if not filter_context:
        return ""

    # Detect interactive-dashboard style vs legacy style
    if any(k in filter_context for k in ("anio_hecho", "mes_hecho", "delito_grupo")):
        block = _format_filters_interactive(filter_context)
    else:
        block = _format_filters_legacy(filter_context)

    return block.strip()


def build_question_from_filters(filter_context: dict | None) -> str:
    """Build an automatic user question from active filters."""
    filters_text = format_filters_for_prompt(filter_context)

    if not filters_text:
        return (
            "Con base en los datos de crímenes en la CDMX entre 2016 y 2025, "
            "¿qué patrones relevantes observas en la incidencia delictiva?"
        )

    question = textwrap.dedent(
        f"""
        Considerando los siguientes filtros aplicados en el dashboard interactivo de crímenes:

        {filters_text}

        ¿Qué patrones relevantes observas en la incidencia delictiva bajo estos filtros?
        Responde de forma ejecutiva y concisa.
        """
    ).strip()

    return question


# ---------------------------------------------------------------------
# LLM interaction: SQL + narrative answer
# ---------------------------------------------------------------------
def generate_sql(model, question: str, filter_context: dict | None = None) -> str:
    """Ask Gemini to generate a single SELECT query on table `crimenes`."""
    filters_block = format_filters_for_prompt(filter_context)

    prompt = textwrap.dedent(
        f"""
        Eres un experto en SQL para Snowflake.

        Solo puedes consultar la tabla {TABLE_NAME}.

        Esquema de la tabla (columnas reales):
        {SCHEMA_TEXT}

        {filters_block if filters_block else ""}

        Reglas IMPORTANTES:
        - Usa exclusivamente los nombres de columna listados arriba.
        - Para filtros de año, usa siempre ANIO_HECHO (no uses YEAR(FECHA_HECHO)).
        - Toda consulta debe incluir ANIO_HECHO BETWEEN 2016 AND 2025.
        - Para agrupar o filtrar por alcaldía, usa ALCALDIA_HECHO.
        - No inventes nombres genéricos como 'alcaldia', 'fecha', 'anio', etc.
        - Solo SELECT, nunca INSERT/UPDATE/DELETE/CREATE.
        - Devuelve un único SELECT, sin explicaciones ni comentarios.

        Pregunta del usuario:
        \"\"\"{question}\"\"\"
        """
    )

    response = model.generate_content(prompt)
    sql = response.text.strip()

    # Strip fenced code if present
    if sql.startswith("```"):
        sql = sql.replace("```sql", "").replace("```", "").strip()

    # Remove trailing semicolon for safety
    sql = sql.rstrip(";").strip()

    return sql


def generate_natural_answer(
    model,
    question: str,
    df: pd.DataFrame,
    filter_context: dict | None = None,
) -> str:
    """Ask Gemini for a Spanish executive explanation."""
    preview = (
        "La consulta no devolvió filas."
        if df.empty
        else df.head(20).to_markdown(index=False)
    )

    filters_block = format_filters_for_prompt(filter_context)

    prompt = textwrap.dedent(
        f"""
        Actúa como un analista senior en ciencia de datos especializado en criminalidad urbana en la CDMX.

        Pregunta del usuario:
        {question}

        {filters_block if filters_block else ""}

        Primeras filas del resultado:
        {preview}

        Instrucciones:
        - Responde en español profesional.
        - Usa esta estructura:
          1) Resumen del hallazgo principal.
          2) Interpretación del contexto o tendencias.
          3) Posibles implicaciones o líneas de acción.
        - Si no hay datos, explica la ausencia y da posibles razones.
        - Evita jerga técnica innecesaria.
        """
    )

    response = model.generate_content(prompt)
    return response.text.strip()


def _run_single_qa_cycle(
    model,
    question: str,
    filter_context: dict | None = None,
) -> None:
    """Run one QA cycle: SQL → DataFrame → narrative answer."""
    sql = generate_sql(model, question, filter_context=filter_context)
    df = run_sql(sql)
    answer = generate_natural_answer(
        model,
        question,
        df,
        filter_context=filter_context,
    )

    final_msg = answer + "\n\n**SQL generado:**\n```sql\n" + sql + "\n```"

    st.session_state.chat_messages.append({"role": "assistant", "content": final_msg})

    st.markdown(answer)

    with st.expander("SQL generado"):
        st.code(sql, language="sql")

    with st.expander("Resultados (primeras filas)"):
        st.dataframe(df.head(50), use_container_width=True)


# ---------------------------------------------------------------------
# Streamlit chatbot UI
# ---------------------------------------------------------------------
def run_chatbot_page(filter_context: dict | None = None):
    """
    Render chatbot UI.

    - Normal questions: ignore dashboard filters (user controla todo).
    - Filter-triggered questions: build question from filters and run 1 cycle.
    """
    # Slightly bigger font for chat
    st.markdown(
        """
        <style>
        div[data-testid="stChatMessageContent"] p,
        .stMarkdown,
        .stTextInput input,
        .stChatInputContainer textarea {
            font-size: 18px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Haz preguntas sobre crímenes en la CDMX de 2016 a 2025. "
        "Puedes generar un análisis específico usando los filtros del dashboard interactivo."
    )

    model = get_gemini_model()

    # Init chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # One-shot trigger from dashboard (pagina3 o pagina5)
    use_filters_now = st.session_state.pop("chatbot_use_filters_once", False)
    auto_question = st.session_state.pop("chatbot_auto_question", None)

    if use_filters_now and filter_context:
        # Prefer pre-built question, else build from filters here
        question = auto_question or build_question_from_filters(filter_context)
        st.session_state.chat_messages.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Procesando análisis con filtros del dashboard..."):
                try:
                    _run_single_qa_cycle(
                        model,
                        question,
                        filter_context=filter_context,
                    )
                except Exception as e:
                    error_msg = f"Error al procesar la consulta con filtros: {e}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

    # Render full history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Normal user input
    user_input = st.chat_input("Escribe tu pregunta...")

    if not user_input:
        return

    st.session_state.chat_messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Procesando consulta..."):
            try:
                _run_single_qa_cycle(
                    model,
                    user_input,
                    filter_context=None,  # normal questions ignore dashboard filters
                )
            except Exception as e:
                error_msg = f"Error al procesar la consulta: {e}"
                st.error(error_msg)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": error_msg}
                )
