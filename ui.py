import streamlit as st

LEVEL_HEX = {"Normal": "#2ea043", "Low": "#d4a017", "Medium": "#f0883e",
             "High": "#f85149", "Critical": "#bc4cd6"}

_CSS = """
<style>
.stApp { background: linear-gradient(180deg, #F3F6FC 0%, #E4EBF7 100%); background-attachment: fixed; }
.block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1150px; }
footer { visibility: hidden; }

.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #10182B !important; }
.stApp p, .stApp li, .stApp label { color: #26314A !important; }
.stApp [data-testid="stCaptionContainer"] { color: #4A5670 !important; }

.hero { padding: 2.2rem 2.2rem; border-radius: 18px; margin-bottom: 1.6rem;
        background: linear-gradient(135deg, #0f2027 0%, #203a43 55%, #2c5364 100%);
        box-shadow: 0 6px 20px rgba(16,24,43,0.18); }
.hero, .hero h1, .hero p { color: #ffffff !important; }
.hero h1 { font-size: 2.1rem; margin: 0 0 0.6rem 0; line-height: 1.25; padding: 0; }
.hero p { font-size: 1.05rem; opacity: 0.92; margin: 0; }

.card { background: #ffffff; border: 1px solid #D5DEEE; border-radius: 14px;
        padding: 1.1rem 1.25rem; min-height: 165px; box-shadow: 0 2px 8px rgba(16,24,43,0.06); }
.card .ttl { font-size: 1.05rem; font-weight: 700; margin-bottom: 0.45rem; color: #10182B !important; }
.card .txt { font-size: 0.92rem; line-height: 1.5; color: #3A455E !important; }

.mcard { background: #ffffff; border: 1px solid #D5DEEE; border-radius: 14px;
         padding: 0.9rem 1.1rem; box-shadow: 0 2px 8px rgba(16,24,43,0.06); }
.mcard .lbl { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.6px; color: #5B6780 !important; }
.mcard .val { font-size: 1.7rem; font-weight: 800; margin-top: 0.15rem; color: #10182B !important; }
.mcard .sub { font-size: 0.78rem; color: #5B6780 !important; }

.banner { border-radius: 14px; padding: 1.1rem 1.5rem; margin-bottom: 1.1rem; }
.banner, .banner .lvl, .banner .sub { color: #ffffff !important; }
.banner .lvl { font-size: 1.7rem; font-weight: 800; letter-spacing: 0.5px; }
.banner .sub { font-size: 0.95rem; }

.badge { display: inline-block; padding: 0.3rem 0.85rem; border-radius: 999px;
         font-weight: 700; color: #ffffff !important; font-size: 0.85rem; }
         section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {
  color: #E6EDF5 !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
  color: #B8C5D6 !important;
}
section[data-testid="stSidebar"] {
  background-color: #0B1E33 !important;
}
section[data-testid="stSidebar"] * {
  color: #E6EDF5 !important;
}
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def show(html):
    st.markdown(html, unsafe_allow_html=True)


def hero(title, subtitle):
    show(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>')


def card(title, text):
    return f'<div class="card"><div class="ttl">{title}</div><div class="txt">{text}</div></div>'


def metric_card(label, value, sub=""):
    return (f'<div class="mcard"><div class="lbl">{label}</div>'
            f'<div class="val">{value}</div><div class="sub">{sub}</div></div>')


def badge(level):
    return f'<span class="badge" style="background:{LEVEL_HEX[level]}">{level}</span>'


def banner(level, title, subtitle=""):
    return (f'<div class="banner" style="background:{LEVEL_HEX[level]}">'
            f'<div class="lvl">{title}</div><div class="sub">{subtitle}</div></div>')
import plotly.graph_objects as go


def gauge_fig(level, score):
    pct = max(0, min(100, score * 100))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 28, "color": LEVEL_HEX.get(level, "#0F172A")}},
        gauge={
            "axis": {"range": [0, 100], "visible": False},
            "bar": {"color": LEVEL_HEX.get(level, "#0F172A"), "thickness": 0.28},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 20], "color": "#E8F5EE"},
                {"range": [20, 40], "color": "#FBF2DD"},
                {"range": [40, 60], "color": "#FCEADD"},
                {"range": [60, 80], "color": "#FBE3E3"},
                {"range": [80, 100], "color": "#F2E3F8"},
            ],
        },
    ))
    fig.update_layout(height=190, margin=dict(l=15, r=15, t=15, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def stat_card(icon, label, value, sub="", trend=None, trend_up=True):
    trend_html = ""
    if trend is not None:
        c = "#2E8B57" if trend_up else "#D64545"
        arrow = "↑" if trend_up else "↓"
        trend_html = (f'<span style="background:{c}22;color:{c};font-weight:700;font-size:0.75rem;'
                      f'padding:0.15rem 0.5rem;border-radius:999px;margin-left:0.5rem;">{arrow} {trend}</span>')
    return (f'<div class="mcard"><div style="display:flex;align-items:center;gap:0.5rem;">'
            f'<span style="font-size:1.25rem;">{icon}</span><div class="lbl" style="margin:0;">{label}</div></div>'
            f'<div style="display:flex;align-items:baseline;margin-top:0.3rem;">'
            f'<div class="val">{value}</div>{trend_html}</div><div class="sub">{sub}</div></div>')


def alert_row(level, title, time_str, desc, thumb=None):
    img = (f'<img src="{thumb}" style="width:64px;height:48px;object-fit:cover;border-radius:8px;margin-right:12px;">'
          if thumb else
          '<div style="width:64px;height:48px;border-radius:8px;background:#E3E8F0;margin-right:12px;"></div>')
    return (f'<div style="display:flex;align-items:center;padding:0.7rem 0;border-bottom:1px solid #E3E8F0;">'
            f'{img}<div style="flex:1;"><div style="font-weight:700;color:{LEVEL_HEX.get(level, "#0F172A")};">{title}</div>'
            f'<div style="font-size:0.82rem;color:#5B6B85;">{time_str} &nbsp;·&nbsp; {desc}</div></div>'
            f'{badge(level)}</div>')