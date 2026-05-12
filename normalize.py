# ══════════════════════════════════════════════════════════════
#   normalize.py v3.3
#   FIX : errors='ignore' → errors='coerce' (FutureWarning)
#   FIX : lecture CSV streaming direct sur disque (pas de buffer RAM)
# ══════════════════════════════════════════════════════════════

import pandas as pd
import numpy  as np
import os
import io

CHUNK_SIZE = 50_000


def normalize_to_csv(uploaded_file, save_path: str = "data/uploaded.csv") -> str:
    os.makedirs("data", exist_ok=True)
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return _read_csv_chunked(uploaded_file, save_path)
    elif filename.endswith(".json"):
        return _read_json(uploaded_file, save_path)
    elif filename.endswith((".xlsx", ".xls")):
        return _read_excel(uploaded_file, save_path)
    else:
        raise ValueError(f"Format non supporté : {filename}\nFormats acceptés : CSV, JSON, XLSX")


def _read_csv_chunked(uploaded_file, save_path: str) -> str:
    """
    Écrit le fichier uploadé sur disque d'abord,
    puis lit chunk par chunk depuis le disque.
    Évite d'allouer le fichier entier en RAM.
    """
    # ── Étape 1 : écriture raw sur disque (streaming, pas de concat RAM)
    raw_path = save_path + ".raw.csv"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(raw_path, "wb") as f:
        while True:
            chunk = uploaded_file.read(1024 * 1024)  # 1 MB à la fois
            if not chunk:
                break
            f.write(chunk)

    # ── Étape 2 : lecture + nettoyage chunk par chunk depuis le fichier disque
    read_kwargs = dict(
        low_memory        = False,
        chunksize         = CHUNK_SIZE,
        on_bad_lines      = "skip",
        encoding_errors   = "replace",
        encoding          = "utf-8",
    )

    try:
        first = True
        total = 0
        with open(save_path, "w", encoding="utf-8", newline="") as out_f:
            for chunk in pd.read_csv(raw_path, **read_kwargs):
                chunk = _clean_chunk(chunk)
                chunk.to_csv(out_f, index=False, header=first)
                first  = False
                total += len(chunk)
        os.remove(raw_path)
        print(f"[NORMALIZE] CSV → {save_path}  ({total:,} lignes)")
        return save_path

    except Exception as e1:
        # Fallback : latin-1 encoding
        try:
            first = True
            total = 0
            with open(save_path, "w", encoding="utf-8", newline="") as out_f:
                for chunk in pd.read_csv(
                    raw_path,
                    low_memory      = False,
                    chunksize       = CHUNK_SIZE,
                    on_bad_lines    = "skip",
                    encoding        = "latin-1",
                    encoding_errors = "replace",
                ):
                    chunk = _clean_chunk(chunk)
                    chunk.to_csv(out_f, index=False, header=first)
                    first  = False
                    total += len(chunk)
            os.remove(raw_path)
            print(f"[NORMALIZE] CSV (latin-1) → {save_path}  ({total:,} lignes)")
            return save_path
        except Exception as e2:
            try:
                os.remove(raw_path)
            except Exception:
                pass
            raise ValueError(f"Impossible de lire le CSV : {e1} | {e2}")


def _read_json(uploaded_file, save_path: str) -> str:
    try:
        df = pd.read_json(uploaded_file)
    except ValueError:
        uploaded_file.seek(0)
        df = pd.read_json(uploaded_file, lines=True)
    df.columns = df.columns.str.strip()
    df.to_csv(save_path, index=False)
    print(f"[NORMALIZE] JSON → {save_path}  ({len(df):,} lignes)")
    return save_path


def _read_excel(uploaded_file, save_path: str) -> str:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    df.to_csv(save_path, index=False)
    print(f"[NORMALIZE] Excel → {save_path}  ({len(df):,} lignes)")
    return save_path


def _clean_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk.columns = chunk.columns.str.strip()
    for col in chunk.columns:
        try:
            # FIX : errors='coerce' au lieu de errors='ignore' (FutureWarning)
            converted = pd.to_numeric(chunk[col], errors="coerce")
            # Garder la conversion seulement si au moins 80% des valeurs sont numériques
            non_null  = converted.notna().sum()
            if non_null / max(len(chunk), 1) >= 0.8:
                chunk[col] = converted
        except Exception:
            pass
    return chunk