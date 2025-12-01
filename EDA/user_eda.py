# user_eda.py
# Local test script to validate the EDA pipeline outside Streamlit.

from eda_pipeline import run_eda_for_upload, append_to_base_csv
from update_base import robust_read_csv


def main() -> None:
    """Run a local EDA test over a new CSV batch."""
    DATA_CSV = "/ruta/a/tu/nuevo_archivo.csv"
    CLIMA_CSV = "/ruta/a/Clima_Delegaciones.csv"
    BASE_LIMPIA = "/ruta/a/FGJ_CLEAN_base.csv"
    OUTPUT_BASE = "/ruta/a/FGJ_CLEAN_actualizada.csv"

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
