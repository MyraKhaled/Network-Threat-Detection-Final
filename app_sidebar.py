import streamlit as st
from config import (
    TEST_SIZE, RANDOM_STATE,
    DT_MAX_DEPTH, DT_MIN_SAMPLES_SPLIT, DT_MIN_SAMPLES_LEAF,
    RF_N_ESTIMATORS, RF_MAX_DEPTH, RF_MIN_SAMPLES_SPLIT, RF_MIN_SAMPLES_LEAF,
    XGB_N_ESTIMATORS, XGB_MAX_DEPTH, XGB_LEARNING_RATE,
    XGB_ALPHA, XGB_GAMMA, XGB_SUBSAMPLE, XGB_REG_LAMBDA,
    ISO_N_ESTIMATORS, ISO_CONTAMINATION,
)


def render_sidebar(T) -> dict:
    """
    Affiche la sidebar et retourne un dict avec :
      - uploaded      : fichier uploadé (ou None)
      - model_type    : str
      - test_size     : float
      - random_state  : int
      - params        : dict hyperparams
      - run_btn       : bool (bouton cliqué ?)
    """
    with st.sidebar:

        # ── Logo + toggle thème
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(
                f'''<div style="display:flex;align-items:center;gap:10px;">
                  <svg width="34" height="34" viewBox="0 0 32 32" fill="none"
                       xmlns="http://www.w3.org/2000/svg">
                    <path d="M16 2L4 7V16C4 22.627 9.373 28 16 30C22.627 28 28 22.627 28 16V7L16 2Z"
                          stroke="{T.ACCENT}" stroke-width="1.5" fill="none"/>
                    <path d="M16 7L8 10.5V16C8 20.418 11.582 24 16 25.5C20.418 24 24 20.418 24 16V10.5L16 7Z"
                          fill="{T.ACCENT}" opacity="0.15"/>
                    <line x1="11" y1="16" x2="14.5" y2="19.5"
                          stroke="{T.ACCENT}" stroke-width="1.8" stroke-linecap="round"/>
                    <line x1="14.5" y1="19.5" x2="21" y2="12"
                          stroke="{T.ACCENT}" stroke-width="1.8" stroke-linecap="round"/>
                  </svg>
                  <div>
                    <div style="font-family:Share Tech Mono,monospace;font-size:0.92rem;
                                font-weight:700;letter-spacing:0.14em;color:{T.ACCENT};">
                      NTD SYSTEM
                    </div>
                    <div style="font-family:Share Tech Mono,monospace;font-size:0.6rem;
                                letter-spacing:0.18em;color:{T.DIMMED};margin-top:2px;">
                      v3.1 · CIC-IDS2017
                    </div>
                  </div>
                </div>''',
                unsafe_allow_html=True,
            )
        with c2:
               if st.button("⏻", key="theme_btn", help="Toggle dark/light"):
                st.session_state.theme = (
                    "light" if st.session_state.theme == "dark" else "dark"
                )
                st.rerun()

        st.markdown("---")

        # ── Dataset
        st.markdown("### Dataset")
        uploaded = st.file_uploader(
            "file", type=["csv", "json", "xlsx", "xls"],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Modèle
        st.markdown("### Model")
        model_type = st.selectbox(
            "model",
            ["Decision Tree", "Random Forest", "XGBoost", "Isolation Forest"],
            label_visibility="collapsed",
        )

        st.markdown("---")

        #Settings
        st.markdown("### Settings")
        test_size    = st.slider("Test size",    0.1,  0.4, TEST_SIZE,    step=0.05)
        random_state = st.number_input("Random state", 0, 9999, RANDOM_STATE)

        st.markdown("---")

        # ── Hyperparams
        st.markdown("### Hyperparams")
        params = _render_hyperparams(model_type)

        st.markdown("---")
        run_btn = st.button("EXECUTE PIPELINE", use_container_width=True)

    return {
        "uploaded"     : uploaded,
        "model_type"   : model_type,
        "test_size"    : test_size,
        "random_state" : random_state,
        "params"       : params,
        "run_btn"      : run_btn,
    }


def _render_hyperparams(model_type: str) -> dict:
    """Affiche les hyperparamètres selon le modèle sélectionné."""
    if model_type == "Decision Tree":
        return {
            "dt_max_depth"        : st.slider("Max depth",  1,  40, DT_MAX_DEPTH),
            "dt_class_weight"     : st.selectbox("Class weight", ["balanced", "None"]),
            "dt_min_samples_split": st.slider("Min split",  2,  50, DT_MIN_SAMPLES_SPLIT),
            "dt_min_samples_leaf" : st.slider("Min leaf",   1,  50, DT_MIN_SAMPLES_LEAF),
        }
    elif model_type == "Random Forest":
        return {
            "rf_n_estimators"     : st.slider("Trees",      10, 300, RF_N_ESTIMATORS),
            "rf_max_depth"        : st.slider("Max depth",   3,  50, RF_MAX_DEPTH),
            "rf_class_weight"     : st.selectbox("Class weight", ["balanced", "None"]),
            "rf_min_samples_split": st.slider("Min split",   2,  50, RF_MIN_SAMPLES_SPLIT),
            "rf_min_samples_leaf" : st.slider("Min leaf",    1,  50, RF_MIN_SAMPLES_LEAF),
        }
    elif model_type == "XGBoost":
        return {
            "xgb_n_estimators" : st.slider("Trees",        10,  500, XGB_N_ESTIMATORS),
            "xgb_max_depth"    : st.slider("Max depth",     3,   20, XGB_MAX_DEPTH),
            "xgb_learning_rate": st.slider("Learning rate", 0.01, 0.5, XGB_LEARNING_RATE, step=0.01),
            "xgb_alpha"        : st.slider("Alpha (L1)",    0.0,  3.0, XGB_ALPHA,  step=0.1),
            "xgb_gamma"        : st.slider("Gamma",         0.0,  2.0, XGB_GAMMA,  step=0.05),
            "xgb_subsample"    : st.slider("Subsample",     0.5,  1.0, XGB_SUBSAMPLE, step=0.05),
            "xgb_reg_lambda"   : st.slider("Lambda (L2)",   0.0,  3.0, XGB_REG_LAMBDA, step=0.1),
        }
    elif model_type == "Isolation Forest":
        params = {
            "iso_n_estimators" : st.slider("Trees",         10, 400, ISO_N_ESTIMATORS),
            "iso_contamination": st.slider("Contamination", 0.01, 0.4, ISO_CONTAMINATION, step=0.01),
        }
        st.info("Unsupervised — training on BENIGN only")
        return params
    return {}