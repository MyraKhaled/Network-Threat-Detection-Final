# ══════════════════════════════════════════════════════════════
#   tab_report.py — Tab 5 : Report + Download
# ══════════════════════════════════════════════════════════════

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from app_helpers import hex_to_rgba, score_color


def render_tab_report(T):
    """Displays the last run report with radar chart and download button."""

    results = st.session_state.results

    if not results:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">[ ]</div>
          <div class="ntd-empty-text">Run the pipeline to generate a report</div>
        </div>
        """, unsafe_allow_html=True)
        return

    m     = results
    now   = datetime.now().strftime("%d %b %Y · %H:%M:%S")
    model = st.session_state.last_model   or "—"
    ds    = st.session_state.last_dataset or "—"
    ver   = st.session_state.last_version or 1

    # ── Metrics summary
    grid_html = "".join(
        f'<div style="text-align:center">'
        f'<div class="ntd-label" style="font-size:0.56rem">{k}</div>'
        f'<div style="font-family:Share Tech Mono,monospace;font-size:1.2rem;'
        f'color:{score_color(v, T)};margin-top:4px">{v:.4f}</div>'
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
                border-left:3px solid {T.ACCENT};border-radius:0 2px 2px 0;
                padding:1.2rem 1.4rem;margin-bottom:1.2rem;">
      <div class="ntd-label" style="margin-bottom:3px;">REPORT — {now}</div>
      <div style="font-family:Share Tech Mono,monospace;font-size:0.85rem;
                  color:{T.TEXT};margin-bottom:0.9rem;">
        {model.upper()} · {ds} · v{ver}
      </div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px">
        {grid_html}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Radar chart
    cats = ["Accuracy", "Precision", "Recall", "F1"]
    vals = [m.get(k, 0) for k in ["accuracy", "precision", "recall", "f1"]]
    fig_radar = go.Figure(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]],
        fill="toself",
        line=dict(color=T.ACCENT, width=1.5),
        fillcolor=hex_to_rgba(T.ACCENT, 0.07),
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor=T.CARD,
            radialaxis=dict(visible=True, range=[0, 1], gridcolor=T.BORDER,
                            tickfont=dict(color=T.DIMMED, size=8, family="Share Tech Mono")),
            angularaxis=dict(gridcolor=T.BORDER,
                             tickfont=dict(color=T.TEXT, size=10, family="Share Tech Mono")),
        ),
        paper_bgcolor=T.CARD, plot_bgcolor=T.CARD,
        font=dict(color=T.TEXT, family="Share Tech Mono"),
        margin=dict(l=60, r=60, t=40, b=40),
        showlegend=False, height=320,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # ── Download
    st.markdown("---")
    st.markdown("<div class='sec-label'>DOWNLOAD REPORT</div>", unsafe_allow_html=True)
    if st.session_state.report_bytes:
        st.download_button(
            label           = "DOWNLOAD (.txt)",
            data            = st.session_state.report_bytes,
            file_name       = st.session_state.report_filename or "ntd_report.txt",
            mime            = "text/plain",
            use_container_width=True,
        )
    else:
        st.button("DOWNLOAD — no report available",
                  disabled=True, use_container_width=True)

    # ── Text preview
    if st.session_state.get("report_content"):
        with st.expander("REPORT PREVIEW"):
            st.code(st.session_state["report_content"], language=None)

    # ── MLflow link
    st.markdown("---")
    st.markdown("<div class='sec-label'>MLFLOW</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:{T.CARD};border:1px solid {T.BORDER};border-radius:2px;
                padding:0.9rem 1.1rem;">
      <div style="font-family:Share Tech Mono,monospace;font-size:0.65rem;
                  color:{T.DIMMED};margin-bottom:8px;">
        Launch the MLflow UI to compare runs:
      </div>
      <code style="font-family:Share Tech Mono,monospace;font-size:0.75rem;color:{T.TEXT};">
        mlflow ui --port 5000
      </code>
      <br>
      <code style="font-family:Share Tech Mono,monospace;font-size:0.7rem;
                   color:{T.DIMMED};display:block;margin-top:5px;">
        → http://localhost:5000
      </code>
    </div>
    """, unsafe_allow_html=True)