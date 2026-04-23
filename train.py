# ══════════════════════════════════════════════════════════════
#   train.py — Main Training Script
#   Called by app.py via subprocess
#   Real-time JSON stdout → read by Streamlit
#   Based on Kaggle Section 3 + NVIDIA DLI Lab1
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

from run_etl import run_etl
from db  import save_experiment, is_connected
from config import (
    MODELS_PATH, REPORTS_PATH, PLOTS_PATH,
    EXPERIMENT_NAME
)


# ════════════════════════════════════════
#   HELPERS
# ════════════════════════════════════════

def emit(data: dict):
    """Print JSON line → Streamlit reads in real-time."""
    print(json.dumps(data), flush=True)


def ensure_dirs():
    for d in [MODELS_PATH, REPORTS_PATH, PLOTS_PATH, "data"]:
        os.makedirs(d, exist_ok=True)


def save_cm_plot(cm, model_name):
    """Save confusion matrix heatmap as PNG."""
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=["BENIGN", "ATTACK"],
        yticklabels=["BENIGN", "ATTACK"],
        ax=ax
    )
    ax.set_title(f"Confusion Matrix — {model_name}",
                 fontsize=12, fontweight="bold")
    ax.set_ylabel("Actual")
    ax.set_xlabel("Predicted")
    plt.tight_layout()
    safe = model_name.lower().replace(" ", "_")
    path = os.path.join(PLOTS_PATH, f"cm_{safe}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path


# ════════════════════════════════════════
#   MAIN TRAIN
# ════════════════════════════════════════

def train(config: dict):
    """
    Full training pipeline.

    config keys:
        model_type    : Decision Tree | Random Forest | XGBoost | Isolation Forest
        data_path     : path to CSV file
        test_size     : float (0.2)
        random_state  : int (42)

        # Decision Tree
        dt_max_depth, dt_class_weight,
        dt_min_samples_split, dt_min_samples_leaf

        # Random Forest
        rf_n_estimators, rf_max_depth, rf_class_weight,
        rf_min_samples_split, rf_min_samples_leaf

        # XGBoost
        xgb_n_estimators, xgb_max_depth, xgb_learning_rate,
        xgb_alpha, xgb_gamma, xgb_subsample, xgb_reg_lambda

        # Isolation Forest
        iso_n_estimators, iso_contamination
    """

    ensure_dirs()
    model_type = config["model_type"]
    t_total    = time.time()

    # ── 1. Started
    emit({"status": "started", "model": model_type,
          "time": time.strftime("%H:%M:%S")})

    # ── 2. Load CSV
    emit({"status": "loading"})
    try:
        df_raw = pd.read_csv(config["data_path"], low_memory=False)
        emit({"status": "loaded",
              "rows": int(df_raw.shape[0]),
              "cols": int(df_raw.shape[1])})
    except Exception as e:
        emit({"status": "error", "msg": f"Cannot read CSV: {e}"})
        sys.exit(1)

    # ── 3. ETL
    emit({"status": "etl_running"})
    X, y, feature_cols = run_etl(df_raw)

    if X is None or y is None:
        emit({"status": "error", "msg": "ETL failed — no labels found"})
        sys.exit(1)

    if len(np.unique(y)) < 2:
        emit({"status": "error", "msg": "Only 1 class in data — need BENIGN and ATTACK"})
        sys.exit(1)

    emit({"status": "etl_done",
          "rows": int(X.shape[0]),
          "features": int(X.shape[1]),
          "benign": int((y == 0).sum()),
          "attack": int((y == 1).sum())})

    # ── 4. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size    = float(config.get("test_size",    0.2)),
        random_state = int(config.get("random_state",    42)),
        stratify     = y
    )

    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    spw = round(neg / pos, 4) if pos > 0 else 1.0

    emit({
        "status"           : "split_done",
        "train_rows"       : int(X_train.shape[0]),
        "test_rows"        : int(X_test.shape[0]),
        "features"         : int(X_train.shape[1]),
        "benign_train"     : neg,
        "attack_train"     : pos,
        "scale_pos_weight" : spw
    })

    # ── 5. Build and train model
    emit({"status": "training_started", "model": model_type})
    t0 = time.time()

    if model_type == "Decision Tree":
        model = DecisionTreeClassifier(
            max_depth         = int(config.get("dt_max_depth",         15)),
            class_weight      = config.get("dt_class_weight",    "balanced"),
            min_samples_split = int(config.get("dt_min_samples_split",  2)),
            min_samples_leaf  = int(config.get("dt_min_samples_leaf",   1)),
            random_state      = int(config.get("random_state",         42))
        )
        model.fit(X_train, y_train)

    elif model_type == "Random Forest":
        model = RandomForestClassifier(
            n_estimators      = int(config.get("rf_n_estimators",      90)),
            max_depth         = int(config.get("rf_max_depth",         25)),
            class_weight      = config.get("rf_class_weight",    "balanced"),
            min_samples_split = int(config.get("rf_min_samples_split",  2)),
            min_samples_leaf  = int(config.get("rf_min_samples_leaf",   1)),
            random_state      = int(config.get("random_state",         42)),
            n_jobs            = -1
        )
        model.fit(X_train, y_train)

    elif model_type == "XGBoost":
        model = XGBClassifier(
            n_estimators     = int(config.get("xgb_n_estimators",   200)),
            max_depth        = int(config.get("xgb_max_depth",        12)),
            max_leaves       = int(config.get("xgb_max_leaves",     1024)),
            learning_rate    = float(config.get("xgb_learning_rate", 0.1)),
            alpha            = float(config.get("xgb_alpha",          1.0)),
            gamma            = float(config.get("xgb_gamma",          0.2)),
            subsample        = float(config.get("xgb_subsample",      1.0)),
            reg_lambda       = float(config.get("xgb_reg_lambda",     1.0)),
            scale_pos_weight = spw,
            objective        = "binary:logistic",
            eval_metric      = "logloss",
            random_state     = int(config.get("random_state",         42)),
            n_jobs           = -1
        )
        model.fit(X_train, y_train,
                  eval_set=[(X_test, y_test)],
                  verbose=False)

    elif model_type == "Isolation Forest":
        model = IsolationForest(
            n_estimators  = int(config.get("iso_n_estimators",    200)),
            contamination = float(config.get("iso_contamination", 0.17)),
            random_state  = int(config.get("random_state",          42)),
            n_jobs        = -1
        )
        # Unsupervised → train on BENIGN only
        X_train_benign = X_train[y_train == 0]
        model.fit(X_train_benign)

    else:
        emit({"status": "error", "msg": f"Unknown model: {model_type}"})
        sys.exit(1)

    train_time = round(time.time() - t0, 2)
    emit({"status": "training_done",
          "model": model_type,
          "train_time": train_time})

    # ── 6. Evaluate
    if model_type == "Isolation Forest":
        y_pred_raw = model.predict(X_test)
        y_pred     = np.where(y_pred_raw == -1, 1, 0)
        y_prob     = None
    else:
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test,   y_pred, zero_division=0)
    f1   = f1_score(y_test,       y_pred, zero_division=0)
    cm   = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    # ROC
    roc_auc  = None
    fpr_list = []
    tpr_list = []
    if y_prob is not None:
        fpr_arr, tpr_arr, _ = roc_curve(y_test, y_prob)
        roc_auc  = round(float(auc(fpr_arr, tpr_arr)), 4)
        fpr_list = [round(float(v), 4) for v in fpr_arr[::100]]
        tpr_list = [round(float(v), 4) for v in tpr_arr[::100]]

    # Overfitting check
    if model_type == "Isolation Forest":
        train_pred = np.where(model.predict(X_train) == -1, 1, 0)
    else:
        train_pred = model.predict(X_train)

    train_acc = round(float(accuracy_score(y_train, train_pred)), 4)
    test_acc  = round(float(acc), 4)
    gap       = round(abs(train_acc - test_acc), 4)
    overfit   = gap > 0.05

    metrics = {
        "accuracy"    : round(float(acc),  4),
        "precision"   : round(float(prec), 4),
        "recall"      : round(float(rec),  4),
        "f1"          : round(float(f1),   4),
        "roc_auc"     : roc_auc,
        "time"        : train_time,
        "train_acc"   : train_acc,
        "test_acc"    : test_acc,
        "gap"         : gap,
        "overfitting" : overfit
    }

    emit({
        "status"  : "results",
        "metrics" : metrics,
        "confusion_matrix": {
            "TP": int(tp), "TN": int(tn),
            "FP": int(fp), "FN": int(fn)
        },
        "roc_curve": {"fpr": fpr_list, "tpr": tpr_list}
    })

    # ── 7. Confusion matrix plot
    cm_path = save_cm_plot(cm, model_type)
    emit({"status": "plot_saved", "path": cm_path})

    # ── 8. Feature importance
    fi_data = {}
    if hasattr(model, "feature_importances_"):
        imp   = model.feature_importances_
        top10 = sorted(zip(feature_cols, imp),
                       key=lambda x: x[1], reverse=True)[:10]
        fi_data = {k: round(float(v), 6) for k, v in top10}
        emit({"status": "feature_importance", "top10": fi_data})

    # ── 9. Save model .pkl
    safe_name  = model_type.lower().replace(" ", "_")
    model_path = os.path.join(MODELS_PATH, f"model_{safe_name}.pkl")
    joblib.dump(model, model_path)
    emit({"status": "model_saved", "path": model_path})

    # ── 10. Build and save stdout.txt report
    total_attacks = int(tp) + int(fn)
    total_benign  = int(tn) + int(fp)
    miss_rate     = round(fn / total_attacks * 100, 2) if total_attacks > 0 else 0
    false_alarm   = round(fp / total_benign  * 100, 2) if total_benign  > 0 else 0
    clf_rep       = classification_report(
        y_test, y_pred,
        target_names=["BENIGN", "ATTACK"],
        digits=4
    )

    params_used = {k: v for k, v in config.items() if k != "data_path"}

    report_text = f"""
╔══════════════════════════════════════════════════════════════╗
║        TRAINING REPORT — {model_type:<34}║
╚══════════════════════════════════════════════════════════════╝

  Date            : {time.strftime("%Y-%m-%d %H:%M:%S")}
  Model           : {model_type}
  Dataset         : {config.get("data_path", "N/A")}

──────────────────────────────────────────────────────────────
  PARAMETERS USED
──────────────────────────────────────────────────────────────
{json.dumps(params_used, indent=4)}

──────────────────────────────────────────────────────────────
  DATASET SUMMARY
──────────────────────────────────────────────────────────────
  Total rows      : {df_raw.shape[0]:,}
  Total columns   : {df_raw.shape[1]}
  Features (ML)   : {X_train.shape[1]}
  Train rows      : {X_train.shape[0]:,}
  Test rows       : {X_test.shape[0]:,}
  BENIGN (train)  : {neg:,}
  ATTACK (train)  : {pos:,}
  scale_pos_weight: {spw}

──────────────────────────────────────────────────────────────
  METRICS
──────────────────────────────────────────────────────────────
  Accuracy        : {acc:.4f}  ({acc*100:.2f}%)
  Precision       : {prec:.4f}  ({prec*100:.2f}%)
  Recall    ⭐    : {rec:.4f}  ({rec*100:.2f}%)
  F1 Score        : {f1:.4f}  ({f1*100:.2f}%)
  ROC AUC         : {roc_auc if roc_auc else "N/A (unsupervised)"}
  Training time   : {train_time:.2f} seconds

──────────────────────────────────────────────────────────────
  OVERFITTING CHECK
──────────────────────────────────────────────────────────────
  Train accuracy  : {train_acc:.4f}
  Test  accuracy  : {test_acc:.4f}
  Gap             : {gap:.4f}
  Overfitting     : {"YES ❌" if overfit else "NO ✅"}

──────────────────────────────────────────────────────────────
  CONFUSION MATRIX
──────────────────────────────────────────────────────────────

                   Predicted
                   BENIGN     ATTACK
  Actual BENIGN  {tn:>9,}  {fp:>9,}
  Actual ATTACK  {fn:>9,}  {tp:>9,}

  TP (attacks caught)   : {tp:,}
  TN (benign correct)   : {tn:,}
  FP (false alarms)     : {fp:,}
  FN (missed attacks)   : {fn:,}  ← most critical !

  Miss rate (FN/attacks): {miss_rate:.2f}%
  False alarm rate      : {false_alarm:.2f}%
  Total attacks in test : {total_attacks:,}
  Total benign in test  : {total_benign:,}

──────────────────────────────────────────────────────────────
  CLASSIFICATION REPORT
──────────────────────────────────────────────────────────────
{clf_rep}
──────────────────────────────────────────────────────────────
  TOP 10 FEATURE IMPORTANCE
──────────────────────────────────────────────────────────────
{"  " + chr(10).join([f"  {k:<45} {v:.6f}" for k, v in fi_data.items()]) if fi_data else "  N/A — Isolation Forest has no feature_importances_"}

══════════════════════════════════════════════════════════════
"""

    report_path = os.path.join(REPORTS_PATH, "stdout.txt")
    os.makedirs(REPORTS_PATH, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    emit({"status": "report_saved", "path": report_path})

    # ── 11. MLflow logging
    try:
        import mlflow, mlflow.sklearn, mlflow.xgboost
        mlflow.set_experiment(EXPERIMENT_NAME)
        with mlflow.start_run(run_name=model_type):
            mlflow.log_params(params_used)
            mlflow.log_metrics({
                "accuracy"    : float(acc),
                "precision"   : float(prec),
                "recall"      : float(rec),
                "f1_score"    : float(f1),
                "train_acc"   : float(train_acc),
                "gap"         : float(gap),
                "TP"          : int(tp),
                "TN"          : int(tn),
                "FP"          : int(fp),
                "FN"          : int(fn),
                "train_time"  : float(train_time),
            })
            if roc_auc:
                mlflow.log_metric("roc_auc", float(roc_auc))
            if model_type == "XGBoost":
                mlflow.xgboost.log_model(model, "model")
            else:
                mlflow.sklearn.log_model(model, "model")
            mlflow.log_artifact(report_path)
            mlflow.log_artifact(cm_path)
        emit({"status": "mlflow_logged"})
    except Exception as e:
        emit({"status": "mlflow_warning", "msg": str(e)})

    # ── 12. Save to DB (MongoDB or JSON)
    dataset_info = {
        "filename"     : os.path.basename(config.get("data_path", "unknown")),
        "total_rows"   : int(df_raw.shape[0]),
        "total_cols"   : int(df_raw.shape[1]),
        "benign_count" : int((y == 0).sum()),
        "attack_count" : int((y == 1).sum()),
        "train_rows"   : int(X_train.shape[0]),
        "test_rows"    : int(X_test.shape[0]),
    }

    save_experiment(
        model_name   = model_type,
        params       = params_used,
        metrics      = metrics,
        cm           = cm,
        feature_cols = feature_cols,
        dataset_info = dataset_info
    )

    db_type = "MongoDB" if is_connected() else "JSON"
    emit({"status": "db_saved", "db": db_type})

    # ── 13. Complete
    emit({
        "status"     : "complete",
        "model"      : model_type,
        "recall"     : metrics["recall"],
        "f1"         : metrics["f1"],
        "total_time" : round(time.time() - t_total, 2)
    })

    return metrics, cm


# ════════════════════════════════════════
#   CLI ENTRY POINT
# ════════════════════════════════════════
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "msg": "Usage: python train.py '<config_json>'"
        }))
        sys.exit(1)

    config = json.loads(sys.argv[1])
    train(config)