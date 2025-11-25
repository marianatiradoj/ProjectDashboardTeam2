import numpy as np
import pandas as pd

def build_inference_frame(dt, colonias_base):
    df = colonias_base.copy()

    # timestamp
    df["ts"] = dt
    df["fecha_hecho"] = pd.to_datetime(dt)

    # Hora
    df["hour_numeric"] = df["fecha_hecho"].dt.hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour_numeric"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour_numeric"] / 24)

    # Día de semana
    df["weekday_numeric"] = df["fecha_hecho"].dt.dayofweek
    df["weekday_sin"] = np.sin(2 * np.pi * df["weekday_numeric"] / 7)
    df["weekday_cos"] = np.cos(2 * np.pi * df["weekday_numeric"] / 7)

    # Mes
    df["month_numeric"] = df["fecha_hecho"].dt.month
    df["month_sin"] = np.sin(2 * np.pi * df["month_numeric"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month_numeric"] / 12)

    # Fin de semana
    df["is_weekend"] = df["weekday_numeric"].isin([5, 6]).astype(int)

    # Quincena
    day = df["fecha_hecho"].dt.day
    df["quincena_window_numeric"] = (day <= 15).astype(int)

    return df
