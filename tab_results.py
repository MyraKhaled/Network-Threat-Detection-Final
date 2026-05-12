# ══════════════════════════════════════════════════════════════
#   tab_results.py — Tab 1 : Pipeline execution + results display
# ══════════════════════════════════════════════════════════════

import os
import sys
import json
import subprocess
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from normalize import normalize_to_csv
from app_helpers import hex_to_rgba, score_cls, score_color, hud_card, bar_row


def run_pipeline(T, sidebar: dict):
    """Launches the train.py subprocess and updates the session state."""
    uploaded     = sidebar["uploaded"]
    model_type   = sidebar["model_type"]
    test_size    = sidebar["test_size"]
    random_state = sidebar["random_state"]
    params       = sidebar["params"]

    if uploaded is None:
        st.error("No file — upload a CSV / JSON / XLSX first")
        st.stop()

    os.makedirs("data",          exist_ok=True)
    os.makedirs("results/plots", exist_ok=True)
    os.makedirs("models",        exist_ok=True)

    try:
        csv_path = normalize_to_csv(uploaded, "data/uploaded.csv")
    except ValueError as e:
        st.error(str(e))
        st.stop()

    dataset_name = os.path.splitext(uploaded.name)[0]

    config = {
        "model_type"   : model_type,
        "data_path"    : csv_path,
        "dataset_name" : dataset_name,
        "test_size"    : float(test_size),
        "random_state" : int(random_state),
        **params,
    }

    # ── Animated spinner
    spinner_ph = st.empty()
    spinner_ph.markdown(f"""
    <div class="ntd-spinner-wrap">
      <div class="ntd-rings">
        <div class="ntd-ring-outer"></div>
        <div class="ntd-ring-mid"></div>
        <div class="ntd-ring-inner"></div>
      </div>
      <div class="ntd-spin-txt">TRAINING {model_type.upper()}...</div>
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
        text=True, bufsize=1,
    )

    results  = None
    cm_data  = None
    fi_data  = {}
    roc_data = {}
    report_path_recv     = ""
    report_filename_recv = ""

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            msg    = json.loads(line)
            status = msg.get("status", "")

            if status == "started":
                pval = 8
                status_ph.info(f"Starting {msg['model']}...")
                logs.append(f"[{msg.get('time','?')}] Pipeline started")
            elif status == "loading":
                pval = 12; logs.append("Loading CSV...")
            elif status == "loaded":
                pval = 18
                logs.append(f"Loaded: {msg['rows']:,} rows x {msg['cols']} columns")
            elif status == "etl_running":
                pval = 28
                status_ph.info("ETL running...")
                logs.append("ETL...")
            elif status == "etl_done":
                pval = 42
                logs.append(
                    f"ETL — {msg['rows']:,} rows x {msg['features']} features | "
                    f"BENIGN:{msg['benign']:,}  ATTACK:{msg['attack']:,}"
                )
            elif status == "split_done":
                pval = 52
                status_ph.info(f"Split — Train:{msg['train_rows']:,} / Test:{msg['test_rows']:,}")
                logs.append("Split done")
            elif status == "training_started":
                pval = 56
                status_ph.info(f"Training {msg['model']}...")
                logs.append(f"Training {msg['model']}...")
            elif status == "training_done":
                pval = 78
                status_ph.info(f"Training complete — {msg['train_time']}s")
                logs.append(f"Complete — {msg['train_time']}s")
            elif status == "results":
                pval     = 85
                results  = msg["metrics"]
                cm_data  = msg["confusion_matrix"]
                roc_data = msg.get("roc_curve", {})
                logs.append(f"Recall={results['recall']:.4f}  F1={results['f1']:.4f}")
            elif status == "feature_importance":
                fi_data = msg.get("top10", {})
            elif status == "model_saved":
                pval = 90
                logs.append(f"Model saved → {msg['path']}")
            elif status == "report_saved":
                report_path_recv = msg.get("path", "")
                logs.append(f"Report generated → {msg['path']}")
                try:
                    with open(report_path_recv, "r", encoding="utf-8") as f:
                        st.session_state.report_content = f.read()
                    with open(report_path_recv, "rb") as f:
                        st.session_state.report_bytes = f.read()
                except Exception:
                    pass
            elif status == "mlflow_logged":
                logs.append("MLflow logged")
            elif status == "db_saved":
                logs.append(f"DB ({msg.get('db','?')}) — {msg.get('run_id','')}")
            elif status == "db_warning":
                logs.append(f"DB warning: {msg.get('msg','')}")
            elif status == "complete":
                pval = 100
                v = msg.get("version", "?")
                status_ph.success(
                    f"COMPLETE — v{v} — Recall={msg['recall']:.4f} | "
                    f"F1={msg['f1']:.4f} | {msg['total_time']}s"
                )
                logs.append(f"Pipeline complete — run_id: {msg.get('run_id','')}")
                report_filename_recv = msg.get("report_filename", "report.txt")
                st.session_state.last_run_id     = msg.get("run_id", "")
                st.session_state.last_version    = msg.get("version", 1)
                st.session_state.last_model      = model_type
                st.session_state.last_dataset    = dataset_name
                st.session_state.report_filename = report_filename_recv
            elif status == "error":
                status_ph.error(f"ERROR — {msg.get('msg','')}")
                logs.append(f"ERROR: {msg.get('msg','')}")

        except Exception:
            logs.append(line)

        progress.progress(pval)
        log_ph.code("\n".join(logs[-8:]), language=None)

    proc.wait()
    spinner_ph.empty()

    # ── Persist in session state
    st.session_state.results  = results
    st.session_state.cm_data  = cm_data
    st.session_state.fi_data  = fi_data
    st.session_state.roc_data = roc_data
    st.session_state.logs     = logs
    st.session_state.ran_once = True

    if results:
        st.session_state.history.append({
            "model"   : model_type,
            "dataset" : dataset_name,
            "version" : st.session_state.last_version,
            "run_id"  : st.session_state.last_run_id,
            "date"    : datetime.now().strftime("%d %b %Y"),
            "time"    : datetime.now().strftime("%H:%M:%S"),
            "metrics" : results,
            "cm"      : cm_data,
        })


def render_results(T):
    """Displays results from the session state."""
    results  = st.session_state.results
    cm_data  = st.session_state.cm_data
    fi_data  = st.session_state.fi_data  or {}
    roc_data = st.session_state.roc_data or {}

    if not results:
        if not st.session_state.ran_once:
            st.markdown("""
            <div class="ntd-empty">
              <div class="ntd-empty-icon">[ - ]</div>
              <div class="ntd-empty-text">Waiting for execution</div>
            </div>
            """, unsafe_allow_html=True)
        return

    # ── Critical performance alert
    rec = results.get("recall", 0)
    f1  = results.get("f1",     0)
    if rec < 0.50 or f1 < 0.50:
        total_att = (cm_data.get("TP", 0) + cm_data.get("FN", 0)) if cm_data else 0
        miss = round(cm_data.get("FN", 0) / total_att * 100, 2) if total_att > 0 else 0
        st.markdown(f"""
        <div class="ntd-alert">
          <div class="ntd-alert-title">ALERT — CRITICAL PERFORMANCE</div>
          <div class="ntd-alert-body">
            Recall = {rec:.4f} · Miss rate = {miss:.2f}% — the model is missing most attacks.
            For Isolation Forest: increase contamination (~0.17).
            For better performance: use Random Forest or supervised XGBoost.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── 4 metric cards
    c1, c2, c3, c4 = st.columns(4)
    for col, (label, key, cls_) in zip(
        [c1, c2, c3, c4],
        [("ACCURACY",  "accuracy",  "c-red"),
         ("PRECISION", "precision", "c-green"),
         ("RECALL",    "recall",    "c-yellow"),
         ("F1 SCORE",  "f1",        "c-accent")],
    ):
        with col:
            st.markdown(hud_card(label, results.get(key, 0), cls_),
                        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Bars + stat row
    bars_html = (
        bar_row("ACCURACY",  results.get("accuracy",  0)) +
        bar_row("PRECISION", results.get("precision", 0)) +
        bar_row("RECALL",    results.get("recall",    0)) +
        bar_row("F1",        results.get("f1",        0))
    )
    ov     = results.get("overfitting", False)
    ov_lbl = "YES" if ov else "NO"
    ov_col = T.ACCENT if ov else T.DIMMED

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:1.2rem;">
      <div style="background:{T.CARD};border:1px solid {T.BORDER};border-radius:2px;padding:1rem 1.2rem;">
        <div class="sec-label" style="margin-top:0">VISUALIZATION</div>
        <div class="bar-section">{bars_html}</div>
      </div>
      <div class="stat-row" style="flex-direction:column;height:fit-content;">
        <div class="stat-cell">
          <div class="stat-cell-label">ROC AUC</div>
          <div class="stat-cell-value">{results.get("roc_auc", "N/A")}</div>
        </div>
        <div class="stat-cell">
          <div class="stat-cell-label">Training time</div>
          <div class="stat-cell-value">{results.get("time", "-")} s</div>
        </div>
        <div class="stat-cell">
          <div class="stat-cell-label">Overfitting (gap={results.get("gap",0):.4f})</div>
          <div class="stat-cell-value" style="color:{ov_col}">{ov_lbl}</div>
          <div class="stat-cell-sub">Train={results.get("train_acc",0):.4f} · Test={results.get("test_acc",0):.4f}</div>
        </div>
        <div class="stat-cell">
          <div class="stat-cell-label">Run</div>
          <div class="stat-cell-value" style="font-size:0.75rem;color:{T.DIMMED};">
            {st.session_state.last_dataset} · {st.session_state.last_model} · v{st.session_state.last_version}
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    cl, cr = st.columns(2)

    # ── Confusion Matrix
    with cl:
        st.markdown("<div class='sec-label'>CONFUSION MATRIX</div>", unsafe_allow_html=True)
        if cm_data:
            is_dark = st.session_state.theme == "dark"
            c_zero  = "#0e0e0e" if is_dark else "#f5f5f5"
            c_mid   = "#3d0a0a" if is_dark else "#f5c6c6"
            c_high  = "#c0392b"
            fig_cm  = go.Figure(data=go.Heatmap(
                z=[[cm_data["TN"], cm_data["FP"]],
                   [cm_data["FN"], cm_data["TP"]]],
                x=["Predicted BENIGN", "Predicted ATTACK"],
                y=["Actual BENIGN",    "Actual ATTACK"],
                text=[[f"TN\n{cm_data['TN']:,}", f"FP\n{cm_data['FP']:,}"],
                      [f"FN\n{cm_data['FN']:,}", f"TP\n{cm_data['TP']:,}"]],
                texttemplate="%{text}",
                textfont={"size": 12, "family": "Share Tech Mono"},
                colorscale=[[0, c_zero], [0.5, c_mid], [1, c_high]],
                showscale=False,
            ))
            fig_cm.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=T.TEXT, family="Share Tech Mono"),
                margin=dict(l=10, r=10, t=10, b=10), height=260,
            )
            st.plotly_chart(fig_cm, use_container_width=True)

    # ── CM detail + miss rate
    with cr:
        st.markdown("<div class='sec-label'>DETAIL</div>", unsafe_allow_html=True)
        if cm_data:
            total_att = cm_data["TP"] + cm_data["FN"]
            miss_rate = round(cm_data["FN"] / total_att * 100, 2) if total_att > 0 else 0
            fn_cls    = "danger" if miss_rate > 50 else ""
            st.markdown(f"""
            <div class='cm-grid'>
              <div class='cm-cell tp'><div class='cm-num'>{cm_data["TP"]:,}</div><div class='cm-label'>True Positive</div></div>
              <div class='cm-cell tn'><div class='cm-num'>{cm_data["TN"]:,}</div><div class='cm-label'>True Negative</div></div>
              <div class='cm-cell fp'><div class='cm-num'>{cm_data["FP"]:,}</div><div class='cm-label'>False Positive</div></div>
              <div class='cm-cell fn'><div class='cm-num {fn_cls}'>{cm_data["FN"]:,}</div><div class='cm-label'>False Negative</div></div>
            </div>
            <div class="miss-banner">
              <div class="miss-banner-label">Miss Rate<br>(FN / attacks)</div>
              <div class="miss-banner-value">{miss_rate:.2f}%</div>
              <div class="miss-banner-sub">{cm_data["FN"]:,} attacks<br>undetected</div>
            </div>
            """, unsafe_allow_html=True)

    # ── ROC Curve
    if roc_data.get("fpr") and results.get("roc_auc"):
        st.markdown("---")
        st.markdown("<div class='sec-label'>ROC CURVE</div>", unsafe_allow_html=True)
        fig_roc = go.Figure()
        fig_roc.add_trace(go.Scatter(
            x=roc_data["fpr"], y=roc_data["tpr"],
            mode="lines", name=f"AUC = {results['roc_auc']:.4f}",
            line=dict(color=T.ACCENT, width=2),
            fill="tozeroy", fillcolor=hex_to_rgba(T.ACCENT, 0.06),
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
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
            margin=dict(l=20, r=20, t=20, b=20), height=280,
        )
        st.plotly_chart(fig_roc, use_container_width=True)

    # ── Feature Importance
    if fi_data:
        st.markdown("---")
        st.markdown("<div class='sec-label'>TOP 10 FEATURE IMPORTANCE</div>", unsafe_allow_html=True)
        fi_df = pd.DataFrame(list(fi_data.items()),
                             columns=["Feature", "Score"]).sort_values("Score")
        fig_fi = go.Figure(go.Bar(
            x=fi_df["Score"], y=fi_df["Feature"], orientation="h",
            marker=dict(color=fi_df["Score"],
                        colorscale=[[0, T.BORDER], [1, T.ACCENT]],
                        showscale=False),
        ))
        fig_fi.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=T.TEXT, family="Share Tech Mono", size=10),
            xaxis=dict(gridcolor=T.BORDER), yaxis=dict(gridcolor=T.BORDER),
            margin=dict(l=10, r=10, t=10, b=10), height=340,
        )
        st.plotly_chart(fig_fi, use_container_width=True)

    # ── Report download
    if st.session_state.report_bytes:
        st.markdown("---")
        st.markdown("<div class='sec-label'>REPORT</div>", unsafe_allow_html=True)
        st.download_button(
            label           = "DOWNLOAD REPORT (.txt)",
            data            = st.session_state.report_bytes,
            file_name       = st.session_state.report_filename or "ntd_report.txt",
            mime            = "text/plain",
            use_container_width=True,
        )

    # ── Pipeline log
    if st.session_state.logs:
        with st.expander("PIPELINE LOG"):
            st.code("\n".join(st.session_state.logs), language="text")


def render_tab_results(T, sidebar: dict):
    """Entry point for Tab 1."""
    if sidebar["run_btn"]:
        run_pipeline(T, sidebar)
    render_results(T)