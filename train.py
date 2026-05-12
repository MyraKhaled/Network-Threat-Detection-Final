# ══════════════════════════════════════════════════════════════
#   train.py — Main Training Script v3.1
#   Appelé par app.py via subprocess
#   Stdout JSON en temps réel → Streamlit
#
#   FIXES v3.1 :
#   ✅ import etl (pas run_etl — nom de fichier correct)
#   ✅ save_experiment() synchronisé avec db.py v3
#      signature : (dataset_name, model_name, params, metrics,
#                   cm, feature_cols, dataset_info,
#                   report_text, report_path)
#   ✅ version calculée via db avant génération rapport
#   ✅ report_filename émis dans "complete" pour dl auto
# ══════════════════════════════════════════════════════════════

import sys
import json
import time
import os
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.tree            import DecisionTreeClassifier
from sklearn.ensemble        import RandomForestClassifier, IsolationForest
from xgboost                 import XGBClassifier
from sklearn.metrics         import (
    accuracy_score, precision_score,
    recall_score, f1_score,
    confusion_matrix, roc_curve, auc,
    classification_report
)

# Import correct — le fichier s'appelle etl.py
from run_etl              import run_etl
from db               import save_experiment, is_connected
from report_generator import generate_report, get_report_filename
from config import MODELS_PATH, REPORTS_PATH, PLOTS_PATH, EXPERIMENT_NAME


# ════════════════════════════════════════
#   HELPERS
# ════════════════════════════════════════

def emit(data: dict):
    print(json.dumps(data), flush=True)

def ensure_dirs():
    for d in [MODELS_PATH, REPORTS_PATH, PLOTS_PATH, "data"]:
        os.makedirs(d, exist_ok=True)

