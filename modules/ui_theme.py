"""BizAdvisor AI design system.

Public API
----------
render_header()          -> call once in app.py (theme + sidebar logo).
inject_theme()           -> CSS only.
get_chart_colors()       -> chart palette (list of hex).
style_figure(fig, ...)   -> apply theme + palette to a Plotly figure.
priority_badge(priority) -> accessible HTML badge (High/Medium/Low).
recommendation_card(...) -> boxed recommendation card (HTML).
empty_state(title, msg)  -> consistent "no data yet" panel.
page_title(title, desc)  -> consistent page heading.

Everything is local: no external fonts, images or scripts.
"""

from __future__ import annotations

import base64
import html

import streamlit as st

# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------
COLORS = {
    "ivory": "#FAF8F3",
    "beige": "#E9DFD0",
    "sand": "#D0BFA8",
    "brown": "#513D32",
    "terracotta": "#B87558",
    "olive": "#6F8060",
    "muted": "#6B6058",
    "white": "#FFFFFF",
    "border": "#D6C9B8",
}

CHART_COLORS = [
    "#513D32", "#B87558", "#6F8060",
    "#A47C65", "#8A9A77", "#D0A17D",
]

LINE_DASHES = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]
MARKER_SYMBOLS = ["circle", "square", "diamond", "triangle-up", "x", "cross"]

PRIORITY_BADGES = {
    # symbol is part of the text so status never depends on colour alone
    "high": ("▲", "High", "#8C2F1B", "#FBE9E4"),
    "medium": ("◆", "Medium", "#7A5200", "#FBF0D5"),
    "low": ("●", "Low", "#3F5A33", "#E6EFDD"),
}

# Logo is embedded in the code, so no image file is needed.
_LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 262 56" '
    'width="262" height="56">'
    '<rect x="0" y="4" width="48" height="48" rx="10" fill="#513D32"/>'
    '<rect x="10" y="31" width="6" height="12" rx="1" fill="#E9DFD0"/>'
    '<rect x="21" y="24" width="6" height="19" rx="1" fill="#D0BFA8"/>'
    '<rect x="32" y="17" width="6" height="26" rx="1" fill="#FAF8F3"/>'
    '<path d="M9 26 L20 18 L27 21 L39 11" fill="none" stroke="#B87558" '
    'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="39" cy="11" r="3" fill="#B87558"/>'
    '<text x="58" y="28" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
    'font-size="24" font-weight="800" fill="#513D32">BizAdvisor '
    '<tspan fill="#B87558">AI</tspan></text>'
    '<text x="58" y="46" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
    'font-size="12.5" fill="#6B6058">Your business. Better decisions.</text>'
    "</svg>"
)
_LOGO_B64 = base64.b64encode(_LOGO_SVG.encode("utf-8")).decode("ascii")


def get_chart_colors() -> list[str]:
    """Return the chart colour palette."""
    return CHART_COLORS


