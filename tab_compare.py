# ══════════════════════════════════════════════════════════════
#   tab_compare.py — Tab 4 : Comparaison runs MLflow
# ══════════════════════════════════════════════════════════════

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime as _dt


def render_tab_compare(T):
    """ Displays the MLflow multi-run comparison tab."""

    st.markdown(
        "<div class='sec-label' style='margin-top:0'>COMPARAISON — RUNS MLFLOW</div>",
        unsafe_allow_html=True,
    )

    # ── Import MLflow
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        client    = MlflowClient()
        mlflow_ok = True
    except Exception as _e:
        mlflow_ok = False
        st.error(f"MLflow not available : {_e}")

    if not mlflow_ok:
        return

    # ── Info schéma
    st.markdown(f"""
    <div style="background:{T.CARD};border:1px solid {T.BORDER};
                border-left:3px solid {T.DIMMED};border-radius:0 2px 2px 0;
                padding:0.7rem 1rem;margin-bottom:1rem;
                font-family:Share Tech Mono,monospace;font-size:0.65rem;color:{T.DIMMED};">
      MLflow SCHEMA &nbsp;·&nbsp;
      <span style="color:{T.TEXT};">Experience</span> = Dataset &nbsp;|&nbsp;
      <span style="color:{T.TEXT};">Run</span> = Algorithme + Version
      &nbsp;·&nbsp; Freely select the runs to compare
    </div>
    """, unsafe_allow_html=True)

    # ── Liste des expériences
    try:
        all_exps  = client.search_experiments(order_by=["name ASC"])
        exp_names = [e.name for e in all_exps if e.lifecycle_stage == "active"]
    except Exception:
        exp_names = []

    if not exp_names:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">[ ]</div>
          <div class="ntd-empty-text">No MLflow experience required — start a training run first</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Sélection expérience
    col_ds, col_ref = st.columns([4, 1])
    with col_ds:
        selected_exp = st.selectbox(
            "Dataset / Expérience MLflow", exp_names, key="cmp_exp",
            help="Each MLflow experiment corresponds to a dataset",
        )
    with col_ref:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↺ Refresh", key="cmp_refresh", use_container_width=True):
            st.rerun()

    # ── Charger les runs
    exp_obj = client.get_experiment_by_name(selected_exp)
    if not exp_obj:
        st.warning(f"Experience not found : {selected_exp}")
        return

    try:
        runs_raw = client.search_runs(
            experiment_ids=[exp_obj.experiment_id],
            order_by=["start_time DESC"],
            max_results=200,
        )
    except Exception as _e2:
        st.warning(f"Loading error : {_e2}")
        return

    if not runs_raw:
        st.markdown(f"""
        <div class="ntd-alert">
          <div class="ntd-alert-title">NO RUN</div>
          <div class="ntd-alert-body">
            No run in "{selected_exp}". Run a training session on this dataset.
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Labels des runs
    def _run_label(r):
        name   = r.data.tags.get("mlflow.runName", r.info.run_id[:8])
        ts     = _dt.fromtimestamp(r.info.start_time / 1000).strftime("%d/%m %H:%M")
        recall = r.data.metrics.get("recall", 0)
        status = r.info.status
        flag   = "" if status == "FINISHED" else f" [{status}]"
        return f"{name}{flag} — {ts} — Recall={recall*100:.1f}%"

    run_labels = [_run_label(r) for r in runs_raw]

    st.markdown(
        f'<div class="ntd-label" style="margin:0.6rem 0 0.3rem;">'
        f'{len(runs_raw)} RUN(S) dans "{selected_exp}"</div>',
        unsafe_allow_html=True,
    )

    selected_labels = st.multiselect(
        "Runs to compare",
        options=run_labels,
        default=run_labels[:min(4, len(run_labels))],
        label_visibility="collapsed",
        key="cmp_runs",
    )

    if len(selected_labels) < 2:
        st.info("Select at least 2 runs to start the comparison.")
        return

    sel_idx  = [run_labels.index(lb) for lb in selected_labels]
    sel_runs = [runs_raw[i] for i in sel_idx]

    # ── Extraction métriques
    def _m(r, k, d=0):  return r.data.metrics.get(k, d)
    def _p(r, k, d="—"):
        v = r.data.params.get(k)
        return v if v is not None else d

    labels    = [r.data.tags.get("mlflow.runName", r.info.run_id[:8]) for r in sel_runs]
    rec_vals  = [_m(r, "recall")    for r in sel_runs]
    f1_vals   = [_m(r, "f1_score")  for r in sel_runs]
    prec_vals = [_m(r, "precision") for r in sel_runs]
    acc_vals  = [_m(r, "accuracy")  for r in sel_runs]
    fn_vals   = [int(_m(r, "FN", 0)) for r in sel_runs]
    fp_vals   = [int(_m(r, "FP", 0)) for r in sel_runs]
    tp_vals   = [int(_m(r, "TP", 0)) for r in sel_runs]
    time_vals = [_m(r, "train_time", 0) for r in sel_runs]
    auc_vals  = [_m(r, "roc_auc",  0)   for r in sel_runs]
    n = len(sel_runs)

    reds  = ["#c0392b","#e74c3c","#922b21","#f1948a","#7b241c","#c0392b","#96281b","#d98880"]
    grays = ["#e8e8e8","#aaaaaa","#666666","#333333","#bbbbbb","#888888","#555555","#dddddd"]
    colors = [reds[i % len(reds)] if i % 2 == 0 else grays[i % len(grays)] for i in range(n)]

    # ── Tableau récapitulatif
    st.markdown("<div class='sec-label'>SUMMARY TABLE</div>", unsafe_allow_html=True)
    recap = []
    for i, r in enumerate(sel_runs):
        total_att = tp_vals[i] + fn_vals[i]
        miss = round(fn_vals[i] / total_att * 100, 2) if total_att > 0 else 0
        recap.append({
            "Run"      : labels[i],
            "Run ID"   : r.info.run_id[:10],
            "Status"   : r.info.status,
            "Accuracy" : f"{acc_vals[i]*100:.2f}%",
            "Precision": f"{prec_vals[i]*100:.2f}%",
            "Recall"   : f"{rec_vals[i]*100:.2f}%",
            "F1"       : f"{f1_vals[i]:.4f}",
            "AUC"      : f"{auc_vals[i]:.4f}" if auc_vals[i] else "N/A",
            "TP"       : str(tp_vals[i]),
            "FN"       : str(fn_vals[i]),
            "FP"       : str(fp_vals[i]),
            "Miss%"    : f"{miss:.2f}%",
            "Time(s)"  : f"{time_vals[i]:.2f}",
        })
    df_recap = pd.DataFrame(recap).astype(str)
    st.dataframe(df_recap, use_container_width=True, hide_index=True)

    # ── Hyperparams
    param_keys = set()
    for r in sel_runs:
        param_keys.update(r.data.params.keys())
    if param_keys:
        with st.expander("PARAMETRES COMPARES (hyperparams)"):
            param_rows = [{"Run": labels[i], **{k: _p(r, k) for k in sorted(param_keys)}}
                          for i, r in enumerate(sel_runs)]
            st.dataframe(pd.DataFrame(param_rows).astype(str), use_container_width=True, hide_index=True)

    # ── Graphique métriques
    st.markdown("<div class='sec-label'>RECALL / F1 / PRECISION / ACCURACY</div>", unsafe_allow_html=True)
    fig_bar = go.Figure()
    for i in range(n):
        fig_bar.add_trace(go.Bar(
            name=labels[i],
            x=["Recall","F1","Precision","Accuracy"],
            y=[rec_vals[i], f1_vals[i], prec_vals[i], acc_vals[i]],
            marker_color=colors[i], opacity=0.9,
            text=[f"{v*100:.1f}%" for v in [rec_vals[i], f1_vals[i], prec_vals[i], acc_vals[i]]],
            textposition="outside",
            textfont=dict(size=9, family="Share Tech Mono"),
        ))
    fig_bar.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=T.TEXT, family="Share Tech Mono", size=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9), orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(gridcolor=T.BORDER), yaxis=dict(gridcolor=T.BORDER, range=[0, 1.22]),
        margin=dict(l=10, r=10, t=50, b=10), height=360,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── FN + FP
    col_fn, col_fp = st.columns(2)
    with col_fn:
        st.markdown("<div class='sec-label'>FAILED ATTACKS — FN</div>", unsafe_allow_html=True)
        fig_fn = go.Figure(go.Bar(
            x=labels, y=fn_vals,
            marker_color=[T.ACCENT if v == max(fn_vals) else T.DIMMED for v in fn_vals],
            opacity=0.85, text=[f"{v:,}" for v in fn_vals], textposition="outside",
            textfont=dict(size=9, family="Share Tech Mono"),
        ))
        fig_fn.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=T.TEXT, family="Share Tech Mono", size=9),
            xaxis=dict(gridcolor=T.BORDER, tickangle=-20),
            yaxis=dict(gridcolor=T.BORDER, title="False Negatives"),
            margin=dict(l=10, r=10, t=24, b=10), height=280,
        )
        st.plotly_chart(fig_fn, use_container_width=True)

    with col_fp:
        st.markdown("<div class='sec-label'>FALSE ALARMS — FP</div>", unsafe_allow_html=True)
        fig_fp = go.Figure(go.Bar(
            x=labels, y=fp_vals, marker_color=T.DIMMED, opacity=0.8,
            text=[f"{v:,}" for v in fp_vals], textposition="outside",
            textfont=dict(size=9, family="Share Tech Mono"),
        ))
        fig_fp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=T.TEXT, family="Share Tech Mono", size=9),
            xaxis=dict(gridcolor=T.BORDER, tickangle=-20),
            yaxis=dict(gridcolor=T.BORDER, title="False Positives"),
            margin=dict(l=10, r=10, t=24, b=10), height=280,
        )
        st.plotly_chart(fig_fp, use_container_width=True)

    # ── Temps d'entraînement
    st.markdown("<div class='sec-label'>TRAINING TIME (seconds)</div>", unsafe_allow_html=True)
    _safe_t = [v for v in time_vals if v > 0]
    fig_time = go.Figure(go.Bar(
        x=labels, y=time_vals,
        marker_color=[T.TEXT if (_safe_t and v == min(_safe_t)) else T.DIMMED for v in time_vals],
        opacity=0.8, text=[f"{v:.1f}s" for v in time_vals], textposition="outside",
        textfont=dict(size=9, family="Share Tech Mono"),
    ))
    fig_time.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=T.TEXT, family="Share Tech Mono", size=9),
        xaxis=dict(gridcolor=T.BORDER, tickangle=-20),
        yaxis=dict(gridcolor=T.BORDER, title="Secondes"),
        margin=dict(l=10, r=10, t=24, b=10), height=260,
    )
    st.plotly_chart(fig_time, use_container_width=True)

    # ── Verdict
    st.markdown("<div class='sec-label'>VERDICT</div>", unsafe_allow_html=True)
    best_rec  = rec_vals.index(max(rec_vals))
    best_f1   = f1_vals.index(max(f1_vals))
    best_fn   = fn_vals.index(min(fn_vals))
    best_fp   = fp_vals.index(min(fp_vals))
    best_time = time_vals.index(min(_safe_t)) if _safe_t else 0

    verdicts = [
        ("Best Recall",                best_rec,  f"{rec_vals[best_rec]*100:.2f}%", True),
        ("Best F1",                    best_f1,   f"{f1_vals[best_f1]:.4f}",        False),
        ("Less (FN)", best_fn,   f"{fn_vals[best_fn]:,}",          True),
        ("Less (FP)",  best_fp,   f"{fp_vals[best_fp]:,}",          False),
        ("Faster",                    best_time, f"{time_vals[best_time]:.1f}s",   False),
    ]
    for _crit, _idx, _val, _key in verdicts:
        _bc = T.ACCENT if _key else T.DIMMED
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    background:{T.CARD};border:1px solid {T.BORDER};
                    border-left:3px solid {_bc};border-radius:0 2px 2px 0;
                    padding:0.6rem 1rem;margin-bottom:5px;">
          <div style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                      color:{T.DIMMED};letter-spacing:0.1em;">{_crit}</div>
          <div style="font-family:Share Tech Mono,monospace;font-size:0.85rem;color:{T.TEXT};">
            {labels[_idx]}
          </div>
          <span class="hud-card-badge badge-g">{_val}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Score composite
    _max_t  = max(time_vals) if max(time_vals) > 0 else 1
    _scores = [
        0.45 * rec_vals[i] + 0.35 * f1_vals[i] + 0.20 * (1 - time_vals[i] / _max_t)
        for i in range(n)
    ]
    _best = _scores.index(max(_scores))
    st.markdown(f"""
    <div style="background:{T.CARD};border:1px solid {T.ACCENT};
                border-radius:2px;padding:1rem 1.2rem;margin-top:0.8rem;">
      <div style="font-family:Share Tech Mono,monospace;font-size:0.6rem;
                  letter-spacing:0.14em;color:{T.ACCENT};margin-bottom:6px;">
        RECOMMANDATION — Recall 45% · F1 35% · Vitesse 20%
      </div>
      <div style="font-family:Share Tech Mono,monospace;font-size:1rem;
                  color:{T.TEXT};font-weight:700;">
        {labels[_best]}
      </div>
      <div style="font-family:Share Tech Mono,monospace;font-size:0.62rem;
                  color:{T.DIMMED};margin-top:4px;">
        Score={_scores[_best]:.4f} · Recall={rec_vals[_best]*100:.2f}% ·
        F1={f1_vals[_best]:.4f} · FN={fn_vals[_best]:,}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Lien MLflow UI
    st.markdown("---")
    st.markdown(f"""
    <div style="background:{T.CARD};border:1px solid {T.BORDER};
                border-radius:2px;padding:0.75rem 1rem;">
      <span style="font-family:Share Tech Mono,monospace;font-size:0.6rem;color:{T.DIMMED};">
        Détail complet dans MLflow UI :
      </span>
      &nbsp;
      <code style="font-family:Share Tech Mono,monospace;font-size:0.72rem;color:{T.TEXT};">
        mlflow ui --port 5000
      </code>
      <span style="font-family:Share Tech Mono,monospace;font-size:0.62rem;color:{T.DIMMED};margin-left:10px;">
        → http://localhost:5000
      </span>
    </div>
    """, unsafe_allow_html=True)