def save_cm_plot(cm_matrix, model_name):
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(
        cm_matrix, annot=True, fmt="d", cmap="Blues",
        xticklabels=["BENIGN", "ATTACK"],
        yticklabels=["BENIGN", "ATTACK"],
        ax=ax
    )
    ax.set_title(f"Confusion Matrix — {model_name}", fontsize=12, fontweight="bold")
    ax.set_ylabel("Actual")
    ax.set_xlabel("Predicted")
    plt.tight_layout()
    safe = model_name.lower().replace(" ", "_")
    path = os.path.join(PLOTS_PATH, f"cm_{safe}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path

def _get_next_version(dataset_name: str, model_type: str) -> int:
    """Calcule la prochaine version sans toucher à la DB."""
    from db import _version_key, _json_load, JSON_EXPERIMENTS, is_mongo_available
    vkey = _version_key(dataset_name, model_type)
    if is_mongo_available():
        from pymongo import MongoClient, DESCENDING
        from config import MONGO_URI, MONGO_DB, MONGO_COLL
        col  = MongoClient(MONGO_URI)[MONGO_DB][MONGO_COLL]
        last = col.find_one({"version_key": vkey}, sort=[("version", DESCENDING)])
        return 1 if not last else last["version"] + 1
    else:
        data = _json_load(JSON_EXPERIMENTS)
        return sum(1 for e in data if e.get("version_key") == vkey) + 1


#   MAIN TRAIN

def train(config: dict):
    ensure_dirs()
    model_type = config["model_type"]
    t_total    = time.time()

    # ── 1. Started
    emit({"status": "started", "model": model_type,
          "time": time.strftime("%H:%M:%S")})

    # ── 2. Load CSV chunked (anti-OOM)
    emit({"status": "loading"})
    try:
        chunks = []
        for chunk in pd.read_csv(
            config["data_path"],
            low_memory      = False,
            chunksize       = 50_000,
            on_bad_lines    = "skip",
            encoding_errors = "replace",
        ):
            chunk.columns = chunk.columns.str.strip()
            chunks.append(chunk)
        df_raw = pd.concat(chunks, ignore_index=True)
        del chunks
        emit({"status": "loaded",
              "rows": int(df_raw.shape[0]),
              "cols": int(df_raw.shape[1])})
    except Exception as e:
        emit({"status": "error", "msg": f"Cannot read CSV: {e}"})
        sys.exit(1)

    if df_raw.empty:
        emit({"status": "error", "msg": "Le fichier CSV est vide."})
        sys.exit(1)

    # ── 3. ETL
    emit({"status": "etl_running"})
    try:
        X, y, feature_cols = run_etl(df_raw)
    except Exception as e:
        emit({"status": "error", "msg": f"ETL exception: {e}"})
        sys.exit(1)

    if X is None or y is None:
        emit({"status": "error", "msg": "ETL échoué — colonne label introuvable"})
        sys.exit(1)

    if len(np.unique(y)) < 2:
        emit({"status": "error",
              "msg": "Une seule classe dans les données — besoin de BENIGN et ATTACK"})
        sys.exit(1)

    emit({"status": "etl_done",
          "rows": int(X.shape[0]),
          "features": int(X.shape[1]),
          "benign": int((y == 0).sum()),
          "attack": int((y == 1).sum())})

    # ── 4. Split
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size    = float(config.get("test_size",    0.2)),
            random_state = int(config.get("random_state",   42)),
            stratify     = y,
        )
    except Exception as e:
        emit({"status": "error", "msg": f"Split échoué: {e}"})
        sys.exit(1)

    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    spw = round(neg / pos, 4) if pos > 0 else 1.0

    emit({"status": "split_done",
          "train_rows": int(X_train.shape[0]),
          "test_rows" : int(X_test.shape[0]),
          "features"  : int(X_train.shape[1])})

    # ── 5. Entraînement
    emit({"status": "training_started", "model": model_type})
    t0 = time.time()

    try:
        if model_type == "Decision Tree":
            cw = config.get("dt_class_weight", "balanced")
            model = DecisionTreeClassifier(
                max_depth         = int(config.get("dt_max_depth",          15)),
                class_weight      = None if cw == "None" else cw,
                min_samples_split = int(config.get("dt_min_samples_split",   2)),
                min_samples_leaf  = int(config.get("dt_min_samples_leaf",    1)),
                random_state      = int(config.get("random_state",           42)),
            )
            model.fit(X_train, y_train)

        elif model_type == "Random Forest":
            cw = config.get("rf_class_weight", "balanced")
            model = RandomForestClassifier(
                n_estimators      = int(config.get("rf_n_estimators",        90)),
                max_depth         = int(config.get("rf_max_depth",           25)),
                class_weight      = None if cw == "None" else cw,
                min_samples_split = int(config.get("rf_min_samples_split",    2)),
                min_samples_leaf  = int(config.get("rf_min_samples_leaf",     1)),
                random_state      = int(config.get("random_state",            42)),
                n_jobs            = -1,
            )
            model.fit(X_train, y_train)

        elif model_type == "XGBoost":
            model = XGBClassifier(
                n_estimators     = int(config.get("xgb_n_estimators",       200)),
                max_depth        = int(config.get("xgb_max_depth",            12)),
                learning_rate    = float(config.get("xgb_learning_rate",     0.1)),
                alpha            = float(config.get("xgb_alpha",              1.0)),
                gamma            = float(config.get("xgb_gamma",              0.2)),
                subsample        = float(config.get("xgb_subsample",          1.0)),
                reg_lambda       = float(config.get("xgb_reg_lambda",         1.0)),
                scale_pos_weight = spw,
                objective        = "binary:logistic",
                eval_metric      = "logloss",
                random_state     = int(config.get("random_state",             42)),
                n_jobs           = -1,
            )
            model.fit(X_train, y_train,
                      eval_set=[(X_test, y_test)], verbose=False)

        elif model_type == "Isolation Forest":
            model = IsolationForest(
                n_estimators  = int(config.get("iso_n_estimators",          200)),
                contamination = float(config.get("iso_contamination",       0.17)),
                random_state  = int(config.get("random_state",               42)),
                n_jobs        = -1,
            )
            model.fit(X_train[y_train == 0])

        else:
            emit({"status": "error", "msg": f"Modèle inconnu: {model_type}"})
            sys.exit(1)

    except MemoryError:
        emit({"status": "error",
              "msg": "Out of memory — réduire Trees/Max depth ou utiliser un dataset plus petit."})
        sys.exit(1)
    except Exception as e:
        emit({"status": "error", "msg": f"Erreur d'entraînement: {e}"})
        sys.exit(1)

    train_time = round(time.time() - t0, 2)
    emit({"status": "training_done", "model": model_type, "train_time": train_time})

    # ── 6. Évaluation
    try:
        if model_type == "Isolation Forest":
            y_pred = np.where(model.predict(X_test) == -1, 1, 0)
            y_prob = None
        else:
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1]

        acc  = accuracy_score (y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec  = recall_score   (y_test, y_pred, zero_division=0)
        f1   = f1_score       (y_test, y_pred, zero_division=0)
        cm   = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
    except Exception as e:
        emit({"status": "error", "msg": f"Évaluation échouée: {e}"})
        sys.exit(1)

    # ROC
    roc_auc = None
    fpr_list = []
    tpr_list = []
    if y_prob is not None:
        try:
            fpr_arr, tpr_arr, _ = roc_curve(y_test, y_prob)
            roc_auc  = round(float(auc(fpr_arr, tpr_arr)), 4)
            step     = max(1, len(fpr_arr) // 500)
            fpr_list = [round(float(v), 4) for v in fpr_arr[::step]]
            tpr_list = [round(float(v), 4) for v in tpr_arr[::step]]
        except Exception:
            pass

    # Overfitting
    try:
        if model_type == "Isolation Forest":
            train_pred = np.where(model.predict(X_train) == -1, 1, 0)
        else:
            train_pred = model.predict(X_train)
        train_acc = round(float(accuracy_score(y_train, train_pred)), 4)
    except Exception:
        train_acc = 0.0

    test_acc = round(float(acc), 4)
    gap      = round(abs(train_acc - test_acc), 4)
    overfit  = gap > 0.05

    metrics = {
        "accuracy"   : round(float(acc),  4),
        "precision"  : round(float(prec), 4),
        "recall"     : round(float(rec),  4),
        "f1"         : round(float(f1),   4),
        "roc_auc"    : roc_auc,
        "time"       : train_time,
        "train_acc"  : train_acc,
        "test_acc"   : test_acc,
        "gap"        : gap,
        "overfitting": overfit,
    }

    emit({
        "status"          : "results",
        "metrics"         : metrics,
        "confusion_matrix": {"TP": int(tp), "TN": int(tn),
                             "FP": int(fp), "FN": int(fn)},
        "roc_curve"       : {"fpr": fpr_list, "tpr": tpr_list},
    })

    # ── 7. CM plot
    try:
        cm_path = save_cm_plot(cm, model_type)
        emit({"status": "plot_saved", "path": cm_path})
    except Exception as e:
        cm_path = ""
        emit({"status": "plot_warning", "msg": str(e)})

    # ── 8. Feature importance
    fi_data = {}
    if hasattr(model, "feature_importances_"):
        try:
            imp   = model.feature_importances_
            top10 = sorted(zip(feature_cols, imp),
                           key=lambda x: x[1], reverse=True)[:10]
            fi_data = {k: round(float(v), 6) for k, v in top10}
            emit({"status": "feature_importance", "top10": fi_data})
        except Exception:
            pass

    # ── 9. Save model .pkl
    try:
        safe_name  = model_type.lower().replace(" ", "_")
        model_path = os.path.join(MODELS_PATH, f"model_{safe_name}.pkl")
        joblib.dump(model, model_path)
        emit({"status": "model_saved", "path": model_path})
    except Exception as e:
        model_path = ""
        emit({"status": "model_warning", "msg": str(e)})

    # ── 10. Dataset name + infos
    dataset_name = config.get("dataset_name") or os.path.basename(
        config.get("data_path", "uploaded.csv")
    )
    dataset_name = os.path.splitext(dataset_name)[0]

    dataset_info = {
        "total_rows"   : int(df_raw.shape[0]),
        "total_cols"   : int(df_raw.shape[1]),
        "benign_count" : int((y == 0).sum()),
        "attack_count" : int((y == 1).sum()),
        "train_rows"   : int(X_train.shape[0]),
        "test_rows"    : int(X_test.shape[0]),
        "n_features"   : int(X_train.shape[1]),
    }

    # 11. Calculer version AVANT rapport (pour inclure dans le rapport)
    version = _get_next_version(dataset_name, model_type)

    #  12. Génération rapport complet
    cm_dict = {"TP": int(tp), "TN": int(tn), "FP": int(fp), "FN": int(fn)}
    try:
        report_path, report_bytes = generate_report(
            model_type   = model_type,
            config       = config,
            metrics      = metrics,
            cm           = cm_dict,
            fi_data      = fi_data,
            dataset_info = dataset_info,
            dataset_name = dataset_name,
            version      = version,
            y_test       = y_test,
            y_pred       = y_pred,
        )
        emit({"status": "report_saved", "path": report_path})
    except Exception as e:
        report_path  = ""
        report_bytes = b""
        emit({"status": "report_warning", "msg": str(e)})

    #  13. Sauvegarde DB (experiments + datasets + reports)
    try:
        params_used = {k: v for k, v in config.items() if k != "data_path"}
        run_id, version = save_experiment(
            dataset_name = dataset_name,
            model_name   = model_type,
            params       = params_used,
            metrics      = metrics,
            cm           = cm,
            feature_cols = feature_cols,
            dataset_info = dataset_info,
            report_text  = report_bytes.decode("utf-8") if report_bytes else "",
            report_path  = report_path,
        )
        db_type = "MongoDB" if is_connected() else "JSON"
        emit({"status": "db_saved", "db": db_type, "run_id": run_id})
    except Exception as e:
        run_id  = f"{dataset_name}__{model_type.replace(' ','_').lower()}__v{version}"
        emit({"status": "db_warning", "msg": str(e)})

    # ── 14. MLflow
    try:
        import mlflow, mlflow.sklearn, mlflow.xgboost
        mlflow.set_experiment(EXPERIMENT_NAME)
        with mlflow.start_run(run_name=f"{model_type}_v{version}"):
            mlflow.log_params({k: v for k, v in config.items() if k != "data_path"})
            mlflow.log_metrics({
                "accuracy" : float(acc),  "precision": float(prec),
                "recall"   : float(rec),  "f1_score" : float(f1),
                "train_acc": float(train_acc), "gap": float(gap),
                "TP": int(tp), "TN": int(tn), "FP": int(fp), "FN": int(fn),
                "train_time": float(train_time),
            })
            if roc_auc:
                mlflow.log_metric("roc_auc", float(roc_auc))
            if model_type == "XGBoost":
                mlflow.xgboost.log_model(model, "model")
            else:
                mlflow.sklearn.log_model(model, "model")
            if report_path and os.path.exists(report_path):
                mlflow.log_artifact(report_path)
            if cm_path and os.path.exists(cm_path):
                mlflow.log_artifact(cm_path)
        emit({"status": "mlflow_logged"})
    except Exception as e:
        emit({"status": "mlflow_warning", "msg": str(e)})

    # ── 15. Complete
    report_filename = get_report_filename(dataset_name, model_type, version)
    emit({
        "status"          : "complete",
        "model"           : model_type,
        "recall"          : metrics["recall"],
        "f1"              : metrics["f1"],
        "total_time"      : round(time.time() - t_total, 2),
        "version"         : version,
        "run_id"          : run_id,
        "report_path"     : report_path,
        "report_filename" : report_filename,
    })

    return metrics, cm


# ════════════════════════════════════════
#   ENTRY POINT
# ════════════════════════════════════════
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error",
                          "msg": "Usage: python train.py '<config_json>'"}))
        sys.exit(1)
    config = json.loads(sys.argv[1])
    train(config)