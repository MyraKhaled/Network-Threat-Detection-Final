# ui_styles.py — NTD  •  Cyber-terminal aesthetic

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    BG:     str
    CARD:   str
    SB:     str
    ACCENT: str
    RED:    str
    TEXT:   str
    DIMMED: str
    BORDER: str
    GREEN:  str
    YELLOW: str
    SHADOW: str
    GLOW:   str


DARK = Theme(
    BG     = "#050810",
    CARD   = "#0a0e1a",
    SB     = "#06090f",
    ACCENT = "#e63946",
    RED    = "#e63946",
    TEXT   = "#e8edf5",
    DIMMED = "#4a5568",
    BORDER = "#151d2e",
    GREEN  = "#00ff9d",
    YELLOW = "#ffb703",
    SHADOW = "rgba(0,0,0,0.7)",
    GLOW   = "rgba(230,57,70,0.18)",
)

LIGHT = Theme(
    BG     = "#f0f2f5",
    CARD   = "#ffffff",
    SB     = "#e8ebf0",
    ACCENT = "#c1121f",
    RED    = "#c1121f",
    TEXT   = "#0d1117",
    DIMMED = "#6b7280",
    BORDER = "#d1d5db",
    GREEN  = "#0a7c59",
    YELLOW = "#b45309",
    SHADOW = "rgba(0,0,0,0.1)",
    GLOW   = "rgba(193,18,31,0.12)",
)


def load_css(theme: str = "dark") -> str:
    t       = LIGHT if theme == "light" else DARK
    is_dark = theme == "dark"
    scanline    = "rgba(0,0,0,0.15)"    if is_dark else "rgba(0,0,0,0.03)"
    grid_color  = "rgba(230,57,70,0.04)" if is_dark else "rgba(193,18,31,0.03)"

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Orbitron:wght@400;600;700;900&display=swap');

/* ══ RESET ══════════════════════════════════════════════════ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

/* ══ BASE APP ═══════════════════════════════════════════════ */
html, body, .stApp {{
    background-color: {t.BG} !important;
    color: {t.TEXT} !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    line-height: 1.65 !important;
}}

/* Grid/scanline texture — decorative only, pointer-events none */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background-image:
        repeating-linear-gradient(0deg, transparent, transparent 2px, {scanline} 2px, {scanline} 4px),
        repeating-linear-gradient(90deg, {grid_color} 0px, {grid_color} 1px, transparent 1px, transparent 60px),
        repeating-linear-gradient(0deg,  {grid_color} 0px, {grid_color} 1px, transparent 1px, transparent 60px);
}}

.block-container {{
    padding: 4.5rem 2rem 3rem 2rem !important;
    max-width: 100% !important;
    position: relative;
    z-index: 1;
}}

/* ══ IMPORTANT: DO NOT HIDE header / footer / MainMenu ══════
   We only hide the deploy button, not the entire header bar.
   This keeps the sidebar collapse arrow rendered by Streamlit.
═══════════════════════════════════════════════════════════ */
.stDeployButton {{ display: none !important; }}
footer {{ visibility: hidden !important; }}

/* Style the top Streamlit toolbar to match our theme */
header[data-testid="stHeader"] {{
    background-color: {t.BG} !important;
    border-bottom: 1px solid {t.BORDER} !important;
}}

/* ══ SIDEBAR ════════════════════════════════════════════════ */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div:first-child {{
    background-color: {t.SB} !important;
    border-right: 1px solid {t.BORDER} !important;
}}

/* Section headings inside sidebar */
section[data-testid="stSidebar"] h3 {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.68rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: {t.ACCENT} !important;
    margin: 0.5rem 0 0.55rem !important;
    padding-bottom: 4px !important;
    border-bottom: 1px solid {t.BORDER} !important;
}}

section[data-testid="stSidebar"] hr {{
    border: none !important;
    border-top: 1px solid {t.BORDER} !important;
    margin: 0.65rem 0 !important;
}}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {{
    font-family: 'Rajdhani', sans-serif !important;
    color: {t.TEXT} !important;
    font-size: 0.95rem !important;
    line-height: 1.55 !important;
}}

