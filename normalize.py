# ══════════════════════════════════════════════════════════════
#   normalize.py — Convert any uploaded file to clean CSV
#   Supports : CSV, JSON, XLSX
#   Called before ETL pipeline
# ══════════════════════════════════════════════════════════════

import pandas as pd
import os


def normalize_to_csv(uploaded_file, save_path="data/uploaded.csv"):
    """
    Convert uploaded dataset (CSV / JSON / XLSX)
    into a clean standardized CSV for the ETL pipeline.

    Parameters
    ----------
    uploaded_file : Streamlit UploadedFile object
    save_path     : str — where to save the CSV

    Returns
    -------
    str — path to saved CSV file
    """

    filename = uploaded_file.name.lower()

    # ── Detect format and read
    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file, low_memory=False)

    elif filename.endswith(".json"):
        df = pd.read_json(uploaded_file)

    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)

    else:
        raise ValueError(
            f"Unsupported file format: {filename}\n"
            "Accepted formats: CSV, JSON, XLSX"
        )

    # ── Clean column names
    df.columns = df.columns.str.strip()

    # ── Save as standard CSV
    os.makedirs("data", exist_ok=True)
    df.to_csv(save_path, index=False)

    print(f"[NORMALIZE] {filename} → {save_path}  ({df.shape[0]:,} rows × {df.shape[1]} cols)")
    return save_path