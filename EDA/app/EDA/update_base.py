# app/EDA/update_base.py
from __future__ import annotations
from typing import Dict, Optional, List
import os
import pandas as pd

from .eda_pipeline import run_eda


# -------- helpers para lectura/escritura --------
def _read_any(path: str) -> pd.DataFrame:
    lower = path.lower()
    if lower.endswith(".csv"):
        return pd.read_csv(path)
    elif lower.endswith(".parquet"):
        return pd.read_parquet(path)
    else:
        raise ValueError(f"Formato no soportado: {path} (usa .csv o .parquet)")


def _write_any(df: pd.DataFrame, path: str) -> None:
    lower = path.lower()
    if lower.endswith(".csv"):
        df.to_csv(path, index=False)
    elif lower.endswith(".parquet"):
        df.to_parquet(path, index=False)
    else:
        raise ValueError(f"Formato no soportado para escribir: {path}")


# -------- función principal --------
def update_master_base(
    master_path: str,
    new_raw_path: str,
    output_path: Optional[str] = None,
    cfg: Optional[Dict] = None,
) -> Dict:
    """
    1) Lee base maestra (ya existente).
    2) Lee datos nuevos crudos.
    3) Corre run_eda() sobre datos nuevos.
    4) Alinea columnas y concatena.
    5) Opcional: elimina duplicados por id.
    6) Guarda la base actualizada.

    Returns: diccionario con info de auditoría.
    """
    cfg = cfg or {}

    # Parámetros de IDs para evitar duplicados
    id_cols: Optional[List[str]] = cfg.get(
        "id_cols"
    )  # ej. ["id_carpeta", "id_registro"]

    # 1) Leer bases
    master_df = _read_any(master_path)
    new_raw_df = _read_any(new_raw_path)

    # 2) Correr EDA sobre los nuevos datos
    new_clean_df, eda_stats, artifacts = run_eda(new_raw_df, cfg)

    # 3) Alinear columnas (union de columnas maestro + nuevos)
    all_cols = sorted(set(master_df.columns) | set(new_clean_df.columns))
    master_aligned = master_df.reindex(columns=all_cols)
    new_aligned = new_clean_df.reindex(columns=all_cols)

    # 4) Concatenar
    combined = pd.concat([master_aligned, new_aligned], ignore_index=True)

    # 5) Opcional: eliminar duplicados por columnas id
    n_before = len(combined)
    if id_cols:
        for col in id_cols:
            if col not in combined.columns:
                raise KeyError(
                    f"Columna id '{col}' no existe en el dataframe combinado"
                )
        combined = combined.drop_duplicates(subset=id_cols, keep="last").reset_index(
            drop=True
        )
    n_after = len(combined)

    # 6) Guardar
    if output_path is None:
        # sobrescribe la maestra
        output_path = master_path
    else:
        # crea carpeta si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    _write_any(combined, output_path)

    # 7) Info resumen
    info = {
        "master_rows_before": len(master_df),
        "new_raw_rows": len(new_raw_df),
        "new_clean_rows": len(new_clean_df),
        "combined_rows_before_dedup": n_before,
        "combined_rows_after_dedup": n_after,
        "n_rows_added_effective": n_after - len(master_df),
        "id_cols": id_cols,
        "eda_stats": eda_stats,
        "output_path": output_path,
    }
    return info


# -------- CLI simple --------
if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser(
        description="Actualizar base maestra con nuevos datos tras EDA"
    )
    parser.add_argument(
        "--master", required=True, help="Ruta base maestra (.csv o .parquet)"
    )
    parser.add_argument(
        "--new_raw", required=True, help="Ruta datos nuevos crudos (.csv o .parquet)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta de salida (si no se da, sobrescribe master)",
    )
    parser.add_argument(
        "--regex", default="EDA/regex_config.jam", help="Ruta .jam de regex"
    )
    parser.add_argument("--date_col", default="fecha_hecho")
    parser.add_argument("--alcaldia_col", default="alcaldia_hecho")
    parser.add_argument("--quincena_days", type=int, default=2)
    parser.add_argument(
        "--id_cols",
        nargs="*",
        default=None,
        help="Columnas llave para evitar duplicados",
    )
    args = parser.parse_args()

    cfg = {
        "regex_path": args.regex,
        "with_weather": False,  # puedes cambiar a True y agregar weather_path si quieres
        "date_col": args.date_col,
        "alcaldia_col": args.alcaldia_col,
        "quincena_window": args.quincena_days,
        "id_cols": args.id_cols,
    }

    info = update_master_base(
        master_path=args.master,
        new_raw_path=args.new_raw,
        output_path=args.output,
        cfg=cfg,
    )

    print(json.dumps(info, indent=2, ensure_ascii=False))