/* Sidebar widgets */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 4px !important;
    color: {t.TEXT} !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
}}
section[data-testid="stSidebar"] input[type="number"] {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 4px !important;
    color: {t.TEXT} !important;
    font-family: 'Share Tech Mono', monospace !important;
}}
section[data-testid="stSidebar"] [role="slider"] {{
    background-color: {t.ACCENT} !important;
    border-color: {t.ACCENT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stSliderTrackFill"] {{
    background-color: {t.ACCENT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stFileUploadDropzone"] {{
    background-color: {t.CARD} !important;
    border: 1px dashed {t.ACCENT}66 !important;
    border-radius: 6px !important;
    transition: border-color 0.2s, background-color 0.2s !important;
}}
section[data-testid="stSidebar"] [data-testid="stFileUploadDropzone"]:hover {{
    border-color: {t.ACCENT} !important;
    background-color: {t.ACCENT}08 !important;
}}

/* ══ RUN BUTTON ═════════════════════════════════════════════ */
section[data-testid="stSidebar"] .stButton > button {{
    width: 100% !important;
    background-color: transparent !important;
    color: {t.ACCENT} !important;
    border: 1px solid {t.ACCENT} !important;
    border-radius: 3px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1rem !important;
    box-shadow: 0 0 16px {t.GLOW}, inset 0 0 16px {t.GLOW} !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background-color: {t.ACCENT}18 !important;
    box-shadow: 0 0 28px {t.GLOW}, inset 0 0 28px {t.GLOW} !important;
    letter-spacing: 0.2em !important;
}}
section[data-testid="stSidebar"] .stButton > button:active {{
    background-color: {t.ACCENT}30 !important;
}}

/* ══ MAIN AREA BUTTONS ══════════════════════════════════════ */
.stButton > button {{
    background-color: transparent !important;
    color: {t.DIMMED} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 3px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em !important;
    transition: all 0.15s !important;
}}
.stButton > button:hover {{
    border-color: {t.ACCENT} !important;
    color: {t.ACCENT} !important;
    box-shadow: 0 0 12px {t.GLOW} !important;
}}

/* ══ TABS ════════════════════════════════════════════════════ */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background-color: transparent !important;
    border-bottom: 1px solid {t.BORDER} !important;
    border-radius: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    background-color: transparent !important;
    border-radius: 0 !important;
    color: {t.DIMMED} !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.4rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.15s !important;
    margin-bottom: -1px !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    background-color: transparent !important;
    color: {t.ACCENT} !important;
    border-bottom: 2px solid {t.ACCENT} !important;
    box-shadow: none !important;
    text-shadow: 0 0 12px {t.ACCENT}88 !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{
    color: {t.TEXT} !important;
    background-color: {t.ACCENT}0a !important;
}}

/* ══ PROGRESS BAR ═══════════════════════════════════════════ */
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, {t.ACCENT}, {t.RED}) !important;
    box-shadow: 0 0 10px {t.GLOW} !important;
}}

/* ══ NATIVE METRIC ══════════════════════════════════════════ */
[data-testid="stMetric"] {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 6px !important;
    padding: 1.1rem 1.3rem !important;
}}
[data-testid="stMetricLabel"] > div {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.64rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: {t.DIMMED} !important;
}}
[data-testid="stMetricValue"] > div {{
    font-family: 'Orbitron', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: {t.TEXT} !important;
}}

/* ══ EXPANDER ═══════════════════════════════════════════════ */
[data-testid="stExpander"] {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 4px !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.78rem !important;
    color: {t.TEXT} !important;
    letter-spacing: 0.08em !important;
}}

/* ══ DROPDOWN ════════════════════════════════════════════════ */
[data-baseweb="popover"] ul {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 4px !important;
}}
[data-baseweb="popover"] li {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
    color: {t.TEXT} !important;
}}
[data-baseweb="popover"] li:hover {{ background-color: {t.ACCENT}18 !important; }}

/* ══ DATAFRAME ══════════════════════════════════════════════ */
.stDataFrame {{ border: 1px solid {t.BORDER} !important; border-radius: 6px !important; }}
[data-testid="stDataFrameResizable"] th {{
    background-color: {t.CARD} !important;
    color: {t.ACCENT} !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}}

