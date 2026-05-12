#   app_init.py
import streamlit as st
from ui_styles import load_css, DARK, LIGHT


def init_page():
    st.set_page_config(
        page_title="NTD — Network Threat Detection",
        page_icon="[NTD]",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={}
    )


def init_session_state():
    defaults = {
        "results"         : None,
        "cm_data"         : None,
        "fi_data"         : {},
        "roc_data"        : {},
        "logs"            : [],
        "history"         : [],
        "report_content"  : "",
        "report_bytes"    : None,
        "report_filename" : "",
        "ran_once"        : False,
        "theme"           : "dark",
        "last_run_id"     : "",
        "last_version"    : 1,
        "last_model"      : "",
        "last_dataset"    : "",
        "db_loaded"       : False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def apply_theme():
    T = DARK if st.session_state.theme == "dark" else LIGHT
    st.markdown(load_css(st.session_state.theme), unsafe_allow_html=True)
    st.markdown("""
    <style>
    /* Cacher menu / deploy / footer */
    #MainMenu                    { display: none !important; }
    [data-testid="stToolbar"]    { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    .stDeployButton              { display: none !important; }
    footer                       { visibility: hidden !important; }
   
    </style>
    """, unsafe_allow_html=True)
    return T


def get_theme():
    return DARK if st.session_state.theme == "dark" else LIGHT