import os
import json
import time
from datetime import datetime
from sklearn.metrics import classification_report


def generate_report(
    model_type   : str,
    config       : dict,
    metrics      : dict,
    cm           : dict,        
    fi_data      : dict,        
    dataset_info : dict,        
    dataset_name : str,
    version      : int,
    y_test       = None,
    y_pred       = None,
) -> tuple[str, bytes]:
    """
    Génère le rapport complet.

    Retourne
    --------
    report_path : str    — chemin du fichier sauvegardé
    report_bytes: bytes  — contenu pour st.download_button
    """

    os.makedirs("results", exist_ok=True)

    tp = cm.get("TP", 0)
    tn = cm.get("TN", 0)
    fp = cm.get("FP", 0)
    fn = cm.get("FN", 0)

    total_attacks = tp + fn
    total_benign  = tn + fp
    miss_rate     = round(fn / total_attacks * 100, 2) if total_attacks > 0 else 0
    false_alarm   = round(fp / total_benign  * 100, 2) if total_benign  > 0 else 0

    acc  = metrics.get("accuracy",  0)
    prec = metrics.get("precision", 0)
    rec  = metrics.get("recall",    0)
    f1   = metrics.get("f1",        0)
    auc  = metrics.get("roc_auc")
    t    = metrics.get("time",      0)
    train_acc = metrics.get("train_acc", 0)
    test_acc  = metrics.get("test_acc",  0)
    gap       = metrics.get("gap",       0)
    overfit   = metrics.get("overfitting", False)

    now      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_id   = f"{dataset_name}__{model_type.replace(' ','_').lower()}__v{version}"

    # Classification report
    clf_rep = ""
    if y_test is not None and y_pred is not None:
        try:
            clf_rep = classification_report(
                y_test, y_pred,
                target_names=["BENIGN", "ATTACK"],
                digits=4
            )
        except Exception:
            clf_rep = "  N/A"

    # Feature importance
    if fi_data:
        fi_lines = "\n".join(
            f"  {k:<45} {v:.6f}" for k, v in fi_data.items()
        )
    else:
        fi_lines = "  N/A — Isolation Forest has no feature_importances_"

    # Params (sans data_path)
    params_clean = {k: v for k, v in config.items()
                    if k not in ("data_path", "model_type")}

    separator = "─" * 62

    report_text = f"""
╔══════════════════════════════════════════════════════════════╗
║  NTD — NETWORK THREAT DETECTION                              ║
║  TRAINING REPORT                                             ║
╚══════════════════════════════════════════════════════════════╝

  Run ID          : {run_id}
  Date            : {now}
  Model           : {model_type}
  Dataset         : {dataset_name}
  Version         : v{version}

{separator}
  PARAMETERS
{separator}
{json.dumps(params_clean, indent=4)}

{separator}
  DATASET SUMMARY
{separator}
  Total rows      : {dataset_info.get("total_rows", 0):,}
  Total columns   : {dataset_info.get("total_cols", 0)}
  Features (ML)   : {dataset_info.get("n_features", 0)}
  Train rows      : {dataset_info.get("train_rows", 0):,}
  Test rows       : {dataset_info.get("test_rows", 0):,}
  BENIGN          : {dataset_info.get("benign_count", 0):,}
  ATTACK          : {dataset_info.get("attack_count", 0):,}

{separator}
  PERFORMANCE METRICS
{separator}
  Accuracy        : {acc:.4f}   ({acc*100:.2f}%)
  Precision       : {prec:.4f}   ({prec*100:.2f}%)
  Recall          : {rec:.4f}   ({rec*100:.2f}%)   [*PRIORITAIRE*]
  F1 Score        : {f1:.4f}   ({f1*100:.2f}%)
  ROC AUC         : {auc if auc else "N/A (non-supervisé)"}
  Training time   : {t:.2f} secondes

{separator}
  OVERFITTING
{separator}
  Train accuracy  : {train_acc:.4f}
  Test accuracy   : {test_acc:.4f}
  Gap             : {gap:.4f}
  Overfitting     : {"OUI — ecart > 5%" if overfit else "NON — modele generalise bien"}

{separator}
  CONFUSION MATRIX
{separator}

                   Predicted
                   BENIGN        ATTACK
  Actual BENIGN  {tn:>11,}   {fp:>11,}
  Actual ATTACK  {fn:>11,}   {tp:>11,}

  TP — Attaques détectées     : {tp:,}
  TN — Bénin correct          : {tn:,}
  FP — Fausses alarmes        : {fp:,}
  FN — Attaques manquées      : {fn:,}   [!!! CRITIQUE !!!]

  Miss rate   (FN / attaques) : {miss_rate:.2f}%
  Fausse alarme (FP / bénin)  : {false_alarm:.2f}%
  Total attaques (test)       : {total_attacks:,}
  Total bénin (test)          : {total_benign:,}

{separator}
  CLASSIFICATION REPORT
{separator}
{clf_rep}
{separator}
  TOP 10 FEATURE IMPORTANCE
{separator}
{fi_lines}

{separator}
  RECOMMANDATIONS
{separator}
{"  [!] Miss rate > 50% : augmenter contamination ou changer de modele" if miss_rate > 50 else "  [OK] Miss rate acceptable"}
{"  [!] Recall < 0.85 : envisager Random Forest ou XGBoost supervise" if rec < 0.85 else "  [OK] Recall satisfaisant"}
{"  [!] Overfitting detecte : reduire max_depth ou augmenter regularisation" if overfit else "  [OK] Pas de surapprentissage"}

══════════════════════════════════════════════════════════════
  Genere par NTD v2.0 — CIC-IDS2017
  {now}
══════════════════════════════════════════════════════════════
"""

    # Sauvegarde locale
    safe_name   = model_type.lower().replace(" ", "_")
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"results/report_{dataset_name}_{safe_name}_v{version}_{ts}.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Aussi sauvegarder le stdout.txt classique pour compatibilité
    with open("results/stdout.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    return report_path, report_text.encode("utf-8")


def get_report_filename(dataset_name: str, model_type: str, version: int) -> str:
    """Retourne le nom de fichier standardisé pour le rapport."""
    safe_ds    = dataset_name.lower().replace(" ", "_")
    safe_model = model_type.lower().replace(" ", "_")
    ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"ntd_{safe_ds}_{safe_model}_v{version}_{ts}.txt"