# --------------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------------
_CSS = """
<style>
:root { color-scheme: light; }

.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #FAF8F3 !important;
    color: #2B211B;
}
[data-testid="stHeader"] { background: #FAF8F3 !important; }
.block-container { padding-top: 1.2rem; max-width: 1280px; }

h1, h2, h3, h4, h5, h6 { color: #513D32; }
h1 { font-weight: 750; letter-spacing: -0.5px; }
h2, h3 { font-weight: 700; }
p, li, label, .stMarkdown { color: #2B211B; }
[data-testid="stCaptionContainer"] { color: #6B6058; }

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: #F1E9DE !important;
    border-right: 1px solid #D6C9B8;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #2B211B; }
[data-testid="stSidebarNav"] a { border-radius: 8px; }
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: rgba(81, 61, 50, 0.12); font-weight: 700; }

/* ---- Metrics, alerts, containers ---- */
[data-testid="stMetric"] {
    background: #F1E9DE; border: 1px solid #D6C9B8;
    border-radius: 10px; padding: 14px 16px; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
    color: #6B6058 !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    color: #2B211B !important; font-weight: 750; }
[data-testid="stAlert"] { border-radius: 12px; border: 1px solid transparent; }
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #D6C9B8; border-radius: 10px; }

/* ---- Buttons ---- */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    min-height: 42px; border-radius: 8px; border: 1px solid #D6C9B8;
    font-weight: 650; background: #FFFFFF; color: #2B211B; }
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: #B87558; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: #513D32; border-color: #513D32; color: #FFFFFF; }
.stButton > button[kind="primary"] *, .stFormSubmitButton > button[kind="primary"] * {
    color: #FFFFFF !important; }

/* ---- Forms ---- */
input, textarea { color: #2B211B !important; background: #FFFFFF !important; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"] {
    background: #FFFFFF !important; border-color: #B9A993 !important;
    border-radius: 8px !important; }
[data-baseweb="select"] * { color: #211A16 !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li {
    background: #FFFFFF !important; color: #211A16 !important; }

/* ---- Tables ---- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid #D6C9B8; border-radius: 8px; overflow: hidden; }

/* ---- Links, focus, separators ---- */
a { color: #81472F; text-underline-offset: 3px; }
button:focus-visible, input:focus-visible, textarea:focus-visible,
a:focus-visible, [role="tab"]:focus-visible,
[data-baseweb="select"]:focus-within {
    outline: 3px solid #B87558 !important; outline-offset: 2px !important; }
hr { border-color: #D6C9B8 !important; }

/* ---- Badges & empty states ---- */
.ba-badge {
    display: inline-flex; align-items: center; gap: 6px; font-weight: 700;
    font-size: 0.85rem; padding: 2px 10px; border-radius: 6px;
    border: 1.5px solid; }
.ba-empty {
    border: 1.5px dashed #D6C9B8; border-radius: 10px;
    padding: 1.4rem; background: #F1E9DE; }
.ba-empty strong { color: #513D32; display: block; margin-bottom: 4px; }
.ba-page-desc { color: #6B6058; margin-top: -0.4rem; margin-bottom: 1rem; }

/* ---- Recommendation cards ---- */
.ba-card {
    background: #FFFFFF;
    border: 1px solid #D6C9B8;
    border-left: 6px solid #B87558;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 2px rgba(81, 61, 50, 0.08);
}
.ba-card-high { border-left-color: #8C2F1B; }
.ba-card-medium { border-left-color: #B7791F; }
.ba-card-low { border-left-color: #3F5A33; }
.ba-card-title { font-size: 1.1rem; font-weight: 700; color: #513D32; margin: 10px 0 2px; }
.ba-card-meta { font-size: 0.85rem; color: #6B6058; margin-bottom: 10px; }
.ba-card-body { color: #2B211B; margin-bottom: 10px; line-height: 1.5; }
.ba-card-action {
    background: #F1E9DE;
    border-radius: 8px;
    padding: 10px 12px;
    color: #2B211B;
    line-height: 1.5;
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
        scroll-behavior: auto !important; }
}
</style>
"""


