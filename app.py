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

from normalize import normalize_to_csv
from ui_styles import load_css, DARK, LIGHT

from config import *

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="NTD — Network Threat Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",  # Garde ça
)

# ── SESSION STATE ─────────────────────────────────────────────
for k, v in {"results": None, "logs": [], "history": [], "theme": "dark"}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── THEME ─────────────────────────────────────────────────────
theme = st.session_state.theme
T     = DARK if theme == "dark" else LIGHT
#st.markdown(load_css(theme), unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────
def score_cls(v):
    return "g" if v >= 0.95 else "y" if v >= 0.85 else "r"

def hud_card(label, value, color_cls):
    c   = score_cls(value)
    lbl = {"g": "EXCELLENT", "y": "GOOD", "r": "LOW"}[c]
    return f"""
<div class="hud-card {color_cls}">
  <div class="hud-card-label">{label}</div>
  <div class="hud-card-value">{value:.4f}</div>
  <span class="hud-card-badge badge-{c}">{lbl}</span>
</div>"""

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:

    # Logo row + theme toggle
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
            "dt_max_depth":         st.slider("Max depth",   1,   40, DT_MAX_DEPTH),
            "dt_class_weight":      st.selectbox("Class weight", ["balanced", "None"]),
            "dt_min_samples_split": st.slider("Min split",   2,   50, DT_MIN_SAMPLES_SPLIT),
            "dt_min_samples_leaf":  st.slider("Min leaf",    1,   50, DT_MIN_SAMPLES_LEAF),
        }
    elif model_type == "Random Forest":
        params = {
            "rf_n_estimators":      st.slider("Trees",       10, 300, RF_N_ESTIMATORS),
            "rf_max_depth":         st.slider("Max depth",    3,  50, RF_MAX_DEPTH),
            "rf_class_weight":      st.selectbox("Class weight", ["balanced", "None"]),
            "rf_min_samples_split": st.slider("Min split",    2,  50, RF_MIN_SAMPLES_SPLIT),
            "rf_min_samples_leaf":  st.slider("Min leaf",     1,  50, RF_MIN_SAMPLES_LEAF),
        }
    elif model_type == "XGBoost":
        params = {
            "xgb_n_estimators":  st.slider("Trees",       10,  500, XGB_N_ESTIMATORS),
            "xgb_max_depth":     st.slider("Max depth",    3,   20, XGB_MAX_DEPTH),
            "xgb_learning_rate": st.slider("LR",          0.01, 0.5, XGB_LEARNING_RATE),
            "xgb_alpha":         st.slider("Alpha",        0.0,  3.0, XGB_ALPHA),
            "xgb_gamma":         st.slider("Gamma",        0.0,  2.0, XGB_GAMMA),
            "xgb_subsample":     st.slider("Subsample",    0.5,  1.0, XGB_SUBSAMPLE),
            "xgb_reg_lambda":    st.slider("Lambda",       0.0,  3.0, XGB_REG_LAMBDA),
        }
    elif model_type == "Isolation Forest":
        params = {
            "iso_n_estimators":  st.slider("Trees",         10, 400, ISO_N_ESTIMATORS),
            "iso_contamination": st.slider("Contamination", 0.01, 0.4, ISO_CONTAMINATION),
        }

    st.markdown("---")
    run_btn = st.button("▶ EXECUTE PIPELINE", use_container_width=True)

