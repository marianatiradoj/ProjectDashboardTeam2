# app/TEST/test_macro_groups.py
import pandas as pd
from EDA.eda_pipeline import run_eda


def test_ver_macrogrupos():
    # Dataset chiquito y controlado
    df = pd.DataFrame(
        {
            "delito": [
                "Robo a transeúnte a bordo de taxi en la colonia Centro",  # 0
                "Violencia familiar en domicilio",  # 1
                "Fraude electrónico a cuentahabiente",  # 2
                "Lesiones con arma de fuego",  # 3
                "Robo a negocio tienda de conveniencia",  # 4
                "Posesión simple de drogas",  # 5
            ],
            "fecha_hecho": [
                "2025-01-16",
                "2025-01-31",
                "2025-02-01",
                "2025-02-15",
                "2025-02-27",
                "2025-03-01",
            ],
            "alcaldia_hecho": [
                "Cuauhtémoc",
                "Benito Juárez",
                "Cuauhtémoc",
                "Iztapalapa",
                "Miguel Hidalgo",
                "Coyoacán",
            ],
            "colonia_hecho": ["Centro", "Del Valle", None, None, "Anzures", "Copilco"],
            "colonia_catalogo": [
                None,
                "Del Valle",
                "Centro",
                "Agrícola Oriental",
                None,
                None,
            ],
            "latitud": [None, 19.38, None, None, 19.43, None],
            "longitud": [None, -99.16, None, None, -99.19, None],
            "competencia": [None, None, "Local", None, None, None],
        }
    )

    cfg = {
        "regex_path": "EDA/regex_config.jam",  # usa el .jam que tienes en la carpeta EDA
        "with_weather": False,
        "date_col": "fecha_hecho",
        "alcaldia_col": "alcaldia_hecho",
        "quincena_window": 2,
    }

    df_clean, stats, artifacts = run_eda(df, cfg)

    # ============================
    # 1) VER FILA x FILA
    # ============================
    print("\n====== DELITO → GRUPO → MACROGRUPO ======")
    print(df_clean[["delito", "delito_grupo", "delito_grupo_macro", "violencia_class"]])

    # ============================
    # 2) VER RESUMEN DE MACROGRUPOS
    # ============================
    print("\n====== RESUMEN MACROGRUPOS (stats['clasificacion']) ======")
    macro_counts = stats["clasificacion"]["macrogroup_counts"]
    macro_pct = stats["clasificacion"]["macrogroup_pct"]
    print("Conteo:", macro_counts)
    print("Porcentajes:", macro_pct)

    # Aserciones mínimas para que pytest marque el test como válido
    assert "delito_grupo_macro" in df_clean.columns
    assert len(macro_counts) > 0
