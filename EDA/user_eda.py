# user_eda.py
# Script de prueba local. En Streamlit NO lo necesitas, pero sirve para validar.

from eda_pipeline import run_eda_for_upload, append_to_base_csv
from update_base import robust_read_csv


def main():
    # Ajusta estas rutas a tu entorno local
    DATA_CSV = "/ruta/a/tu/nuevo_archivo.csv"  # archivo "crudo" nuevo
    CLIMA_CSV = "/ruta/a/Clima_Delegaciones.csv"
    BASE_LIMPIA = "/ruta/a/FGJ_CLEAN_base.csv"  # base ya limpia
    OUTPUT_BASE = "/ruta/a/FGJ_CLEAN_actualizada.csv"  # salida combinada

    df_raw = robust_read_csv(DATA_CSV)

    df_clean, stats = run_eda_for_upload(
        df_raw=df_raw,
        clima_csv_path=CLIMA_CSV,
        regex_config_path="regex_config.jam",
    )

    print("Stats EDA:")
    for k, v in stats.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v}")

    merge_info = append_to_base_csv(
        new_clean_df=df_clean,
        base_clean_csv_path=BASE_LIMPIA,
        output_path=OUTPUT_BASE,
    )
    print("\nMerge info:", merge_info)


if __name__ == "__main__":
    main()
