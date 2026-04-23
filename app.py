# ══════════════════════════════════════════════════════════════
#   app.py — Network Threat Detection Dashboard
#   Models trained on CIC-IDS2017 dataset
# ══════════════════════════════════════════════════════════════

import streamlit as st
import subprocess
import json
import os
import sys
import plotly.graph_objects as go
from datetime import datetime

from normalize  import normalize_to_csv
from ui_styles  import load_css, DARK, LIGHT
from config     import *

# ════════════════════════════════════════
#   PAGE CONFIG  — must be first st call
# ════════════════════════════════════════
st.set_page_config(
    page_title="NTD — Network Threat Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",   # sidebar open by default, user can collapse
)

# ════════════════════════════════════════
#   SESSION STATE
# ════════════════════════════════════════
defaults = {
    "results"        : None,
    "cm_data"        : None,
    "fi_data"        : {},
    "roc_data"       : {},
    "logs"           : [],
    "history"        : [],
    "report_content" : "",
    "ran_once"       : False,
    "theme"          : "dark",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ════════════════════════════════════════
#   THEME  — load CSS before any widget
# ════════════════════════════════════════
T = DARK if st.session_state.theme == "dark" else LIGHT
st.markdown(load_css(st.session_state.theme), unsafe_allow_html=True)


# ════════════════════════════════════════
#   HELPERS
# ════════════════════════════════════════
def score_cls(v):
    return "g" if v >= 0.95 else "y" if v >= 0.85 else "r"

def score_color(v):
    return T.GREEN if v >= 0.95 else T.YELLOW if v >= 0.85 else T.RED

def hud_card(label, value, color_cls):
    c   = score_cls(value)
    lbl = {"g": "EXCELLENT", "y": "GOOD", "r": "LOW"}[c]
    return f"""
<div class="hud-card {color_cls}">
  <div class="hud-card-label">{label}</div>
  <div class="hud-card-value">{value:.4f}</div>
  <span class="hud-card-badge badge-{c}">{lbl}</span>
</div>"""


# ════════════════════════════════════════
#   SIDEBAR
# ════════════════════════════════════════
with st.sidebar:

    # Logo + theme toggle
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            f'<div style="font-family:Orbitron,sans-serif;font-size:0.78rem;'
            f'font-weight:700;letter-spacing:0.12em;color:{T.ACCENT};">'
            f'⬡ NTD SYSTEM</div>'
            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.5rem;'
            f'letter-spacing:0.18em;color:{T.DIMMED};margin-top:2px;">'
            f'v2.0 · CIC-IDS2017</div>',
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("⇄", key="theme_btn", help="Toggle dark/light"):
            st.session_state.theme = (
                "light" if st.session_state.theme == "dark" else "dark"
            )
            st.rerun()

    st.markdown("---")

    st.markdown("### 📂 Dataset")
    uploaded = st.file_uploader(
        "file", type=["csv", "json", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("### 🤖 Model")
    model_type = st.selectbox(
        "model",
        ["Decision Tree", "Random Forest", "XGBoost", "Isolation Forest"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("### ⚙️ Settings")
    test_size    = st.slider("Test size",    0.1,  0.4,  TEST_SIZE,    step=0.05)
    random_state = st.number_input("Random state", 0, 9999, RANDOM_STATE)

    st.markdown("---")

    st.markdown("### 🔧 Hyperparams")

    params = {}

    if model_type == "Decision Tree":
        params = {
            "dt_max_depth"        : st.slider("Max depth",    1,   40,  DT_MAX_DEPTH,
                help="Max questions the tree asks"),
            "dt_class_weight"     : st.selectbox("Class weight", ["balanced", "None"],
                help="balanced = compensates for BENIGN/ATTACK imbalance"),
            "dt_min_samples_split": st.slider("Min split",    2,   50,  DT_MIN_SAMPLES_SPLIT),
            "dt_min_samples_leaf" : st.slider("Min leaf",     1,   50,  DT_MIN_SAMPLES_LEAF),
        }
    elif model_type == "Random Forest":
        params = {
            "rf_n_estimators"     : st.slider("Trees",        10, 300,  RF_N_ESTIMATORS),
            "rf_max_depth"        : st.slider("Max depth",     3,  50,  RF_MAX_DEPTH),
            "rf_class_weight"     : st.selectbox("Class weight", ["balanced", "None"]),
            "rf_min_samples_split": st.slider("Min split",     2,  50,  RF_MIN_SAMPLES_SPLIT),
            "rf_min_samples_leaf" : st.slider("Min leaf",      1,  50,  RF_MIN_SAMPLES_LEAF),
        }
    elif model_type == "XGBoost":
        params = {
            "xgb_n_estimators" : st.slider("Trees",        10,  500, XGB_N_ESTIMATORS),
            "xgb_max_depth"    : st.slider("Max depth",     3,   20,  XGB_MAX_DEPTH),
            "xgb_learning_rate": st.slider("Learning rate", 0.01, 0.5, XGB_LEARNING_RATE, step=0.01),
            "xgb_alpha"        : st.slider("Alpha (L1)",    0.0,  3.0, XGB_ALPHA,  step=0.1),
            "xgb_gamma"        : st.slider("Gamma",         0.0,  2.0, XGB_GAMMA,  step=0.05),
            "xgb_subsample"    : st.slider("Subsample",     0.5,  1.0, XGB_SUBSAMPLE, step=0.05),
            "xgb_reg_lambda"   : st.slider("Lambda (L2)",   0.0,  3.0, XGB_REG_LAMBDA, step=0.1),
        }
    elif model_type == "Isolation Forest":
        params = {
            "iso_n_estimators" : st.slider("Trees",         10, 400, ISO_N_ESTIMATORS),
            "iso_contamination": st.slider("Contamination", 0.01, 0.4, ISO_CONTAMINATION, step=0.01,
                help="~0.17 for CIC-IDS2017"),
        }
        st.info("ℹ️ Unsupervised — trains on BENIGN data only")

    st.markdown("---")
    run_btn = st.button("▶ EXECUTE PIPELINE", use_container_width=True)


# ════════════════════════════════════════
#   PAGE HEADER
# ════════════════════════════════════════
st.markdown(
    f"""
    <div style="margin-bottom:1.5rem;padding-bottom:1.2rem;
                border-bottom:1px solid {T.BORDER};">
      <div style="font-family:Orbitron,sans-serif;font-size:1.55rem;
                  font-weight:900;letter-spacing:0.04em;color:{T.TEXT};line-height:1.1;">
        NETWORK&thinsp;<span style="color:{T.ACCENT};">THREAT</span>&thinsp;DETECTION
      </div>
      <div style="display:flex;align-items:center;gap:18px;margin-top:6px;flex-wrap:wrap;">
        <span style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                     letter-spacing:0.16em;color:{T.DIMMED};">
          ML-POWERED INTRUSION ANALYSIS SYSTEM
        </span>
        <span style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                     color:{T.GREEN};letter-spacing:0.1em;">
          ● ONLINE
        </span>
        <span style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                     color:{T.DIMMED};letter-spacing:0.1em;">
          DATASET: CIC-IDS2017
        </span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Dataset info card
info_blocks = [
    ("SOURCE",    "Canadian Institute for Cybersecurity — University of New Brunswick"),
    ("YEAR",      "2017"),
    ("SAMPLES",   "~2.8 million network flow records"),
    ("FEATURES",  "78 traffic features extracted via CICFlowMeter"),
    ("CLASSES",   "BENIGN + 14 attack types"),
    ("SPLIT",     f"Training: {round((1-TEST_SIZE)*100)}%  ·  Testing: {round(TEST_SIZE*100)}%"),
    ("MODELS",    "Decision Tree · Random Forest · XGBoost · Isolation Forest"),
]

rows_html = "".join(
    f'<div style="display:flex;gap:0;padding:0.45rem 0;border-bottom:1px solid {T.BORDER};">'
    f'<div style="font-family:Share Tech Mono,monospace;font-size:0.62rem;'
    f'letter-spacing:0.14em;color:{T.ACCENT};min-width:110px;padding-top:3px;'
    f'text-transform:uppercase;">{key}</div>'
    f'<div style="font-family:Rajdhani,sans-serif;font-size:0.95rem;'
    f'color:{T.TEXT};line-height:1.55;font-weight:500;">{val}</div>'
    f'</div>'
    for key, val in info_blocks
)

st.markdown(
    f"""
    <div style="background:{T.CARD};border:1px solid {T.BORDER};
                border-radius:6px;padding:1.1rem 1.4rem;margin-bottom:1.6rem;">
      <div style="font-family:Orbitron,sans-serif;font-size:0.85rem;font-weight:700;
                  color:{T.TEXT};letter-spacing:0.06em;margin-bottom:0.8rem;">
        CIC-IDS2017 DATASET
      </div>
      {rows_html}
      <div style="margin-top:0.9rem;background:{T.BG};border:1px solid {T.BORDER};
                  border-left:3px solid {T.YELLOW};border-radius:4px;padding:0.85rem 1rem;">
        <div style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                    letter-spacing:0.14em;text-transform:uppercase;
                    color:{T.YELLOW};margin-bottom:5px;">⚠ IMBALANCE NOTE</div>
        <div style="font-family:Rajdhani,sans-serif;font-size:0.95rem;
                    color:{T.TEXT};line-height:1.55;font-weight:500;">
          Benign traffic ~83% of records. Use
          <code style="font-family:Share Tech Mono,monospace;color:{T.ACCENT};
          font-size:0.8rem;">class_weight=balanced</code>
          for supervised models. Evaluate with <strong>Recall</strong>
          and <strong>F1-score</strong>, not raw accuracy.
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ════════════════════════════════════════
#   TABS
# ════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["[ RESULTS ]", "[ HISTORY ]", "[ REPORT ]"])


# ══════════════════════════════════════════════════════════════
# TAB 1 — RESULTS
# ══════════════════════════════════════════════════════════════
with tab1:

    if run_btn:

        if uploaded is None:
            st.error("⚠  NO DATASET — upload a file first (CSV / JSON / XLSX)")
            st.stop()

        os.makedirs("data",          exist_ok=True)
        os.makedirs("results/plots", exist_ok=True)
        os.makedirs("models",        exist_ok=True)

        try:
            csv_path = normalize_to_csv(uploaded, "data/uploaded.csv")
        except ValueError as e:
            st.error(str(e))
            st.stop()

        config = {
            "model_type"  : model_type,
            "data_path"   : csv_path,
            "test_size"   : float(test_size),
            "random_state": int(random_state),
            **params,
        }

        # Spinner
        spinner_ph = st.empty()
        spinner_ph.markdown(f"""
        <div class="ntd-spinner-wrap">
          <div class="ntd-rings">
            <div class="ntd-ring-outer"></div>
            <div class="ntd-ring-mid"></div>
            <div class="ntd-ring-inner"></div>
          </div>
          <div class="ntd-spin-txt">TRAINING {model_type.upper()}…</div>
          <div class="ntd-dots">
            <div class="ntd-dot d1"></div>
            <div class="ntd-dot d2"></div>
            <div class="ntd-dot d3"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        progress  = st.progress(0)
        status_ph = st.empty()
        log_ph    = st.empty()
        logs      = []
        pval      = 0

        proc = subprocess.Popen(
            [sys.executable, "train.py", json.dumps(config)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        results  = None
        cm_data  = None
        fi_data  = {}
        roc_data = {}

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg    = json.loads(line)
                status = msg.get("status", "")

                if status == "started":
                    pval = 8;  status_ph.info(f"🚀 Starting {msg['model']}…")
                    logs.append(f"[{msg.get('time','?')}] Pipeline started")
                elif status == "loading":
                    pval = 12; logs.append("Loading CSV…")
                elif status == "loaded":
                    pval = 18; logs.append(f"Loaded {msg['rows']:,} rows × {msg['cols']} cols")
                elif status == "etl_running":
                    pval = 28; status_ph.info("🔄 ETL preprocessing…"); logs.append("ETL running…")
                elif status == "etl_done":
                    pval = 42
                    logs.append(
                        f"ETL done — {msg['rows']:,} rows × {msg['features']} features | "
                        f"BENIGN:{msg['benign']:,}  ATTACK:{msg['attack']:,}"
                    )
                elif status == "split_done":
                    pval = 52
                    status_ph.info(
                        f"✅ Split — Train:{msg['train_rows']:,} | Test:{msg['test_rows']:,}"
                    )
                    logs.append("Split done ✅")
                elif status == "training_started":
                    pval = 56; status_ph.info(f"⚡ Training {msg['model']}…")
                    logs.append(f"Training {msg['model']}…")
                elif status == "training_done":
                    pval = 78; status_ph.info(f"✅ Training done in {msg['train_time']}s")
                    logs.append(f"Training done — {msg['train_time']}s ✅")
                elif status == "results":
                    pval     = 85
                    results  = msg["metrics"]
                    cm_data  = msg["confusion_matrix"]
                    roc_data = msg.get("roc_curve", {})
                    logs.append(f"Results — Recall={results['recall']:.4f}  F1={results['f1']:.4f}")
                elif status == "feature_importance":
                    fi_data = msg.get("top10", {})
                elif status == "model_saved":
                    pval = 90; logs.append(f"Model saved → {msg['path']}")
                elif status == "report_saved":
                    logs.append(f"Report saved → {msg['path']}")
                    try:
                        with open("results/stdout.txt", "r", encoding="utf-8") as f:
                            st.session_state.report_content = f.read()
                    except Exception:
                        pass
                elif status == "complete":
                    pval = 100
                    status_ph.success(
                        f"✅ COMPLETE — Recall={msg['recall']:.4f} | "
                        f"F1={msg['f1']:.4f} | Time={msg['total_time']}s"
                    )
                    logs.append("Pipeline complete ✅")
                elif status == "error":
                    status_ph.error(f"❌ {msg['msg']}")
                    logs.append(f"ERROR: {msg['msg']}")

            except Exception:
                logs.append(line)

            progress.progress(pval)
            log_ph.code("\n".join(logs[-8:]), language=None)

        proc.wait()
        spinner_ph.empty()

        st.session_state.results  = results
        st.session_state.cm_data  = cm_data
        st.session_state.fi_data  = fi_data
        st.session_state.roc_data = roc_data
        st.session_state.logs     = logs
        st.session_state.ran_once = True

        if results:
            st.session_state.history.append({
                "model"  : model_type,
                "date"   : datetime.now().strftime("%d %b %Y"),
                "time"   : datetime.now().strftime("%H:%M:%S"),
                "metrics": results,
                "cm"     : cm_data,
            })

    # ── Display results
    results  = st.session_state.results
    cm_data  = st.session_state.cm_data
    fi_data  = st.session_state.fi_data  or {}
    roc_data = st.session_state.roc_data or {}

    if results:

        c1, c2, c3, c4 = st.columns(4)
        for col, (label, key, cls_) in zip(
            [c1, c2, c3, c4],
            [("ACCURACY",  "accuracy",  "c-red"),
             ("PRECISION", "precision", "c-green"),
             ("RECALL ⭐", "recall",    "c-yellow"),
             ("F1 SCORE",  "f1",        "c-accent")],
        ):
            with col:
                st.markdown(hud_card(label, results.get(key, 0), cls_),
                            unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # AUC / Time / Overfitting
        ca, cb, cc = st.columns(3)
        with ca:
            if results.get("roc_auc"):
                v  = results["roc_auc"]
                c_ = score_cls(v)
                st.markdown(f"""
                <div class='hud-card c-accent' style='text-align:center;'>
                    <div class='hud-card-label'>ROC AUC</div>
                    <div class='hud-card-value'>{v:.4f}</div>
                    <span class='hud-card-badge badge-{c_}'>{'PERFECT' if v>=0.9999 else 'GOOD' if v>=0.99 else 'LOW'}</span>
                </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown(f"""
            <div class='hud-card c-yellow' style='text-align:center;'>
                <div class='hud-card-label'>Training Time</div>
                <div class='hud-card-value' style='font-size:1.5rem;'>{results.get('time','-')}s</div>
            </div>""", unsafe_allow_html=True)
        with cc:
            ov  = results.get("overfitting", False)
            oc  = "c-red" if ov else "c-green"
            ot  = "YES ❌" if ov else "NO ✅"
            bg_ = "badge-r" if ov else "badge-g"
            st.markdown(f"""
            <div class='hud-card {oc}' style='text-align:center;'>
                <div class='hud-card-label'>Overfitting (gap={results.get('gap',0):.4f})</div>
                <div class='hud-card-value' style='font-size:1.5rem;'>{ot}</div>
                <span class='hud-card-badge {bg_}'>Train={results.get('train_acc',0):.4f} / Test={results.get('test_acc',0):.4f}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")

        cl, cr = st.columns(2)

        with cl:
            st.markdown("<div class='sec-label'>CONFUSION MATRIX</div>", unsafe_allow_html=True)
            if cm_data:
                fig_cm = go.Figure(data=go.Heatmap(
                    z=[[cm_data["TN"], cm_data["FP"]],
                       [cm_data["FN"], cm_data["TP"]]],
                    x=["Predicted BENIGN", "Predicted ATTACK"],
                    y=["Actual BENIGN",    "Actual ATTACK"],
                    text=[[f"TN\n{cm_data['TN']:,}", f"FP\n{cm_data['FP']:,}"],
                          [f"FN\n{cm_data['FN']:,}", f"TP\n{cm_data['TP']:,}"]],
                    texttemplate="%{text}",
                    textfont={"size": 13, "family": "Orbitron"},
                    colorscale=[[0, "#0a0e1a"], [0.5, "#4a0010"], [1, "#e63946"]],
                    showscale=False,
                ))
                fig_cm.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=T.TEXT, family="Share Tech Mono"),
                    margin=dict(l=10, r=10, t=10, b=10), height=270,
                )
                st.plotly_chart(fig_cm, use_container_width=True)

        with cr:
            st.markdown("<div class='sec-label'>DETAIL</div>", unsafe_allow_html=True)
            if cm_data:
                total_att = cm_data["TP"] + cm_data["FN"]
                miss_rate = round(cm_data["FN"] / total_att * 100, 2) if total_att > 0 else 0
                st.markdown(f"""
                <div class='cm-grid'>
                    <div class='cm-cell tp'>
                        <div class='cm-num' style='color:{T.GREEN};'>{cm_data["TP"]:,}</div>
                        <div class='cm-label'>True Positive ✅</div>
                    </div>
                    <div class='cm-cell tn'>
                        <div class='cm-num' style='color:{T.ACCENT};'>{cm_data["TN"]:,}</div>
                        <div class='cm-label'>True Negative ✅</div>
                    </div>
                    <div class='cm-cell fp'>
                        <div class='cm-num' style='color:{T.YELLOW};'>{cm_data["FP"]:,}</div>
                        <div class='cm-label'>False Positive ⚠️</div>
                    </div>
                    <div class='cm-cell fn'>
                        <div class='cm-num' style='color:{T.RED};'>{cm_data["FN"]:,}</div>
                        <div class='cm-label'>False Negative 🔴</div>
                    </div>
                </div>
                <div style="margin-top:12px;background:{T.CARD};border:1px solid {T.BORDER};
                            border-left:3px solid {T.RED};border-radius:4px;padding:1rem;">
                    <div style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                                color:{T.DIMMED};letter-spacing:0.14em;text-transform:uppercase;
                                margin-bottom:4px;">Miss Rate (FN / all attacks)</div>
                    <div style="font-family:Orbitron,sans-serif;font-size:1.6rem;
                                font-weight:700;color:{T.RED};">{miss_rate:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        # ROC Curve
        if roc_data.get("fpr") and results.get("roc_auc"):
            st.markdown("---")
            st.markdown("<div class='sec-label'>ROC CURVE</div>", unsafe_allow_html=True)
            fig_roc = go.Figure()
            fig_roc.add_trace(go.Scatter(
                x=roc_data["fpr"], y=roc_data["tpr"], mode="lines",
                name=f"AUC = {results['roc_auc']:.4f}",
                line=dict(color=T.ACCENT, width=2.5),
                fill="tozeroy", fillcolor=T.ACCENT + "15",
            ))
            fig_roc.add_trace(go.Scatter(
                x=[0, 1], y=[0, 1], mode="lines", name="Random (0.50)",
                line=dict(color=T.DIMMED, dash="dash", width=1),
            ))
            fig_roc.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=T.TEXT, family="Share Tech Mono"),
                xaxis=dict(title="False Positive Rate", gridcolor=T.BORDER, tickfont=dict(size=9)),
                yaxis=dict(title="True Positive Rate",  gridcolor=T.BORDER, tickfont=dict(size=9)),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
                margin=dict(l=20, r=20, t=20, b=20), height=300,
            )
            st.plotly_chart(fig_roc, use_container_width=True)

        # Feature importance
        if fi_data:
            st.markdown("---")
            st.markdown("<div class='sec-label'>TOP 10 FEATURE IMPORTANCE</div>",
                        unsafe_allow_html=True)
            import pandas as pd
            fi_df = pd.DataFrame(
                list(fi_data.items()), columns=["Feature", "Score"]
            ).sort_values("Score")
            fig_fi = go.Figure(go.Bar(
                x=fi_df["Score"], y=fi_df["Feature"], orientation="h",
                marker=dict(
                    color=fi_df["Score"],
                    colorscale=[[0, T.BORDER], [1, T.ACCENT]],
                    showscale=False,
                ),
            ))
            fig_fi.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=T.TEXT, family="Share Tech Mono", size=10),
                xaxis=dict(gridcolor=T.BORDER), yaxis=dict(gridcolor=T.BORDER),
                margin=dict(l=10, r=10, t=10, b=10), height=360,
            )
            st.plotly_chart(fig_fi, use_container_width=True)

        if st.session_state.logs:
            with st.expander("TRAINING LOG"):
                st.code("\n".join(st.session_state.logs), language="text")

    elif not st.session_state.ran_once:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">📡</div>
          <div class="ntd-empty-text">Awaiting pipeline execution</div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 2 — HISTORY
# ══════════════════════════════════════════════════════════════
with tab2:

    history = st.session_state.history

    # Try DB
    try:
        from db import get_all_experiments, get_best_experiment, is_connected
        db_experiments = get_all_experiments()
        db_label = "MongoDB" if is_connected() else "JSON"
    except Exception:
        db_experiments = []
        db_label = "N/A"

    if not history and not db_experiments:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">🕒</div>
          <div class="ntd-empty-text">No training runs recorded yet</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        if history:
            st.markdown(
                f'<div class="ntd-label" style="margin-bottom:1rem;">'
                f'{len(history)} RUN(S) THIS SESSION</div>',
                unsafe_allow_html=True,
            )
            for run in reversed(history):
                m   = run["metrics"]
                f1v = m.get("f1", 0)
                c   = score_cls(f1v)
                lbl = {"g": "EXCELLENT", "y": "GOOD", "r": "LOW"}[c]
                cm_ = run.get("cm", {})

                scores_html = "".join(
                    f'<div style="text-align:center">'
                    f'<div class="hist-key">{k}</div>'
                    f'<div class="hist-score" style="color:{score_color(v)};">{v:.4f}</div>'
                    f'</div>'
                    for k, v in [
                        ("ACC",  m.get("accuracy",  0)),
                        ("PREC", m.get("precision", 0)),
                        ("REC",  m.get("recall",    0)),
                        ("F1",   f1v),
                    ]
                )
                cm_html = ""
                if cm_:
                    cm_html = (
                        f'<div style="font-family:Share Tech Mono,monospace;'
                        f'font-size:0.58rem;color:{T.DIMMED};margin-top:3px;">'
                        f'TP:{cm_["TP"]:,} TN:{cm_["TN"]:,} '
                        f'FP:{cm_["FP"]:,} '
                        f'<span style="color:{T.RED};">FN:{cm_["FN"]:,}</span></div>'
                    )

                st.markdown(f"""
                <div class="hist-row">
                  <div style="min-width:160px">
                    <div class="hist-model">{run['model']}</div>
                    <div class="hist-ts">{run['date']} · {run['time']}</div>
                    {cm_html}
                  </div>
                  <div style="display:flex;gap:24px;flex:1;justify-content:center">
                    {scores_html}
                  </div>
                  <span class="hud-card-badge badge-{c}">{lbl}</span>
                </div>
                """, unsafe_allow_html=True)

        if db_experiments:
            st.markdown("---")
            st.markdown(
                f'<div class="ntd-label" style="margin-bottom:1rem;">'
                f'DATABASE HISTORY ({db_label})</div>',
                unsafe_allow_html=True,
            )
            import pandas as pd
            rows = []
            for e in db_experiments:
                m = e.get("metrics", {})
                c = e.get("confusion_matrix", {})
                rows.append({
                    "Model"  : e.get("model_name", "?"),
                    "v"      : f"v{e.get('version','?')}",
                    "Date"   : e.get("date", "")[:16],
                    "Recall" : f"{m.get('recall',0)*100:.2f}%",
                    "F1"     : f"{m.get('f1_score',0)*100:.2f}%",
                    "AUC"    : f"{m.get('roc_auc',0):.4f}" if m.get("roc_auc") else "N/A",
                    "FN"     : c.get("FN", "-"),
                    "Miss%"  : f"{c.get('miss_rate_pct',0):.2f}%",
                    "Time(s)": m.get("training_time", "-"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬡  CLEAR SESSION HISTORY", key="clear_hist"):
            st.session_state.history = []
            st.rerun()


# ══════════════════════════════════════════════════════════════
# TAB 3 — REPORT
# ══════════════════════════════════════════════════════════════
with tab3:

    results = st.session_state.results

    if not results:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">📄</div>
          <div class="ntd-empty-text">Execute pipeline to generate report</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        m     = results
        now   = datetime.now().strftime("%d %b %Y · %H:%M:%S")
        model = (st.session_state.history[-1]["model"]
                 if st.session_state.history else "—")

        grid_html = "".join(
            f'<div style="text-align:center">'
            f'<div class="ntd-label" style="font-size:0.58rem">{k}</div>'
            f'<div style="font-family:Orbitron,sans-serif;font-size:1.3rem;'
            f'font-weight:700;color:{score_color(v)};margin-top:4px">{v:.4f}</div>'
            f'</div>'
            for k, v in [
                ("ACCURACY",  m.get("accuracy",  0)),
                ("PRECISION", m.get("precision", 0)),
                ("RECALL",    m.get("recall",    0)),
                ("F1",        m.get("f1",        0)),
            ]
        )

        st.markdown(f"""
        <div style="background:{T.CARD};border:1px solid {T.BORDER};
                    border-left:3px solid {T.ACCENT};border-radius:6px;
                    padding:1.3rem 1.5rem;margin-bottom:1.4rem;">
          <div class="ntd-label" style="margin-bottom:4px;">ANALYSIS REPORT — {now}</div>
          <div style="font-family:Orbitron,sans-serif;font-size:0.95rem;
                      font-weight:700;color:{T.TEXT};margin-bottom:1rem;">
            MODEL: {model.upper()}
          </div>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">
            {grid_html}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Radar
        cats = ["Accuracy", "Precision", "Recall", "F1"]
        vals = [m.get(k, 0) for k in ["accuracy", "precision", "recall", "f1"]]
        fig_radar = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself",
            line=dict(color=T.ACCENT, width=2),
            fillcolor=T.ACCENT + "1a",
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor=T.CARD,
                radialaxis=dict(visible=True, range=[0, 1], gridcolor=T.BORDER,
                                tickfont=dict(color=T.DIMMED, size=8, family="Share Tech Mono")),
                angularaxis=dict(gridcolor=T.BORDER,
                                 tickfont=dict(color=T.TEXT, size=10, family="Orbitron")),
            ),
            paper_bgcolor=T.CARD, plot_bgcolor=T.CARD,
            font=dict(color=T.TEXT, family="Share Tech Mono"),
            margin=dict(l=60, r=60, t=40, b=40),
            showlegend=False, height=340,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("---")
        st.markdown("<div class='sec-label'>FULL REPORT</div>", unsafe_allow_html=True)

        cr1, cr2 = st.columns(2)
        with cr1:
            if st.button("📄 Load Report", use_container_width=True):
                try:
                    with open("results/stdout.txt", "r", encoding="utf-8") as f:
                        st.session_state.report_content = f.read()
                except Exception:
                    st.warning("No report file found — run the pipeline first!")
        with cr2:
            content = st.session_state.get("report_content", "")
            if content:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    "⬇️  Download (.txt)", content,
                    file_name=f"ntd_{model.replace(' ','_')}_{ts}.txt",
                    use_container_width=True,
                )
            else:
                st.button("⬇️  Download", disabled=True, use_container_width=True)

        if st.session_state.get("report_content"):
            st.code(st.session_state["report_content"], language=None)

        st.markdown("---")
        st.markdown("<div class='sec-label'>MLFLOW TRACKING</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:{T.CARD};border:1px solid {T.BORDER};
                    border-radius:6px;padding:1rem 1.2rem;">
            <div style="font-family:Share Tech Mono,monospace;font-size:0.68rem;
                        color:{T.DIMMED};margin-bottom:10px;">
                Launch MLflow UI to compare all experiment runs:
            </div>
            <code style="font-family:Share Tech Mono,monospace;font-size:0.78rem;
                         color:{T.GREEN};">mlflow ui --port 5000</code>
            <br>
            <code style="font-family:Share Tech Mono,monospace;font-size:0.78rem;
                         color:{T.DIMMED};display:block;margin-top:6px;">
                → http://localhost:5000
            </code>
        </div>
        """, unsafe_allow_html=True)