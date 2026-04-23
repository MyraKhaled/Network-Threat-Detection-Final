# ══════════════════════════════════════════════════════════════
#   config.py — ALL PARAMETERS CENTRALIZED
#   Network Threat Detection — CICIDS 2017
#   Based on Kaggle Section 3 + NVIDIA DLI Lab1
# ══════════════════════════════════════════════════════════════

# ────────────────────────────────────────
#   DATA
# ────────────────────────────────────────
TARGET_COLUMN  = "Label_binary"
EXCLUDE_LABELS = ["Label", "Label_binary", "Label_multiclass"]
FEATURE_TYPE   = "number"
SCALER_PATH    = "models/scaler.pkl"
FEATURES_PATH  = "models/features.pkl"

# ────────────────────────────────────────
#   SPLIT
# ────────────────────────────────────────
TEST_SIZE    = 0.2
RANDOM_STATE = 42
STRATIFY     = True

# ────────────────────────────────────────
#   DECISION TREE
# ────────────────────────────────────────
DT_MAX_DEPTH         = 15
DT_CLASS_WEIGHT      = "balanced"
DT_MIN_SAMPLES_SPLIT = 2
DT_MIN_SAMPLES_LEAF  = 1

# ────────────────────────────────────────
#   RANDOM FOREST
# ────────────────────────────────────────
RF_N_ESTIMATORS      = 90
RF_MAX_DEPTH         = 25
RF_CLASS_WEIGHT      = "balanced"
RF_MIN_SAMPLES_SPLIT = 2
RF_MIN_SAMPLES_LEAF  = 1
RF_N_JOBS            = -1

# ────────────────────────────────────────
#   XGBOOST — NVIDIA DLI Lab1 style
# ────────────────────────────────────────
XGB_N_ESTIMATORS  = 200
XGB_MAX_DEPTH     = 12
XGB_MAX_LEAVES    = 2 ** 10
XGB_ALPHA         = 1.0
XGB_GAMMA         = 0.2
XGB_LEARNING_RATE = 0.1
XGB_SUBSAMPLE     = 1.0
XGB_REG_LAMBDA    = 1.0
XGB_EVAL_METRIC   = "logloss"
XGB_OBJECTIVE     = "binary:logistic"
XGB_N_JOBS        = -1

# ────────────────────────────────────────
#   ISOLATION FOREST — unsupervised
# ────────────────────────────────────────
ISO_N_ESTIMATORS  = 200
ISO_CONTAMINATION = 0.17
ISO_N_JOBS        = -1

# ────────────────────────────────────────
#   PATHS
# ────────────────────────────────────────
OUTPUT_PATH  = "results/"
MODELS_PATH  = "models/"
REPORTS_PATH = "results/"
PLOTS_PATH   = "results/plots/"

# ────────────────────────────────────────
#   MLFLOW
# ────────────────────────────────────────
EXPERIMENT_NAME = "Network-Threat-Detection"
MLFLOW_TRACKING = "./mlruns"

# ────────────────────────────────────────
#   MONGODB
# ────────────────────────────────────────
MONGO_URI  = "mongodb://localhost:27017/"
MONGO_DB   = "network_threat_detection"
MONGO_COLL = "experiments"

# ────────────────────────────────────────
#   PLOTS
# ────────────────────────────────────────
PLOT_DPI = 150