# ── PAGE HEADER ───────────────────────────────────────────────
st.markdown(
    f"""
    <div style="margin-bottom:1.5rem;padding-bottom:1.2rem;
                border-bottom:1px solid {T.BORDER};">
      <div style="font-family:Orbitron,sans-serif;font-size:1.55rem;
                  font-weight:900;letter-spacing:0.04em;color:{T.TEXT};
                  line-height:1.1;">
        NETWORK&thinsp;<span style="color:{T.ACCENT};">THREAT</span>&thinsp;DETECTION
      </div>
      <div style="display:flex;align-items:center;gap:18px;margin-top:6px;">
        <span style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                     letter-spacing:0.16em;color:{T.DIMMED};">
          ML-POWERED INTRUSION ANALYSIS SYSTEM
        </span>
        <span style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                     color:{T.GREEN};letter-spacing:0.1em;
                     text-shadow:0 0 8px {T.GREEN}88;">
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

# ── DATASET INFO (inline under header) ───────────────────────
info_blocks = [
    ("SOURCE",       "Canadian Institute for Cybersecurity (CIC), University of New Brunswick"),
    ("YEAR",         "2017"),
    ("SAMPLES",      "~2.8 million network flow records"),
    ("FEATURES",     "78 network traffic features extracted via CICFlowMeter"),
    ("CLASSES",      "Benign + 14 attack types"),
    ("ATTACK TYPES", "DDoS · DoS Hulk · DoS GoldenEye · DoS Slowloris · DoS SlowHTTPTest · "
                     "FTP-Patator · SSH-Patator · Web Attack (Brute Force / XSS / SQL) · "
                     "Infiltration · Bot · PortScan · Heartbleed"),
    ("SPLIT",        f"Training: {round((1 - TEST_SIZE)*100)}%  ·  Testing: {round(TEST_SIZE*100)}%"),
    ("MODELS",       "Decision Tree · Random Forest · XGBoost · Isolation Forest"),
    ("PURPOSE",      "Binary and multi-class intrusion detection benchmarking"),
    ("REFERENCE",    "Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2018). "
                     "Toward Generating a New Intrusion Detection Dataset and Intrusion "
                     "Traffic Characterization. ICISSP."),
]

rows_html = "".join(
    f"""
    <div style="display:flex;gap:0;padding:0.5rem 0;
                border-bottom:1px solid {T.BORDER};">
      <div style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;
                  letter-spacing:0.14em;color:{T.ACCENT};
                  min-width:130px;padding-top:3px;text-transform:uppercase;">
        {key}
      </div>
      <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;
                  color:{T.TEXT};line-height:1.55;font-weight:500;">
        {val}
      </div>
    </div>
    """
    for key, val in info_blocks
)

st.markdown(
    f"""
    <div style="background:{T.CARD};border:1px solid {T.BORDER};
                border-radius:6px;padding:1.2rem 1.5rem;margin-bottom:1.8rem;">
      <div style="font-family:Orbitron,sans-serif;font-size:1rem;
                  font-weight:700;color:{T.TEXT};letter-spacing:0.06em;
                  margin-bottom:1rem;">
        CIC-IDS2017 DATASET
      </div>
      {rows_html}
      <div style="margin-top:1rem;background:{T.BG};border:1px solid {T.BORDER};
                  border-left:3px solid {T.YELLOW};border-radius:4px;
                  padding:0.9rem 1.1rem;">
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;
                    letter-spacing:0.14em;text-transform:uppercase;
                    color:{T.YELLOW};margin-bottom:6px;">
          ⚠ IMBALANCE NOTE
        </div>
        <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;
                    color:{T.TEXT};line-height:1.6;font-weight:500;">
          CIC-IDS2017 is highly imbalanced — benign traffic dominates (~83% of records).
          Models using <code style="font-family:'Share Tech Mono',monospace;
          color:{T.ACCENT};font-size:0.82rem;">class_weight=balanced</code>
          or anomaly-based approaches (Isolation Forest) handle this more robustly.
          Evaluate with F1-score and Recall rather than raw accuracy.
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── TABS ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "[ RESULTS ]", "[ HISTORY ]", "[ REPORT ]"
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — RESULTS
# ══════════════════════════════════════════════════════════════
with tab1:

    if run_btn:

        if uploaded is None:
            st.error("⚠  NO DATASET LOADED — upload a file first")
            st.stop()

        os.makedirs("data", exist_ok=True)
        csv_path = normalize_to_csv(uploaded, "data/uploaded.csv")

        config = {
            "model_type":   model_type,
            "data_path":    csv_path,
            "test_size":    float(test_size),
            "random_state": int(random_state),
            **params,
        }

        # Spinner
        ph = st.empty()
        ph.markdown(f"""
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

        proc = subprocess.Popen(
            [sys.executable, "train.py", json.dumps(config)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        logs    = []
        results = None
        for line in proc.stdout:
            try:
                msg = json.loads(line)
                if msg.get("status") == "results":
                    results = msg["metrics"]
            except Exception:
                logs.append(line)
        proc.wait()
        ph.empty()

        st.session_state.results = results
        st.session_state.logs    = logs
        if results:
            st.session_state.history.append({
                "model":   model_type,
                "date":    datetime.now().strftime("%d %b %Y"),
                "time":    datetime.now().strftime("%H:%M:%S"),
                "metrics": results,
            })

    # ── Display ───────────────────────────────────────────────
    if st.session_state.results:
        m = st.session_state.results

        c1, c2, c3, c4 = st.columns(4)
        for col, (label, key, cls) in zip(
            [c1, c2, c3, c4],
            [("ACCURACY",  "accuracy",  "c-red"),
             ("PRECISION", "precision", "c-green"),
             ("RECALL",    "recall",    "c-yellow"),
             ("F1 SCORE",  "f1",        "c-accent")],
        ):
            with col:
                st.markdown(hud_card(label, m.get(key, 0), cls),
                            unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.logs:
            with st.expander("TRAINING LOG OUTPUT"):
                st.code("".join(st.session_state.logs), language="text")

    else:
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

    if not history:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">🕒</div>
          <div class="ntd-empty-text">No training runs recorded yet</div>
        </div>
        """, unsafe_allow_html=True)
    else:
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

            scores_html = "".join(
                f'<div style="text-align:center">'
                f'<div class="hist-key">{k}</div>'
                f'<div class="hist-score">{v:.4f}</div>'
                f'</div>'
                for k, v in [
                    ("ACC",  m.get("accuracy",  0)),
                    ("PREC", m.get("precision", 0)),
                    ("REC",  m.get("recall",    0)),
                    ("F1",   f1v),
                ]
            )

            st.markdown(f"""
            <div class="hist-row">
              <div style="min-width:150px">
                <div class="hist-model">{run['model']}</div>
                <div class="hist-ts">{run['date']} · {run['time']}</div>
              </div>
              <div style="display:flex;gap:24px;flex:1;justify-content:center">
                {scores_html}
              </div>
              <span class="hud-card-badge badge-{c}">{lbl}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬡  CLEAR HISTORY", key="clear_hist"):
            st.session_state.history = []
            st.rerun()

# ══════════════════════════════════════════════════════════════
# TAB 3 — REPORT
# ══════════════════════════════════════════════════════════════
with tab3:

    if not st.session_state.results:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">📄</div>
          <div class="ntd-empty-text">Execute pipeline to generate report</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        m     = st.session_state.results
        now   = datetime.now().strftime("%d %b %Y · %H:%M:%S")
        model = (st.session_state.history[-1]["model"]
                 if st.session_state.history else "—")

        # Summary header
        grid = "".join(
            f'<div style="text-align:center">'
            f'<div class="ntd-label" style="font-size:0.6rem">{k}</div>'
            f'<div style="font-family:Orbitron,sans-serif;font-size:1.35rem;'
            f'font-weight:700;color:{T.TEXT};margin-top:4px">{v:.4f}</div>'
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
          <div class="ntd-label" style="margin-bottom:4px">
            ANALYSIS REPORT — {now}
          </div>
          <div style="font-family:Orbitron,sans-serif;font-size:0.95rem;
                      font-weight:700;color:{T.TEXT};margin-bottom:1rem;">
            MODEL: {model.upper()}
          </div>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">
            {grid}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Radar
        cats = ["Accuracy", "Precision", "Recall", "F1"]
        vals = [m.get(k, 0) for k in ["accuracy", "precision", "recall", "f1"]]
        fig  = go.Figure(go.Scatterpolar(
            r         = vals + [vals[0]],
            theta     = cats + [cats[0]],
            fill      = "toself",
            line      = dict(color=T.ACCENT, width=2),
            fillcolor = T.ACCENT + "1a",
        ))
        fig.update_layout(
            polar = dict(
                bgcolor    = T.CARD,
                radialaxis = dict(visible=True, range=[0, 1],
                                  gridcolor=T.BORDER,
                                  tickfont=dict(color=T.DIMMED, size=8,
                                                family="Share Tech Mono")),
                angularaxis= dict(gridcolor=T.BORDER,
                                  tickfont=dict(color=T.TEXT, size=10,
                                                family="Orbitron")),
            ),
            paper_bgcolor = T.CARD,
            plot_bgcolor  = T.CARD,
            font          = dict(color=T.TEXT, family="Share Tech Mono"),
            margin        = dict(l=60, r=60, t=40, b=40),
            showlegend    = False,
            height        = 360,
        )
        st.plotly_chart(fig, use_container_width=True)