/* ══ CODE BLOCK ═════════════════════════════════════════════ */
.stCode, [data-testid="stCodeBlock"] {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 4px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
}}

/* ══ INFO / WARNING / ERROR BOXES ══════════════════════════ */
[data-testid="stAlert"] {{
    border-radius: 4px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.95rem !important;
    border: 1px solid {t.BORDER} !important;
}}

/* ══ CUSTOM CLASSES ═════════════════════════════════════════ */

.ntd-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.64rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {t.ACCENT};
}}

/* HUD metric card */
.hud-card {{
    background-color: {t.CARD};
    border: 1px solid {t.BORDER};
    border-radius: 6px;
    padding: 1.1rem 1.3rem 1rem;
    position: relative;
    overflow: hidden;
}}
.hud-card::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 0 0 6px 6px;
}}
.hud-card.c-red::after    {{ background:{t.RED};    box-shadow:0 0 10px {t.RED}88; }}
.hud-card.c-green::after  {{ background:{t.GREEN};  box-shadow:0 0 10px {t.GREEN}88; }}
.hud-card.c-yellow::after {{ background:{t.YELLOW}; box-shadow:0 0 10px {t.YELLOW}88; }}
.hud-card.c-accent::after {{ background:{t.ACCENT}; box-shadow:0 0 10px {t.ACCENT}88; }}

.hud-card-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.64rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: {t.DIMMED};
    margin-bottom: 8px;
}}
.hud-card-value {{
    font-family: 'Orbitron', sans-serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: {t.TEXT};
    letter-spacing: -0.01em;
    line-height: 1;
}}
.hud-card-badge {{
    display: inline-block;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.1em;
    padding: 2px 9px;
    border-radius: 2px;
    margin-top: 8px;
    text-transform: uppercase;
}}
.badge-g {{ background:{t.GREEN}18;  color:{t.GREEN};  border:1px solid {t.GREEN}44;  text-shadow:0 0 8px {t.GREEN}88; }}
.badge-y {{ background:{t.YELLOW}18; color:{t.YELLOW}; border:1px solid {t.YELLOW}44; }}
.badge-r {{ background:{t.RED}18;    color:{t.RED};    border:1px solid {t.RED}44;    text-shadow:0 0 8px {t.RED}88; }}

/* CM grid */
.cm-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:8px; }}
.cm-cell {{
    background:{t.CARD}; border:1px solid {t.BORDER};
    border-radius:6px; padding:14px; text-align:center;
}}
.cm-cell.tp {{ border-top:2px solid {t.GREEN};  }}
.cm-cell.tn {{ border-top:2px solid {t.ACCENT}; }}
.cm-cell.fp {{ border-top:2px solid {t.YELLOW}; }}
.cm-cell.fn {{ border-top:2px solid {t.RED};    }}
.cm-num {{
    font-family:'Orbitron',sans-serif;
    font-size:1.4rem; font-weight:700; line-height:1;
}}
.cm-label {{
    font-family:'Share Tech Mono',monospace;
    font-size:0.58rem; color:{t.DIMMED};
    text-transform:uppercase; letter-spacing:0.1em; margin-top:5px;
}}

/* History row */
.hist-row {{
    display:flex; align-items:center; gap:16px;
    background-color:{t.CARD}; border:1px solid {t.BORDER};
    border-left:3px solid {t.ACCENT}; border-radius:4px;
    padding:0.85rem 1.1rem; margin-bottom:0.5rem;
    transition:border-color .15s, box-shadow .15s;
}}
.hist-row:hover {{
    border-left-color:{t.RED};
    box-shadow:-4px 0 20px {t.GLOW};
}}
.hist-model {{
    font-family:'Share Tech Mono',monospace;
    font-size:0.78rem; letter-spacing:0.1em;
    color:{t.ACCENT}; min-width:140px; text-transform:uppercase;
}}
.hist-ts {{
    font-family:'Share Tech Mono',monospace;
    font-size:0.62rem; color:{t.DIMMED}; margin-top:2px;
}}
.hist-score {{
    font-family:'Orbitron',sans-serif;
    font-size:0.92rem; font-weight:600; color:{t.TEXT};
}}
.hist-key {{
    font-family:'Share Tech Mono',monospace;
    font-size:0.6rem; color:{t.DIMMED};
    text-transform:uppercase; letter-spacing:0.12em;
}}

