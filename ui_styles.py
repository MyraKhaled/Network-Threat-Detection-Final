# ui_styles.py — NTD  •  Minimal: noir / blanc / rouge
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    BG:     str
    CARD:   str
    CARD2:  str
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
    BG     = "#0e0e0e",
    CARD   = "#161616",
    CARD2  = "#1c1c1c",
    SB     = "#111111",
    ACCENT = "#c0392b",
    RED    = "#c0392b",
    TEXT   = "#e8e8e8",
    DIMMED = "#666666",
    BORDER = "#2a2a2a",
    GREEN  = "#e8e8e8",   # on utilise blanc pour "bon"
    YELLOW = "#999999",   # gris moyen pour "moyen"
    SHADOW = "rgba(0,0,0,0.9)",
    GLOW   = "rgba(192,57,43,0.15)",
)

LIGHT = Theme(
    BG     = "#f5f5f5",
    CARD   = "#ffffff",
    CARD2  = "#f0f0f0",
    SB     = "#ebebeb",
    ACCENT = "#c0392b",
    RED    = "#c0392b",
    TEXT   = "#111111",
    DIMMED = "#777777",
    BORDER = "#dddddd",
    GREEN  = "#111111",
    YELLOW = "#555555",
    SHADOW = "rgba(0,0,0,0.1)",
    GLOW   = "rgba(192,57,43,0.10)",
)


def load_css(theme: str = "dark") -> str:
    t = LIGHT if theme == "light" else DARK

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, .stApp {{
    background-color: {t.BG} !important;
    color: {t.TEXT} !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
}}

.block-container {{
    padding: 1.2rem 2.5rem 3rem 2.5rem !important;
    max-width: 100% !important;
}}

.stDeployButton {{ display: none !important; }}
footer {{ visibility: hidden !important; }}
/* Header : on garde juste le fond transparent, on ne touche à rien d'autre */
header[data-testid="stHeader"] {{
    background-color : transparent !important;
    border-bottom    : none !important;
    box-shadow       : none !important;
}}

/* ══ SIDEBAR ════════════════════════════════════════════════ */
\*section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div:first-child {{
    background-color: {t.SB} !important;
    border-right: 1px solid {t.BORDER} !important;
}}*/

section[data-testid="stSidebar"] h3 {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.65rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: {t.DIMMED} !important;
    margin: 0.5rem 0 0.5rem !important;
    padding-bottom: 4px !important;
    border-bottom: 1px solid {t.BORDER} !important;
}}
section[data-testid="stSidebar"] hr {{
    border: none !important;
    border-top: 1px solid {t.BORDER} !important;
    margin: 0.6rem 0 !important;
}}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {{
    font-family: 'Share Tech Mono', monospace !important;
    color: {t.TEXT} !important;
    font-size: 0.82rem !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 2px !important;
    color: {t.TEXT} !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
}}
section[data-testid="stSidebar"] input[type="number"] {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 2px !important;
    color: {t.TEXT} !important;
    font-family: 'Share Tech Mono', monospace !important;
}}
section[data-testid="stSidebar"] [role="slider"] {{
    background-color: {t.ACCENT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stSliderTrackFill"] {{
    background-color: {t.ACCENT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stFileUploadDropzone"] {{
    background-color: {t.CARD} !important;
    border: 1px dashed {t.BORDER} !important;
    border-radius: 2px !important;
}}
section[data-testid="stSidebar"] [data-testid="stFileUploadDropzone"]:hover {{
    border-color: {t.ACCENT} !important;
}}

/* ══ RUN BUTTON ═════════════════════════════════════════════ */
section[data-testid="stSidebar"] .stButton > button {{
    width: 100% !important;
    background: {t.ACCENT} !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1rem !important;
    transition: opacity 0.15s !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    opacity: 0.85 !important;
}}

/* ══ MAIN BUTTONS ═══════════════════════════════════════════ */
.stButton > button {{
    background-color: transparent !important;
    color: {t.DIMMED} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 2px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    transition: all 0.15s !important;
}}
.stButton > button:hover {{
    border-color: {t.ACCENT} !important;
    color: {t.ACCENT} !important;
}}

/* ══ TABS ════════════════════════════════════════════════════ */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background-color: transparent !important;
    border-bottom: 1px solid {t.BORDER} !important;
    gap: 0 !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    background-color: transparent !important;
    color: {t.DIMMED} !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.4rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.15s !important;
    margin-bottom: -1px !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {t.TEXT} !important;
    border-bottom: 2px solid {t.ACCENT} !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{
    color: {t.TEXT} !important;
}}

/* ══ PROGRESS BAR ═══════════════════════════════════════════ */
.stProgress > div > div > div > div {{
    background: {t.ACCENT} !important;
}}

/* ══ EXPANDER ═══════════════════════════════════════════════ */
[data-testid="stExpander"] {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 2px !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
    color: {t.DIMMED} !important;
    letter-spacing: 0.1em !important;
}}

