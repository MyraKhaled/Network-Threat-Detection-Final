# ══════════════════════════════════════════════════════════════
#   tab_datasets.py — Tab 3 : Dataset Registry
# ══════════════════════════════════════════════════════════════

import streamlit as st


def render_tab_datasets(T):
    """Displays the list of datasets registered in the database with their runs and reports."""

    try:
        from db import get_all_datasets, get_reports_by_dataset, get_experiments_by_dataset
        datasets = get_all_datasets()
    except Exception:
        datasets = []

    if not datasets:
        st.markdown("""
        <div class="ntd-empty">
          <div class="ntd-empty-icon">[ ]</div>
          <div class="ntd-empty-text">No dataset registered — run a training first</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(
        f'<div class="ntd-label" style="margin-bottom:1rem;">'
        f'{len(datasets)} DATASET(S) REGISTERED</div>',
        unsafe_allow_html=True,
    )

    for ds in datasets:
        ds_id   = ds.get("dataset_id", "?")
        runs    = get_experiments_by_dataset(ds_id)
        reports = get_reports_by_dataset(ds_id)
        n_runs  = len(runs)
        n_rep   = len(reports)

        best_rec = max((r.get("metrics", {}).get("recall", 0) for r in runs), default=0)
        best_mod = next(
            (r.get("model_name", "?") for r in runs
             if r.get("metrics", {}).get("recall", 0) == best_rec),
            "—"
        )

        versions_html = " · ".join(
            f'<span style="color:{T.ACCENT};">'
            f'{r.get("model_name","?")} v{r.get("version","?")}'
            f'</span>'
            for r in sorted(runs, key=lambda x: x.get("date", ""), reverse=True)[:6]
        )

        st.markdown(f"""
        <div style="background:{T.CARD};border:1px solid {T.BORDER};
                    border-left:3px solid {T.ACCENT};border-radius:0 2px 2px 0;
                    padding:1.1rem 1.3rem;margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
            <div>
              <div style="font-family:Share Tech Mono,monospace;font-size:0.9rem;
                          color:{T.TEXT};letter-spacing:0.06em;">{ds_id}</div>
              <div style="font-family:Share Tech Mono,monospace;font-size:0.6rem;
                          color:{T.DIMMED};margin-top:3px;">
                Original file : {ds.get("original_name","?")}
              </div>
            </div>
            <div style="text-align:right">
              <span class="hud-card-badge badge-g">{n_runs} runs</span>
              &nbsp;
              <span class="hud-card-badge badge-y">{n_rep} reports</span>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;
                      margin-top:0.9rem;border-top:1px solid {T.BORDER};padding-top:0.9rem;">
            <div>
              <div class="stat-cell-label">Total rows</div>
              <div class="stat-cell-value">{ds.get("total_rows",0):,}</div>
            </div>
            <div>
              <div class="stat-cell-label">Columns</div>
              <div class="stat-cell-value">{ds.get("total_cols",0)}</div>
            </div>
            <div>
              <div class="stat-cell-label">BENIGN</div>
              <div class="stat-cell-value">{ds.get("benign_count",0):,}</div>
            </div>
            <div>
              <div class="stat-cell-label">ATTACK</div>
              <div class="stat-cell-value">{ds.get("attack_count",0):,}</div>
            </div>
          </div>

          <div style="margin-top:0.8rem;font-family:Share Tech Mono,monospace;font-size:0.62rem;">
            <span style="color:{T.DIMMED};">Best Recall : </span>
            <span style="color:{T.TEXT};">{best_rec:.4f}</span>
            <span style="color:{T.DIMMED};margin-left:10px;">({best_mod})</span>
          </div>

          <div style="margin-top:0.6rem;font-family:Share Tech Mono,monospace;font-size:0.6rem;color:{T.DIMMED};">
            Versions : {versions_html if versions_html else "—"}
          </div>

          <div style="margin-top:0.6rem;font-family:Share Tech Mono,monospace;font-size:0.6rem;color:{T.DIMMED};">
            First seen : {ds.get("first_seen","?")[:16]} ·
            Last run : {ds.get("last_seen","?")[:16]}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Reports linked to the dataset
        if reports:
            with st.expander(f"Reports — {ds_id} ({n_rep})"):
                for rep in reports:
                    col_i, col_dl = st.columns([4, 1])
                    with col_i:
                        st.markdown(
                            f'<div style="font-family:Share Tech Mono,monospace;font-size:0.7rem;color:{T.DIMMED};">'
                            f'{rep.get("run_id","?")} · {rep.get("generated_at","?")[:16]}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with col_dl:
                        rep_text = rep.get("report_text", "")
                        if rep_text:
                            fn = f'{rep.get("run_id","report")}.txt'
                            st.download_button(
                                label           = "DL",
                                data            = rep_text.encode("utf-8"),
                                file_name       = fn,
                                mime            = "text/plain",
                                key             = f"dl_{rep.get('report_id','x')}",
                            )