/* Section divider */
.sec-label {{
    font-family:'Share Tech Mono',monospace;
    font-size:0.62rem; letter-spacing:0.16em;
    text-transform:uppercase; color:{t.ACCENT};
    display:flex; align-items:center; gap:10px;
    margin:1.4rem 0 0.8rem;
}}
.sec-label::after {{
    content:''; flex:1; height:1px;
    background:linear-gradient(90deg,{t.BORDER},transparent);
}}

/* Spinner */
@keyframes ntd-spin  {{ to {{ transform:rotate(360deg);  }} }}
@keyframes ntd-spinr {{ to {{ transform:rotate(-360deg); }} }}
@keyframes ntd-pulse {{ 0%,100%{{opacity:1;}}50%{{opacity:0.3;}} }}
@keyframes ntd-blink {{ 0%,49%{{opacity:1;}}50%,100%{{opacity:0;}} }}
@keyframes ntd-dot   {{
    0%,80%,100%{{transform:scale(.2);opacity:.15;}}
    40%        {{transform:scale(1); opacity:1;  }}
}}

.ntd-spinner-wrap {{
    display:flex; flex-direction:column; align-items:center;
    gap:16px; padding:2.5rem 2rem;
    background-color:{t.CARD}; border:1px solid {t.BORDER};
    border-radius:6px; margin:1rem 0;
    position:relative; overflow:hidden;
}}
.ntd-spinner-wrap::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,transparent,{t.ACCENT},transparent);
    animation:ntd-pulse 1.5s ease-in-out infinite;
}}
.ntd-rings {{ position:relative; width:60px; height:60px; }}
.ntd-ring-outer {{
    position:absolute; inset:0;
    border:2px solid {t.BORDER}; border-top-color:{t.ACCENT};
    border-radius:50%; animation:ntd-spin .9s linear infinite;
    box-shadow:0 0 18px {t.ACCENT}55;
}}
.ntd-ring-mid {{
    position:absolute; inset:10px;
    border:1px solid {t.BORDER}; border-right-color:{t.GREEN};
    border-radius:50%; animation:ntd-spinr .65s linear infinite;
}}
.ntd-ring-inner {{
    position:absolute; inset:20px;
    border:1px solid {t.BORDER}; border-bottom-color:{t.YELLOW};
    border-radius:50%; animation:ntd-spin .45s linear infinite;
}}
.ntd-spin-txt {{
    font-family:'Share Tech Mono',monospace;
    font-size:0.72rem; letter-spacing:0.16em;
    text-transform:uppercase; color:{t.ACCENT};
    animation:ntd-blink 1.1s step-end infinite;
}}
.ntd-dots {{ display:flex; gap:6px; }}
.ntd-dot {{
    width:6px; height:6px; border-radius:50%;
    animation:ntd-dot 1.3s ease-in-out infinite;
}}
.ntd-dot.d1 {{ background:{t.ACCENT}; }}
.ntd-dot.d2 {{ background:{t.GREEN};  animation-delay:.15s; }}
.ntd-dot.d3 {{ background:{t.YELLOW}; animation-delay:.30s; }}

/* Empty state */
.ntd-empty {{ text-align:center; padding:3.5rem 2rem; }}
.ntd-empty-icon {{ font-size:2rem; margin-bottom:0.8rem; opacity:0.3; }}
.ntd-empty-text {{
    font-family:'Share Tech Mono',monospace;
    font-size:0.72rem; letter-spacing:0.14em;
    text-transform:uppercase; color:{t.DIMMED};
}}

/* Scrollbar */
::-webkit-scrollbar {{ width:4px; height:4px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:{t.BORDER}; border-radius:99px; }}
::-webkit-scrollbar-thumb:hover {{ background:{t.DIMMED}; }}
</style>
"""