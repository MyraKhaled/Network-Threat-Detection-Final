# ══════════════════════════════════════════════════════════════
#   etl.py — ETL Pipeline
#   Same transformations as Kaggle Section 2
#   Includes feature engineering
# ══════════════════════════════════════════════════════════════

import numpy as np
import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler

from config import (
    EXCLUDE_LABELS, FEATURE_TYPE,
    SCALER_PATH, FEATURES_PATH, TARGET_COLUMN
)

# All possible label column names
TARGET_CANDIDATES = [
    "Label_binary", "Label", "label",
    "Class", "class", "Attack", "attack",
    "category", "Category"
]


# ────────────────────────────────────────
#   Step 1 — Find label column
# ────────────────────────────────────────
def find_target_column(df):
    for col in TARGET_CANDIDATES:
        if col in df.columns:
            return col
    return None


# ────────────────────────────────────────
#   Step 2 — Clean
# ────────────────────────────────────────
def clean_data(df):
    df = df.copy()

    # Strip column names
    df.columns = df.columns.str.strip()

    # Replace inf
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Fill NaN with median (numeric columns)
    for col in df.select_dtypes(include=np.number).columns:
        med = df[col].median()
        df[col] = df[col].fillna(0 if np.isnan(med) else med)

    df = df.fillna(0)

    # Remove duplicates
    before = len(df)
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    removed = before - len(df)

    print(f"[ETL] Clean — duplicates removed: {removed:,}", flush=True)
    return df


# ────────────────────────────────────────
#   Step 3 — Feature Engineering
# ────────────────────────────────────────
def feature_engineering(df):
    df = df.copy()

    # Log of flow duration (reduces skewness)
    if "Flow Duration" in df.columns:
        df["log_flow_duration"] = np.log1p(
            df["Flow Duration"].clip(lower=0)
        )

    # Bytes per second
    if "TotLen Fwd Pkts" in df.columns and "Flow Duration" in df.columns:
        df["bytes_per_sec"] = (
            df["TotLen Fwd Pkts"] / (df["Flow Duration"] + 1)
        )

    # Packet direction ratio
    if "Tot Fwd Pkts" in df.columns and "Tot Bwd Pkts" in df.columns:
        df["packet_ratio"]  = df["Tot Fwd Pkts"] / (df["Tot Bwd Pkts"] + 1)
        df["total_packets"] = df["Tot Fwd Pkts"] + df["Tot Bwd Pkts"]

    return df


# ────────────────────────────────────────
#   Step 4 — Normalize labels to binary
# ────────────────────────────────────────
def normalize_label(y):
    """
    Convert any label format to binary:
        0 = BENIGN
        1 = ATTACK
    """
    series = pd.Series(y).astype(str).str.lower().str.strip()
    return series.apply(
        lambda x: 0 if x in ["normal", "benign", "0", "0.0"] else 1
    ).values


# ────────────────────────────────────────
#   Main ETL function
# ────────────────────────────────────────
def run_etl(df, apply_scaler=True):
    """
    Full ETL pipeline.

    Parameters
    ----------
    df           : pd.DataFrame — raw input
    apply_scaler : bool — fit and save StandardScaler

    Returns
    -------
    X            : np.ndarray — feature matrix (scaled)
    y            : np.ndarray — binary labels (0/1)
    feature_cols : list — feature column names
    """

    print("[ETL] START", flush=True)
    os.makedirs("models", exist_ok=True)

    # Step 1 — Clean
    df = clean_data(df)
    print(f"[ETL] After clean: {df.shape[0]:,} rows × {df.shape[1]} cols", flush=True)

    # Step 2 — Feature engineering
    df = feature_engineering(df)

    # Step 3 — Find label column
    target_col = find_target_column(df)
    if target_col is None:
        print("[ETL] ERROR: No label column found", flush=True)
        return None, None, None

    print(f"[ETL] Label column: '{target_col}'", flush=True)

    # Step 4 — Extract and normalize labels
    y_raw = df[target_col].values
    y     = normalize_label(y_raw)

    # Step 5 — Drop label columns from features
    cols_to_drop = [c for c in EXCLUDE_LABELS if c in df.columns]
    cols_to_drop += [target_col]
    cols_to_drop  = list(set(cols_to_drop))
    df = df.drop(columns=cols_to_drop, errors="ignore")

    # Step 6 — Keep numeric features only
    df = df.select_dtypes(include=np.number).fillna(0)

    # Step 7 — Remove constant columns
    constant = [c for c in df.columns if df[c].nunique() <= 1]
    if constant:
        df.drop(columns=constant, inplace=True)
        print(f"[ETL] Constant cols removed: {len(constant)}", flush=True)

    feature_cols = df.columns.tolist()

    # Save feature list
    joblib.dump(feature_cols, FEATURES_PATH)

    X = df.values

    # Step 8 — Scale
    if apply_scaler:
        scaler = StandardScaler()
        X      = scaler.fit_transform(X)
        joblib.dump(scaler, SCALER_PATH)
        print("[ETL] StandardScaler applied and saved", flush=True)

    print(f"[ETL] DONE — X:{X.shape}  y:{y.shape}  "
          f"BENIGN:{(y==0).sum():,}  ATTACK:{(y==1).sum():,}", flush=True)

    return X, y, feature_cols