import json
import os
from datetime import datetime
import numpy as np

from config import MONGO_URI, MONGO_DB, MONGO_COLL

# ── Collection / table names
COLL_EXPERIMENTS = MONGO_COLL            # "experiments"
COLL_DATASETS    = "datasets"
COLL_REPORTS     = "reports"

JSON_EXPERIMENTS = "results/experiments.json"
JSON_DATASETS    = "results/datasets.json"
JSON_REPORTS     = "results/reports.json"

#  CONNECTION

def _mongo_client():
    from pymongo import MongoClient
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)

def is_mongo_available():
    try:
        _mongo_client().server_info()
        return True
    except Exception:
        return False

def is_connected():
    return is_mongo_available()


#   HELPERS

def _safe(v):
    if isinstance(v, np.integer):  return int(v)
    if isinstance(v, np.floating): return float(v)
    if isinstance(v, np.ndarray):  return v.tolist()
    return v

def _clean_name(name: str) -> str:
    """Nettoie le nom du dataset : retire extension, espaces → _"""
    name = os.path.splitext(os.path.basename(name))[0]
    return name.strip().replace(" ", "_").lower()

def _version_key(dataset_name: str, model_name: str) -> str:
    return f"{_clean_name(dataset_name)}__{model_name.replace(' ', '_').lower()}"

def _ensure_dirs():
    os.makedirs("results", exist_ok=True)


#   JSON HELPERS