def inject_theme() -> None:
    """Inject the global stylesheet. Safe to call on every run."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header() -> None:
    """Theme + a logo pinned to the top of the sidebar on every page.

    Call once in app.py after st.set_page_config() and before
    st.navigation(). app.py is the entrypoint for every page, so this
    applies to all pages.
    """
    inject_theme()
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebarHeader"] {{
            min-height: 5rem;
            background: url("data:image/svg+xml;base64,{_LOGO_B64}")
                no-repeat 1.25rem center / 225px auto;
            border-bottom: 1px solid #D6C9B8;
            margin-bottom: 0.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Page building blocks
# --------------------------------------------------------------------------
def page_title(title: str, description: str = "") -> None:
    st.title(title)
    if description:
        st.markdown(
            f'<p class="ba-page-desc">{html.escape(description)}</p>',
            unsafe_allow_html=True,
        )


def empty_state(title: str, message: str) -> None:
    st.markdown(
        f'<div class="ba-empty"><strong>{html.escape(title)}</strong>'
        f"{html.escape(message)}</div>",
        unsafe_allow_html=True,
    )


def priority_badge(priority: str) -> str:
    """HTML badge with symbol + text + border (not colour alone).

    Render with st.markdown(..., unsafe_allow_html=True).
    """
    key = str(priority).strip().lower()
    symbol, label, fg, bg = PRIORITY_BADGES.get(
        key, ("○", str(priority).title() or "Info", "#2B211B", "#EFE8DD")
    )
    return (
        f'<span class="ba-badge" style="color:{fg};background:{bg};'
        f'border-color:{fg}"><span aria-hidden="true">{symbol}</span>'
        f"{html.escape(label)} priority</span>"
    )


def recommendation_card(priority: str, title: str, category: str,
                        message: str, action: str = "") -> str:
    """Boxed recommendation card.

    Render with st.markdown(..., unsafe_allow_html=True).
    """
    level = str(priority).strip().lower()
    if level not in PRIORITY_BADGES:
        level = "low"
    action_html = (
        f'<div class="ba-card-action"><strong>Suggested next step:</strong> '
        f"{html.escape(str(action))}</div>"
        if action
        else ""
    )
    return (
        f'<div class="ba-card ba-card-{level}">'
        f"{priority_badge(priority)}"
        f'<div class="ba-card-title">{html.escape(str(title))}</div>'
        f'<div class="ba-card-meta">Category: {html.escape(str(category))}</div>'
        f'<div class="ba-card-body">{html.escape(str(message))}</div>'
        f"{action_html}"
        f"</div>"
    )


# --------------------------------------------------------------------------
# Plotly helper
# --------------------------------------------------------------------------
def style_figure(fig, title: str | None = None, height: int | None = 380,
                 vary_bar_colors: bool = True):
    """Explicitly theme a Plotly figure. Call on every figure before
    st.plotly_chart.

    Global CSS does not restyle Plotly, so everything is set here:
    backgrounds, fonts, axes, gridlines, legend, hover labels, palette, and
    non-colour cues (dash styles + marker shapes on line charts).
    """
    colors = get_chart_colors()
    text = "#2B211B"
    grid = "#E3D9CB"
    axis_line = "#B9A993"
    paper = "#FFFFFF"

    has_title = bool(title or fig.layout.title.text)

    fig.update_layout(
        paper_bgcolor=paper,
        plot_bgcolor=paper,
        colorway=colors,
        font=dict(color=text, size=12,
                  family="Segoe UI, Helvetica, Arial, sans-serif"),
        margin=dict(l=56, r=24, t=56 if has_title else 24, b=56),
        legend=dict(font=dict(color=text), bgcolor="rgba(255,255,255,0.9)",
                    bordercolor=axis_line, borderwidth=1),
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(color=text),
                        bordercolor=axis_line),
    )
    if title:
        fig.update_layout(title=dict(text=title, font=dict(color=text, size=16)))
    elif fig.layout.title.text:
        fig.update_layout(title_font=dict(color=text, size=16))
    if height:
        fig.update_layout(height=height)

    axis = dict(gridcolor=grid, gridwidth=1, showgrid=True, zeroline=False,
                linecolor=axis_line, linewidth=1, ticks="outside",
                tickfont=dict(color=text), title_font=dict(color=text))
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)

    for i, trace in enumerate(fig.data):
        colour = colors[i % len(colors)]
        ttype = trace.type
        if ttype == "scatter":
            mode = getattr(trace, "mode", None) or "lines"
            trace.update(line=dict(color=colour, width=2.5,
                                   dash=LINE_DASHES[i % len(LINE_DASHES)]))
            if "markers" in mode or mode == "lines":
                trace.update(
                    mode="lines+markers",
                    marker=dict(
                        color=colour, size=8,
                        symbol=MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)],
                        line=dict(color="#FFFFFF", width=1),
                    ),
                )
        elif ttype == "bar":
            n = len(trace.x) if trace.x is not None else 0
            single = len(fig.data) == 1
            marker_colour = (
                [colors[j % len(colors)] for j in range(n)]
                if (single and vary_bar_colors and n > 1)
                else colour
            )
            trace.update(marker=dict(color=marker_colour,
                                     line=dict(color=axis_line, width=0.5)))
        elif ttype == "pie":
            n = len(trace.labels) if trace.labels is not None else 0
            trace.update(
                marker=dict(colors=[colors[j % len(colors)] for j in range(n)],
                            line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent",
                textfont=dict(color=text),
                insidetextorientation="radial",
            )
    return fig