# ══════════════════════════════════════════════════════════════
#   db.py — Database Layer
#   Primary  : MongoDB
#   Fallback : JSON file (if MongoDB not available)
#   Stores dataset info + model results + versioning
# ══════════════════════════════════════════════════════════════

import json
import os
from datetime import datetime
import numpy as np

from config import MONGO_URI, MONGO_DB, MONGO_COLL

# JSON fallback path
JSON_DB = "results/experiments.json"


# ════════════════════════════════════════
#   CONNECTION CHECK
# ════════════════════════════════════════

def is_mongo_available():
    try:
        from pymongo import MongoClient
        c = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        c.server_info()
        return True
    except Exception:
        return False


def is_connected():
    return is_mongo_available()


# ════════════════════════════════════════
#   HELPERS
# ════════════════════════════════════════

def _safe(v):
    """Convert numpy types to Python native."""
    if isinstance(v, (np.integer,)):  return int(v)
    if isinstance(v, (np.floating,)): return float(v)
    if isinstance(v, np.ndarray):     return v.tolist()
    return v


def _build_document(model_name, params, metrics, cm,
                    feature_cols, dataset_info, version):
    """Build the experiment document to store."""

    tn = int(cm[0][0])
    fp = int(cm[0][1])
    fn = int(cm[1][0])
    tp = int(cm[1][1])

    total_attacks = tp + fn
    total_benign  = tn + fp

    return {
        "model_name"  : model_name,
        "version"     : version,
        "date"        : datetime.now().isoformat(timespec="seconds"),

        # ── Dataset info
        "dataset": {
            "filename"      : dataset_info.get("filename",   "unknown"),
            "total_rows"    : dataset_info.get("total_rows",  0),
            "total_cols"    : dataset_info.get("total_cols",  0),
            "benign_count"  : dataset_info.get("benign_count", 0),
            "attack_count"  : dataset_info.get("attack_count", 0),
            "train_rows"    : dataset_info.get("train_rows",   0),
            "test_rows"     : dataset_info.get("test_rows",    0),
            "n_features"    : len(feature_cols) if feature_cols else 0,
        },

        # ── Parameters used
        "params": {k: _safe(v) for k, v in params.items()},

        # ── Metrics
        "metrics": {
            "accuracy"      : round(float(metrics.get("accuracy",  0)), 6),
            "precision"     : round(float(metrics.get("precision", 0)), 6),
            "recall"        : round(float(metrics.get("recall",    0)), 6),
            "f1_score"      : round(float(metrics.get("f1",        0)), 6),
            "roc_auc"       : round(float(metrics.get("roc_auc") or 0), 6),
            "training_time" : round(float(metrics.get("time",      0)), 4),
            "train_accuracy": round(float(metrics.get("train_acc", 0)), 6),
            "gap"           : round(float(metrics.get("gap",       0)), 6),
            "overfitting"   : bool(metrics.get("overfitting", False)),
        },

        # ── Confusion matrix + derived stats
        "confusion_matrix": {
            "TP"            : tp,
            "TN"            : tn,
            "FP"            : fp,
            "FN"            : fn,
            "total_attacks" : total_attacks,
            "total_benign"  : total_benign,
            "miss_rate_pct" : round(fn / total_attacks * 100, 4) if total_attacks > 0 else 0,
            "false_alarm_pct": round(fp / total_benign * 100, 4) if total_benign > 0 else 0,
        },

        # ── Top features (first 20)
        "feature_cols": feature_cols[:20] if feature_cols else [],
    }


# ════════════════════════════════════════
#   SAVE
# ════════════════════════════════════════

def save_experiment(model_name, params, metrics, cm,
                    feature_cols=None, dataset_info=None):
    """
    Save experiment to MongoDB (or JSON fallback).

    Parameters
    ----------
    model_name   : str
    params       : dict — training parameters
    metrics      : dict — accuracy, precision, recall, f1, roc_auc, time
    cm           : np.ndarray (2×2) — confusion matrix
    feature_cols : list — feature names
    dataset_info : dict — filename, rows, cols, benign/attack counts

    Returns
    -------
    str — version identifier
    """
    if dataset_info is None:
        dataset_info = {}

    if is_mongo_available():
        return _save_mongo(model_name, params, metrics, cm,
                           feature_cols, dataset_info)
    else:
        return _save_json(model_name, params, metrics, cm,
                          feature_cols, dataset_info)


def _save_mongo(model_name, params, metrics, cm,
                feature_cols, dataset_info):
    from pymongo import MongoClient, DESCENDING
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db     = client[MONGO_DB]
    col    = db[MONGO_COLL]

    # Auto version
    last = col.find_one(
        {"model_name": model_name},
        sort=[("version", DESCENDING)]
    )
    version = 1 if not last else last["version"] + 1

    doc = _build_document(model_name, params, metrics, cm,
                          feature_cols, dataset_info, version)
    col.insert_one(doc)
    print(f"[DB] MongoDB — saved {model_name} v{version}")
    return f"{model_name}_v{version}"


def _save_json(model_name, params, metrics, cm,
               feature_cols, dataset_info):
    os.makedirs("results", exist_ok=True)
    data = _json_load()

    # Auto version
    version = sum(1 for e in data
                  if e["model_name"] == model_name) + 1

    doc = _build_document(model_name, params, metrics, cm,
                          feature_cols, dataset_info, version)
    data.append(doc)
    _json_save(data)
    print(f"[DB] JSON — saved {model_name} v{version}")
    return f"{model_name}_v{version}"


# ════════════════════════════════════════
#   READ
# ════════════════════════════════════════

def get_all_experiments():
    """Return all experiments sorted by date desc."""
    if is_mongo_available():
        from pymongo import MongoClient, DESCENDING
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db     = client[MONGO_DB]
        docs   = list(db[MONGO_COLL].find({}, {"_id": 0}).sort("date", DESCENDING))
        return docs
    else:
        data = _json_load()
        return sorted(data, key=lambda x: x.get("date", ""), reverse=True)


def get_best_experiment(metric="recall"):
    """Return experiment with highest value for given metric."""
    data = get_all_experiments()
    if not data:
        return None
    return max(data, key=lambda x: x.get("metrics", {}).get(metric, 0))


def get_experiments_by_model(model_name):
    """Return all runs for a specific model."""
    data = get_all_experiments()
    return [e for e in data if e.get("model_name") == model_name]


def delete_all():
    """Delete all experiments."""
    if is_mongo_available():
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI)
        client[MONGO_DB][MONGO_COLL].delete_many({})
        print("[DB] All MongoDB experiments deleted")
    _json_save([])
    print("[DB] JSON experiments cleared")


# ════════════════════════════════════════
#   JSON HELPERS
# ════════════════════════════════════════

def _json_load():
    if not os.path.exists(JSON_DB):
        return []
    with open(JSON_DB, "r", encoding="utf-8") as f:
        return json.load(f)


def _json_save(data):
    os.makedirs("results", exist_ok=True)
    with open(JSON_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)