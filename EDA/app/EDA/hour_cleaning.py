# EDA/hour_cleaning.py
import pandas as pd


def normalize_hour_column(df, col: str = "hora_hecho") -> pd.DataFrame:
    """
    Normaliza la columna de hora a valores enteros 0–23 en df[col].

    - Acepta formatos como:
        '04:00:00',
        '4:00',
        '04:00:00 a. m.',
        '11:00:00 p. m.',
        etc.
    - Si no puede parsear algún valor, lo deja como NaN.
    """

    if col not in df.columns:
        # Si no existe, no hacemos nada
        return df

    # Pasamos todo a string y limpiamos espacios
    s = df[col].astype(str).str.strip()

    # 1) Intento con formato 24h clásico: HH:MM:SS
    dt = pd.to_datetime(s, format="%H:%M:%S", errors="coerce")

    # 2) Donde falló, probamos 24h sin segundos: HH:MM
    mask = dt.isna()
    if mask.any():
        dt2 = pd.to_datetime(s[mask], format="%H:%M", errors="coerce")
        dt = dt.where(~mask, dt2)

    # 3) Donde siga fallando, probamos 12h con AM/PM,
    #    reemplazando 'a. m.' / 'p. m.' por AM/PM
    mask = dt.isna()
    if mask.any():
        s_am_pm = (
            s[mask]
            .str.replace("a. m.", "AM", regex=False)
            .str.replace("p. m.", "PM", regex=False)
            .str.replace("a. m.", "AM", regex=False)  # variantes con espacio raro
            .str.replace("p. m.", "PM", regex=False)
        )
        dt3 = pd.to_datetime(s_am_pm, format="%I:%M:%S %p", errors="coerce")
        dt = dt.where(~mask, dt3)

    # 4) Último recurso: extraemos el primer número (hora) si todo lo demás falló
    horas = dt.dt.hour.astype("float")

    mask = horas.isna()
    if mask.any():
        extraida = (
            s[mask]
            .str.extract(r"(\d{1,2})")[0]
            .astype("float")
        )
        horas = horas.where(~mask, extraida)

    # Guardamos el resultado en la MISMA columna para que
    # el resto de tu código (EDA, gráficas, etc.) siga usando 'hora_hecho'
    df[col] = horas.astype("Int64")  # enteros 0–23 con soporte para NaN

    return df