/* ══ DROPDOWN ════════════════════════════════════════════════ */
[data-baseweb="popover"] ul {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 2px !important;
}}
[data-baseweb="popover"] li {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
    color: {t.TEXT} !important;
}}
[data-baseweb="popover"] li:hover {{ background-color: {t.BORDER} !important; }}

/* ══ DATAFRAME ══════════════════════════════════════════════ */
.stDataFrame {{ border: 1px solid {t.BORDER} !important; border-radius: 2px !important; }}
[data-testid="stDataFrameResizable"] th {{
    background-color: {t.CARD2} !important;
    color: {t.ACCENT} !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}}

/* ══ CODE BLOCK ═════════════════════════════════════════════ */
.stCode, [data-testid="stCodeBlock"] {{
    background-color: {t.CARD} !important;
    border: 1px solid {t.BORDER} !important;
    border-radius: 2px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.78rem !important;
}}

/* ══ ALERT BOXES ════════════════════════════════════════════ */
[data-testid="stAlert"] {{
    border-radius: 2px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
}}

/* ══════════════════════════════════════════════════════════
   COMPOSANTS PERSONNALISES
══════════════════════════════════════════════════════════ */

/* ── Titre de section */
.sec-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {t.DIMMED};
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.4rem 0 0.9rem;
}}
.sec-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {t.BORDER};
}}

.ntd-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {t.DIMMED};
}}

/* ══ CARTE METRIQUE ═════════════════════════════════════════ */
.hud-card {{
    background: {t.CARD};
    border: 1px solid {t.BORDER};
    border-top: 2px solid {t.BORDER};
    border-radius: 2px;
    padding: 1.2rem 1.3rem 1.1rem;
    position: relative;
}}
.hud-card.c-red    {{ border-top-color: {t.RED};    }}
.hud-card.c-green  {{ border-top-color: {t.TEXT};   }}
.hud-card.c-yellow {{ border-top-color: {t.DIMMED}; }}
.hud-card.c-accent {{ border-top-color: {t.ACCENT}; }}

.hud-card-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {t.DIMMED};
    margin-bottom: 8px;
}}
.hud-card-value {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.9rem;
    font-weight: 400;
    color: {t.TEXT};
    letter-spacing: 0.02em;
    line-height: 1;
    margin-bottom: 10px;
}}
.hud-card-badge {{
    display: inline-block;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.1em;
    padding: 3px 8px;
    text-transform: uppercase;
    border-radius: 1px;
}}
.badge-g {{
    background: transparent;
    color: {t.TEXT};
    border: 1px solid {t.BORDER};
}}
.badge-y {{
    background: transparent;
    color: {t.DIMMED};
    border: 1px solid {t.BORDER};
}}
.badge-r {{
    background: {t.RED}18;
    color: {t.RED};
    border: 1px solid {t.RED}44;
}}

/* ══ GRILLE CONFUSION MATRIX ════════════════════════════════ */
.cm-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
}}
.cm-cell {{
    background: {t.CARD};
    border: 1px solid {t.BORDER};
    border-radius: 2px;
    padding: 1rem 0.8rem;
    text-align: center;
}}
.cm-cell.fn {{
    border-color: {t.RED}66;
    background: {t.RED}0a;
}}
.cm-num {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.5rem;
    font-weight: 400;
    line-height: 1;
    margin-bottom: 4px;
    color: {t.TEXT};
}}
.cm-num.danger {{ color: {t.RED}; }}
.cm-tag {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.56rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {t.DIMMED};
    margin-top: 3px;
}}
.cm-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {t.DIMMED};
}}

/* ══ ALERTE CRITIQUE ════════════════════════════════════════ */
.ntd-alert {{
    background: {t.CARD};
    border: 1px solid {t.BORDER};
    border-left: 3px solid {t.RED};
    border-radius: 0 2px 2px 0;
    padding: 0.9rem 1.2rem;
    margin-bottom: 1.4rem;
}}
.ntd-alert-title {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {t.RED};
    margin-bottom: 5px;
}}
.ntd-alert-body {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    color: {t.DIMMED};
    line-height: 1.6;
}}

/* ══ BARRE HORIZONTALE METRIQUE ════════════════════════════= */
.bar-section {{ margin-bottom: 1.4rem; }}
.bar-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 7px;
}}
.bar-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {t.DIMMED};
    width: 80px;
    text-align: right;
    flex-shrink: 0;
}}
.bar-track {{
    flex: 1;
    height: 12px;
    background: {t.CARD2};
    border: 1px solid {t.BORDER};
    border-radius: 1px;
    overflow: hidden;
}}
.bar-fill-bad     {{ height: 100%; background: {t.RED};    }}
.bar-fill-neutral {{ height: 100%; background: {t.TEXT};   }}
.bar-fill-dim     {{ height: 100%; background: {t.DIMMED}; }}
.bar-pct {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    color: {t.DIMMED};
    width: 46px;
    text-align: right;
    flex-shrink: 0;
}}

/* ══ MISS RATE BANNER ═══════════════════════════════════════ */
.miss-banner {{
    background: {t.RED}0d;
    border: 1px solid {t.RED}44;
    border-left: 3px solid {t.RED};
    border-radius: 0 2px 2px 0;
    padding: 1rem 1.2rem;
    margin-top: 10px;
    display: flex;
    align-items: baseline;
    gap: 14px;
}}
.miss-banner-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {t.DIMMED};
    flex-shrink: 0;
}}
.miss-banner-value {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 2rem;
    font-weight: 400;
    color: {t.RED};
    line-height: 1;
}}
.miss-banner-sub {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    color: {t.DIMMED};
}}

/* ══ STAT ROW ═══════════════════════════════════════════════ */
.stat-row {{
    display: flex;
    gap: 0;
    background: {t.CARD};
    border: 1px solid {t.BORDER};
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 1.2rem;
}}
.stat-cell {{
    flex: 1;
    padding: 1rem 1.1rem;
    border-right: 1px solid {t.BORDER};
}}
.stat-cell:last-child {{ border-right: none; }}
.stat-cell-label {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {t.DIMMED};
    margin-bottom: 5px;
}}
.stat-cell-value {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.2rem;
    color: {t.TEXT};
    line-height: 1;
}}
.stat-cell-sub {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem;
    color: {t.DIMMED};
    margin-top: 4px;
}}

/* ══ HISTORY ROW ════════════════════════════════════════════ */
.hist-row {{
    display: flex;
    align-items: center;
    gap: 16px;
    background: {t.CARD};
    border: 1px solid {t.BORDER};
    border-left: 2px solid {t.ACCENT};
    border-radius: 0 2px 2px 0;
    padding: 0.85rem 1.1rem;
    margin-bottom: 6px;
}}
.hist-model {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    color: {t.TEXT};
    text-transform: uppercase;
}}
.hist-ts {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem;
    color: {t.DIMMED};
    margin-top: 2px;
}}
.hist-score {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.9rem;
}}
.hist-key {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.56rem;
    color: {t.DIMMED};
    text-transform: uppercase;
    letter-spacing: 0.12em;
}}

/* ══ SPINNER ════════════════════════════════════════════════ */
@keyframes ntd-spin  {{ to {{ transform: rotate(360deg);  }} }}
@keyframes ntd-spinr {{ to {{ transform: rotate(-360deg); }} }}
@keyframes ntd-blink {{ 0%,49%{{ opacity:1; }} 50%,100%{{ opacity:0; }} }}
@keyframes ntd-dot   {{ 0%,80%,100%{{ transform:scale(.2);opacity:.15; }} 40%{{ transform:scale(1);opacity:1; }} }}

.ntd-spinner-wrap {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    padding: 2rem;
    background: {t.CARD};
    border: 1px solid {t.BORDER};
    border-radius: 2px;
    margin: 1rem 0;
}}
.ntd-rings {{ position: relative; width: 52px; height: 52px; }}
.ntd-ring-outer {{
    position: absolute; inset: 0;
    border: 1px solid {t.BORDER}; border-top-color: {t.ACCENT};
    border-radius: 50%;
    animation: ntd-spin .9s linear infinite;
}}
.ntd-ring-mid {{
    position: absolute; inset: 10px;
    border: 1px solid {t.BORDER}; border-right-color: {t.TEXT};
    border-radius: 50%;
    animation: ntd-spinr .65s linear infinite;
}}
.ntd-ring-inner {{
    position: absolute; inset: 20px;
    border: 1px solid {t.BORDER}; border-bottom-color: {t.DIMMED};
    border-radius: 50%;
    animation: ntd-spin .45s linear infinite;
}}
.ntd-spin-txt {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {t.ACCENT};
    animation: ntd-blink 1.1s step-end infinite;
}}
.ntd-dots {{ display: flex; gap: 5px; }}
.ntd-dot {{
    width: 5px; height: 5px; border-radius: 50%; background: {t.DIMMED};
    animation: ntd-dot 1.3s ease-in-out infinite;
}}
.ntd-dot.d2 {{ animation-delay: .15s; }}
.ntd-dot.d3 {{ animation-delay: .30s; }}

/* ══ EMPTY STATE ════════════════════════════════════════════ */
.ntd-empty {{ text-align: center; padding: 4rem 2rem; }}
.ntd-empty-icon {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: {t.BORDER};
}}
.ntd-empty-text {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {t.DIMMED};
}}

/* ══ SCROLLBAR ══════════════════════════════════════════════ */
::-webkit-scrollbar {{ width: 3px; height: 3px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {t.BORDER}; border-radius: 0; }}
::-webkit-scrollbar-thumb:hover {{ background: {t.DIMMED}; }}
</style>
"""