def _json_load(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _json_save(path: str, data: list):
    _ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

#   DATASET TABLE

def _get_or_create_dataset(dataset_name: str, dataset_info: dict) -> str:
    """
    Upsert dataset dans la table datasets.
    Retourne le dataset_id (clean_name).
    """
    clean = _clean_name(dataset_name)
    now   = datetime.now().isoformat(timespec="seconds")

    doc = {
        "dataset_id"    : clean,
        "original_name" : dataset_name,
        "clean_name"    : clean,
        "first_seen"    : now,
        "last_seen"     : now,
        "total_rows"    : dataset_info.get("total_rows",   0),
        "total_cols"    : dataset_info.get("total_cols",   0),
        "benign_count"  : dataset_info.get("benign_count", 0),
        "attack_count"  : dataset_info.get("attack_count", 0),
        "run_count"     : 1,
    }

    if is_mongo_available():
        from pymongo import MongoClient
        col = _mongo_client()[MONGO_DB][COLL_DATASETS]
        existing = col.find_one({"dataset_id": clean})
        if existing:
            col.update_one(
                {"dataset_id": clean},
                {"$set": {"last_seen": now,
                           "total_rows": doc["total_rows"],
                           "total_cols": doc["total_cols"]},
                 "$inc": {"run_count": 1}}
            )
        else:
            col.insert_one(doc)
    else:
        _ensure_dirs()
        data = _json_load(JSON_DATASETS)
        existing = next((d for d in data if d.get("dataset_id") == clean), None)
        if existing:
            existing["last_seen"]  = now
            existing["run_count"]  = existing.get("run_count", 0) + 1
            existing["total_rows"] = doc["total_rows"]
            existing["total_cols"] = doc["total_cols"]
        else:
            data.append(doc)
        _json_save(JSON_DATASETS, data)

    return clean

#   REPORT TABLE

def save_report_record(
    run_id       : str,
    dataset_id   : str,
    model_name   : str,
    version      : int,
    report_path  : str,
    report_text  : str,
) -> str:
    """Sauvegarde les métadonnées du rapport + texte dans la table reports."""
    now       = datetime.now().isoformat(timespec="seconds")
    report_id = f"rep__{run_id}"

    doc = {
        "report_id"   : report_id,
        "run_id"      : run_id,
        "dataset_id"  : dataset_id,
        "model_name"  : model_name,
        "version"     : version,
        "generated_at": now,
        "file_path"   : report_path,
        "report_text" : report_text,  # texte complet stocké en DB
    }

    if is_mongo_available():
        from pymongo import MongoClient
        col = _mongo_client()[MONGO_DB][COLL_REPORTS]
        col.replace_one({"report_id": report_id}, doc, upsert=True)
    else:
        _ensure_dirs()
        data = _json_load(JSON_REPORTS)
        data = [r for r in data if r.get("report_id") != report_id]
        data.append(doc)
        _json_save(JSON_REPORTS, data)

    return report_id

#   BUILD EXPERIMENT DOCUMENT

def _build_document(dataset_name, model_name, params, metrics,
                    cm, feature_cols, dataset_info, version, report_text):

    tn = int(cm[0][0]); fp = int(cm[0][1])
    fn = int(cm[1][0]); tp = int(cm[1][1])
    total_att    = tp + fn
    total_benign = tn + fp
    clean_ds     = _clean_name(dataset_name)
    now          = datetime.now().isoformat(timespec="seconds")

    run_id = f"{clean_ds}__{model_name.replace(' ','_').lower()}__v{version}"

    return {
        #Identity
        "version_key"  : _version_key(dataset_name, model_name),
        "version"      : version,
        "run_id"       : run_id,
        "date"         : now,

        #Dataset (référence + snapshot)
        "dataset_id"   : clean_ds,
        "dataset": {
            "raw_filename"  : dataset_name,
            "clean_name"    : clean_ds,
            "total_rows"    : dataset_info.get("total_rows",   0),
            "total_cols"    : dataset_info.get("total_cols",   0),
            "benign_count"  : dataset_info.get("benign_count", 0),
            "attack_count"  : dataset_info.get("attack_count", 0),
            "train_rows"    : dataset_info.get("train_rows",   0),
            "test_rows"     : dataset_info.get("test_rows",    0),
            "n_features"    : dataset_info.get("n_features",   0),
        },

        #Modèle
        "model_name"   : model_name,
        "params"       : {k: _safe(v) for k, v in params.items()},

        #Métriques
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

        #Matrice de confusion
        "confusion_matrix": {
            "TP": tp, "TN": tn, "FP": fp, "FN": fn,
            "total_attacks"  : total_att,
            "total_benign"   : total_benign,
            "miss_rate_pct"  : round(fn / total_att    * 100, 4) if total_att    > 0 else 0,
            "false_alarm_pct": round(fp / total_benign * 100, 4) if total_benign > 0 else 0,
        },

        #Rapport (référence + texte)
        "report_id"    : f"rep__{run_id}",
        "report_text"  : report_text or "",

        #Features
        "feature_cols" : (feature_cols or [])[:20],
    }

#   SAVE EXPERIMENT (entrée principale)

def save_experiment(dataset_name, model_name, params, metrics,
                    cm, feature_cols=None, dataset_info=None,
                    report_text=None, report_path=None):
    """
    Sauvegarde complète :
      1. Upsert table datasets
      2. Insert experiment avec versioning
      3. Insert table reports
    Retourne (run_id, version)
    """
    if dataset_info is None: dataset_info = {}
    if feature_cols is None: feature_cols = []
    if report_text  is None:
        try:
            with open("results/stdout.txt", "r", encoding="utf-8") as f:
                report_text = f.read()
        except Exception:
            report_text = ""

    # 1Dataset table
    dataset_id = _get_or_create_dataset(dataset_name, dataset_info)

    # 2Versioning
    vkey = _version_key(dataset_name, model_name)
    if is_mongo_available():
        from pymongo import MongoClient, DESCENDING
        col  = _mongo_client()[MONGO_DB][COLL_EXPERIMENTS]
        last = col.find_one({"version_key": vkey}, sort=[("version", DESCENDING)])
        version = 1 if not last else last["version"] + 1
    else:
        data    = _json_load(JSON_EXPERIMENTS)
        version = sum(1 for e in data if e.get("version_key") == vkey) + 1

    # 3Build & save experiment
    doc = _build_document(dataset_name, model_name, params, metrics,
                          cm, feature_cols, dataset_info, version, report_text)

    if is_mongo_available():
        from pymongo import MongoClient
        _mongo_client()[MONGO_DB][COLL_EXPERIMENTS].insert_one(doc)
        print(f"[DB] MongoDB — saved {doc['run_id']}")
    else:
        data = _json_load(JSON_EXPERIMENTS)
        data.append(doc)
        _json_save(JSON_EXPERIMENTS, data)
        print(f"[DB] JSON — saved {doc['run_id']}")

    # 4Report table
    if report_path:
        save_report_record(
            run_id      = doc["run_id"],
            dataset_id  = dataset_id,
            model_name  = model_name,
            version     = version,
            report_path = report_path,
            report_text = report_text,
        )

    return doc["run_id"], version

#   READ — EXPERIMENTS

def get_all_experiments(limit: int = None):
    if is_mongo_available():
        from pymongo import MongoClient, DESCENDING
        col    = _mongo_client()[MONGO_DB][COLL_EXPERIMENTS]
        cursor = col.find({}, {"_id": 0}).sort("date", DESCENDING)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    data = sorted(_json_load(JSON_EXPERIMENTS),
                  key=lambda x: x.get("date", ""), reverse=True)
    return data[:limit] if limit else data

def get_latest_experiment():
    data = get_all_experiments()
    return data[0] if data else None

def get_best_experiment(metric="recall"):
    data = get_all_experiments()
    if not data: return None
    return max(data, key=lambda x: x.get("metrics", {}).get(metric, 0))

def get_experiments_by_dataset(dataset_name: str):
    clean = _clean_name(dataset_name)
    return [e for e in get_all_experiments()
            if e.get("dataset_id") == clean]

def get_experiments_by_model(model_name: str):
    return [e for e in get_all_experiments()
            if e.get("model_name") == model_name]

def get_versions(dataset_name: str, model_name: str):
    vkey = _version_key(dataset_name, model_name)
    return [e for e in get_all_experiments()
            if e.get("version_key") == vkey]

#   READ — DATASETS

def get_all_datasets():
    """Retourne tous les datasets enregistrés."""
    if is_mongo_available():
        from pymongo import MongoClient
        col = _mongo_client()[MONGO_DB][COLL_DATASETS]
        return list(col.find({}, {"_id": 0}))
    return _json_load(JSON_DATASETS)

def get_dataset(dataset_id: str):
    if is_mongo_available():
        from pymongo import MongoClient
        col = _mongo_client()[MONGO_DB][COLL_DATASETS]
        return col.find_one({"dataset_id": dataset_id}, {"_id": 0})
    data = _json_load(JSON_DATASETS)
    return next((d for d in data if d.get("dataset_id") == dataset_id), None)

#   READ — REPORTS

def get_all_reports():
    if is_mongo_available():
        from pymongo import MongoClient, DESCENDING
        col = _mongo_client()[MONGO_DB][COLL_REPORTS]
        return list(col.find({}, {"_id": 0}).sort("generated_at", DESCENDING))
    return sorted(_json_load(JSON_REPORTS),
                  key=lambda x: x.get("generated_at", ""), reverse=True)

def get_report_by_run(run_id: str):
    if is_mongo_available():
        from pymongo import MongoClient
        col = _mongo_client()[MONGO_DB][COLL_REPORTS]
        return col.find_one({"run_id": run_id}, {"_id": 0})
    data = _json_load(JSON_REPORTS)
    return next((r for r in data if r.get("run_id") == run_id), None)

def get_reports_by_dataset(dataset_id: str):
    return [r for r in get_all_reports()
            if r.get("dataset_id") == dataset_id]

#   DELETE

def delete_all():
    if is_mongo_available():
        from pymongo import MongoClient
        db = _mongo_client()[MONGO_DB]
        db[COLL_EXPERIMENTS].delete_many({})
        db[COLL_DATASETS].delete_many({})
        db[COLL_REPORTS].delete_many({})
        print("[DB] MongoDB — all collections cleared")
    _json_save(JSON_EXPERIMENTS, [])
    _json_save(JSON_DATASETS,    [])
    _json_save(JSON_REPORTS,     [])
    print("[DB] JSON — all files cleared")