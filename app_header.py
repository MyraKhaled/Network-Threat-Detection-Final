# ══════════════════════════════════════════════════════════════
#   app_header.py — En-tête de page + carte info dataset
# ══════════════════════════════════════════════════════════════

import streamlit as st


def render_header(T, test_size: float):
    # ── Titre
    st.markdown(
        f"""
        <div style="margin-top:-0.5rem;margin-bottom:1.2rem;padding-bottom:0.9rem;
                    border-bottom:1px solid {T.BORDER};">
          <div style="font-family:Share Tech Mono,monospace;font-size:1.9rem;
                      font-weight:700;letter-spacing:0.06em;color:{T.TEXT};line-height:1.15;">
            NETWORK <span style="color:{T.ACCENT};">THREAT</span> DETECTION
          </div>
          <div style="display:flex;align-items:center;gap:20px;margin-top:8px;flex-wrap:wrap;">
            <span style="font-family:Share Tech Mono,monospace;font-size:0.72rem;
                         letter-spacing:0.16em;color:{T.DIMMED};">
              ML-POWERED INTRUSION ANALYSIS — CIC-IDS2017
            </span>
            <span style="font-family:Share Tech Mono,monospace;font-size:0.72rem;
                         color:{T.ACCENT};letter-spacing:0.1em;">
              [ONLINE]
            </span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Carte info dataset
    info_blocks = [
        ("SOURCE",   "Canadian Institute for Cybersecurity — UNB"),
        ("SAMPLES",  "~2.8 million network flow records"),
        ("FEATURES", "78 features — CICFlowMeter"),
        ("CLASSES",  "BENIGN + 14 attack types"),
        ("SPLIT",    f"Train {round((1-test_size)*100)}% / Test {round(test_size*100)}%"),
        ("MODELS",   "Decision Tree · Random Forest · XGBoost · Isolation Forest"),
    ]

    rows_html = "".join(
        f'<div style="display:flex;gap:0;padding:0.38rem 0;border-bottom:1px solid {T.BORDER};">'
        f'<div style="font-family:Share Tech Mono,monospace;font-size:0.6rem;'
        f'letter-spacing:0.14em;color:{T.ACCENT};min-width:100px;padding-top:2px;">{key}</div>'
        f'<div style="font-family:Share Tech Mono,monospace;font-size:0.8rem;color:{T.TEXT};">{val}</div>'
        f'</div>'
        for key, val in info_blocks
    )

    st.markdown(
        f"""
        <div style="background:{T.CARD};border:1px solid {T.BORDER};
                    border-radius:2px;padding:1rem 1.2rem;margin-bottom:1.4rem;">
          <div style="font-family:Share Tech Mono,monospace;font-size:0.65rem;
                      color:{T.DIMMED};letter-spacing:0.12em;margin-bottom:0.6rem;">
            CIC-IDS2017
          </div>
          {rows_html}
          <div style="margin-top:0.8rem;background:{T.CARD2};border:1px solid {T.BORDER};
                      border-left:3px solid {T.ACCENT};border-radius:0 2px 2px 0;
                      padding:0.7rem 0.9rem;">
            <div style="font-family:Share Tech Mono,monospace;font-size:0.58rem;
                        color:{T.ACCENT};letter-spacing:0.14em;margin-bottom:3px;">
              IMBALANCE NOTE
            </div>
            <div style="font-family:Share Tech Mono,monospace;font-size:0.78rem;color:{T.DIMMED};">
              Benign ~83% des enregistrements.
              Used <code style="color:{T.TEXT}">class_weight=balanced</code>
              pour les modeles supervisés.
              Evaluer avec <strong style="color:{T.TEXT}">Recall</strong> et
              <strong style="color:{T.TEXT}">F1</strong>, pas l'accuracy brute.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )