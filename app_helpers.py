# ══════════════════════════════════════════════════════════════
#   app_helpers.py — Fonctions utilitaires partagées
# ══════════════════════════════════════════════════════════════


def hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    """Convertit une couleur hex en rgba()."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def score_cls(v: float) -> str:
    """Retourne la classe CSS selon le score : g / y / r."""
    return "g" if v >= 0.95 else "y" if v >= 0.85 else "r"


def score_color(v: float, T=None) -> str:
    """Retourne la couleur hex selon le score."""
    if T is None:
        from app_init import get_theme
        T = get_theme()
    return T.GREEN if v >= 0.95 else T.YELLOW if v >= 0.85 else T.RED


def hud_card(label: str, value: float, color_cls: str) -> str:
    """Génère le HTML d'une carte métrique HUD."""
    c   = score_cls(value)
    lbl = {"g": "EXCELLENT", "y": "GOOD", "r": "LOW"}[c]
    return f"""
<div class="hud-card {color_cls}">
  <div class="hud-card-label">{label}</div>
  <div class="hud-card-value">{value:.4f}</div>
  <span class="hud-card-badge badge-{c}">{lbl}</span>
</div>"""


def bar_row(label: str, value: float, low: bool = True) -> str:
    """Génère une barre horizontale de métrique."""
    from app_init import get_theme
    T   = get_theme()
    pct = round(value * 100, 2)
    cls = "bar-fill-bad" if (low and value < 0.85) else "bar-fill-neutral"
    return (
        f'<div class="bar-row">'
        f'<div class="bar-label">{label}</div>'
        f'<div class="bar-track"><div class="{cls}" style="width:{pct}%"></div></div>'
        f'<div class="bar-pct">{pct:.1f}%</div>'
        f'</div>'
    )