import streamlit as st

from app_init     import init_page, init_session_state, apply_theme
from app_sidebar  import render_sidebar
from app_header   import render_header
from tab_results  import render_tab_results
from tab_history  import render_tab_history
from tab_datasets import render_tab_datasets
from tab_compare  import render_tab_compare
from tab_report   import render_tab_report


#1.Configuration page
init_page()

#Session state
init_session_state()

#Thème + CSS
T = apply_theme()

#4. Sidebar
sidebar = render_sidebar(T)

# ── 5. En-tête + carte dataset
render_header(T, sidebar["test_size"])

#6. Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "[ RESULTS ]", "[ HISTORY ]", "[ DATASETS ]", "[ COMPARE ]", "[ REPORT ]"
])

with tab1:
    render_tab_results(T, sidebar)

with tab2:
    render_tab_history(T)

with tab3:
    render_tab_datasets(T)

with tab4:
    render_tab_compare(T)

with tab5:
    render_tab_report(T)