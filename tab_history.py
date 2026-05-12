# ══════════════════════════════════════════════════════════════
#   tab_history.py — Tab 2 : Run History
# ══════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app_helpers import score_cls, score_color


def render_tab_history(T):
    """Displays the session history and runs from the database."""

    # ── Clear button
    col_cl, _ = st.columns([1, 4])
    with col_cl:
        if st.button("CLEAR HISTORY", key="clear_hist_btn"):
            st.session_state.history = []
            st.rerun()

    history = st.session_state.history

    # ── DB loading
    try:
        from db import get_all_experiments, get_best_experiment, is_connected
        db_experiments = get_all_experiments()
        db_label       = "MongoDB" if is_connected() else "JSON"
    except Exception:
        db_experiments = []
        db_label       = "N/A"

    if not history and not db_experiments:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">[ ]</div>
          <div class="ntd-empty-text">No runs recorded</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Current session history
    if history:
        st.markdown(
            f'<div class="ntd-label" style="margin-bottom:0.8rem;">'
            f'{len(history)} RUN(S) — CURRENT SESSION</div>',
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
                f'<div class="hist-score" style="color:{score_color(v, T)};">{v:.4f}</div>'
                f'</div>'
                for k, v in [
                    ("ACC",  m.get("accuracy",  0)),
                    ("PREC", m.get("precision", 0)),
                    ("REC",  m.get("recall",    0)),
                    ("F1",   f1v),
                ]
            )
            fn_val    = cm_.get("FN", 0) if cm_ else 0
            total_att = (cm_.get("TP", 0) + fn_val) if cm_ else 0
            miss      = round(fn_val / total_att * 100, 2) if total_att > 0 else 0

            st.markdown(f"""
            <div class="hist-row">
              <div style="min-width:200px">
                <div class="hist-model">{run['model']}</div>
                <div class="hist-ts">{run.get('dataset','—')} · v{run.get('version','?')}</div>
                <div class="hist-ts">{run['date']} {run['time']}</div>
                <div style="font-family:Share Tech Mono,monospace;font-size:0.58rem;
                            color:{T.ACCENT};margin-top:2px;">
                  Miss={miss:.1f}%  FN={fn_val:,}
                </div>
              </div>
              <div style="display:flex;gap:22px;flex:1;justify-content:center">
                {scores_html}
              </div>
              <span class="hud-card-badge badge-{c}">{lbl}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── DB history
    if db_experiments:
        st.markdown("---")
        st.markdown(
            f'<div class="ntd-label" style="margin-bottom:0.8rem;">'
            f'DATABASE ({db_label})</div>',
            unsafe_allow_html=True,
        )
        rows = []
        for e in db_experiments:
            m = e.get("metrics", {})
            c = e.get("confusion_matrix", {})
            rows.append({
                "Run ID"  : e.get("run_id", "?"),
                "Dataset" : e.get("dataset_id", "?"),
                "Model"   : e.get("model_name", "?"),
                "v"       : f"v{e.get('version', '?')}",
                "Date"    : e.get("date", "")[:16],
                "Recall"  : f"{m.get('recall', 0)*100:.2f}%",
                "F1"      : f"{m.get('f1_score', 0)*100:.2f}%",
                "AUC"     : f"{m.get('roc_auc', 0):.4f}" if m.get("roc_auc") else "N/A",
                "FN"      : c.get("FN", "-"),
                "Miss%"   : f"{c.get('miss_rate_pct', 0):.2f}%",
                "Time(s)" : m.get("training_time", "-"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # DB comparative chart
        if len(rows) > 1:
            df_c = pd.DataFrame([{
                "Label" : f"{e['model_name']} v{e.get('version','?')}",
                "Recall": e["metrics"].get("recall",   0),
                "F1"    : e["metrics"].get("f1_score", 0),
            } for e in db_experiments])
            fig_h = go.Figure()
            fig_h.add_trace(go.Bar(
                name="Recall", x=df_c["Label"], y=df_c["Recall"],
                marker_color=T.ACCENT, opacity=0.9))
            fig_h.add_trace(go.Bar(
                name="F1", x=df_c["Label"], y=df_c["F1"],
                marker_color=T.TEXT, opacity=0.6))
            fig_h.update_layout(
                barmode="group",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=T.TEXT, family="Share Tech Mono", size=10),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor=T.BORDER),
                yaxis=dict(gridcolor=T.BORDER, range=[0, 1.05]),
                margin=dict(l=10, r=10, t=10, b=10), height=280,
            )
            st.plotly_chart(fig_h, use_container_width=True)

        # Best DB model
        try:
            from db import get_best_experiment
            best = get_best_experiment("recall")
            if best:
                bm = best.get("metrics", {})
                bc = best.get("confusion_matrix", {})
                st.markdown(f"""
                <div style="background:{T.CARD};border:1px solid {T.BORDER};
                            border-left:3px solid {T.TEXT};border-radius:0 2px 2px 0;
                            padding:0.9rem 1.1rem;margin-top:0.8rem;">
                  <span class="hud-card-badge badge-g">BEST RECALL</span>
                  <span style="font-family:Share Tech Mono,monospace;font-size:0.9rem;
                               margin-left:12px;color:{T.TEXT};">
                    {best.get("model_name","?")} · {best.get("dataset_id","?")} · v{best.get("version","?")}
                  </span>
                  <div style="font-family:Share Tech Mono,monospace;font-size:0.65rem;
                              color:{T.DIMMED};margin-top:5px;">
                    Recall={bm.get("recall",0):.4f} · F1={bm.get("f1_score",0):.4f} ·
                    FN={bc.get("FN",0):,} · Miss={bc.get("miss_rate_pct",0):.2f}%
                  </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass