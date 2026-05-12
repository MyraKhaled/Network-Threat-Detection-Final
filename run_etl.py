import sys
import io
import numpy as np
import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from config import EXCLUDE_LABELS, SCALER_PATH, FEATURES_PATH, TARGET_COLUMN

TARGET_CANDIDATES = [
    "Label_binary", "Label", "label",
    "Class", "class", "Attack", "attack",
    "category", "Category"
]

CHUNK_SIZE = 50_000


def find_target_column(df):
    for col in TARGET_CANDIDATES:
        if col in df.columns:
            return col
    return None


def clean_data(df):
    """
    Nettoyage NaN/Inf uniquement.

    ⚠ Déduplication INTENTIONNELLEMENT ABSENTE :
      - pandas drop_duplicates() alloue (n_cols x n_rows) int64 → OOM
      - df.apply() hash-based alloue la même matrice transposée → OOM
      - Sur CIC-IDS2017 les doublons < 3% n'affectent pas les métriques
    """
    df = df.copy()
    df.columns = df.columns.str.strip()
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    for col in df.select_dtypes(include=np.number).columns:
        med = df[col].median()
        df[col] = df[col].fillna(
            0.0 if (isinstance(med, float) and np.isnan(med)) else med
        )

    df = df.fillna(0)
    print(f"[ETL] Clean done — {len(df):,} rows", flush=True)
    return df


def feature_engineering(df):
    df = df.copy()
    if "Flow Duration" in df.columns:
        df["log_flow_duration"] = np.log1p(df["Flow Duration"].clip(lower=0))
    if "TotLen Fwd Pkts" in df.columns and "Flow Duration" in df.columns:
        df["bytes_per_sec"] = df["TotLen Fwd Pkts"] / (df["Flow Duration"] + 1)
    if "Tot Fwd Pkts" in df.columns and "Tot Bwd Pkts" in df.columns:
        df["packet_ratio"]  = df["Tot Fwd Pkts"] / (df["Tot Bwd Pkts"] + 1)
        df["total_packets"] = df["Tot Fwd Pkts"] + df["Tot Bwd Pkts"]
    return df


def normalize_label(y):
    series = pd.Series(y).astype(str).str.lower().str.strip()
    return series.apply(
        lambda x: 0 if x in ["normal", "benign", "0", "0.0"] else 1
    ).values


def downcast_numeric_features(df):
    """float64→float32, int64→int32. Appelé après select_dtypes."""
    for col in df.select_dtypes(include="float64").columns:
        df[col] = df[col].astype(np.float32)
    for col in df.select_dtypes(include="int64").columns:
        df[col] = df[col].astype(np.int32)
    return df


def run_etl(df, apply_scaler=True):
    """
    Pipeline ETL complet — memory-safe v3.2

    Retourne
    --------
    X            : np.ndarray float32
    y            : np.ndarray int8
    feature_cols : list[str]
    """
    print("[ETL] START", flush=True)
    os.makedirs("models", exist_ok=True)

    # 1. Nettoyage (SANS déduplication)
    df = clean_data(df)
    print(f"[ETL] After clean: {df.shape[0]:,} rows x {df.shape[1]} cols", flush=True)

    # 2. Feature engineering
    df = feature_engineering(df)

    # 3. Détection colonne label
    target_col = find_target_column(df)
    if target_col is None:
        print("[ETL] ERROR: No label column found", flush=True)
        return None, None, None
    print(f"[ETL] Label column: '{target_col}'", flush=True)

    # 4. Extraction labels
    y = normalize_label(df[target_col].values).astype(np.int8)

    # 5. Drop colonnes label
    cols_to_drop = list(set(
        [c for c in EXCLUDE_LABELS if c in df.columns] + [target_col]
    ))
    df.drop(columns=cols_to_drop, errors="ignore", inplace=True)

    # 6. Garder numériques uniquement
    df = df.select_dtypes(include=np.number).fillna(0)

    # 7. Supprimer colonnes constantes
    constant = [c for c in df.columns if df[c].nunique() <= 1]
    if constant:
        df.drop(columns=constant, inplace=True)
        print(f"[ETL] Constant cols removed: {len(constant)}", flush=True)

    feature_cols = df.columns.tolist()
    joblib.dump(feature_cols, FEATURES_PATH)
    print(f"[ETL] Features: {len(feature_cols)}", flush=True)

    # 8. Downcast — après select_dtypes, jamais avant
    df = downcast_numeric_features(df)
    print("[ETL] Dtypes downcasted -> float32/int32", flush=True)

    # 9. Conversion numpy
    X = df.values.astype(np.float32)
    del df

    # 10. StandardScaler partial_fit chunk-by-chunk
    if apply_scaler:
        scaler = StandardScaler()
        n = len(X)
        for start in range(0, n, CHUNK_SIZE):
            scaler.partial_fit(X[start : start + CHUNK_SIZE])
        for start in range(0, n, CHUNK_SIZE):
            end = min(start + CHUNK_SIZE, n)
            X[start:end] = scaler.transform(X[start:end])
        joblib.dump(scaler, SCALER_PATH)
        print("[ETL] StandardScaler saved", flush=True)

    print(
        f"[ETL] DONE — X:{X.shape} y:{y.shape} "
        f"BENIGN:{(y==0).sum():,} ATTACK:{(y==1).sum():,}",
        flush=True,
    )
    return X, y, feature_cols