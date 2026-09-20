import streamlit as st

LEVEL_HEX = {"Normal": "#157e28", "Low": "#d4a017", "Medium": "#f0883e",
             "High": "#f85149", "Critical": "#bc4cd6"}

_CSS = """
<style>
.stApp { background: radial-gradient(1200px 600px at 15% -10%, #1b2a4a 0%, rgba(11,15,25,0) 60%),
                     radial-gradient(900px 500px at 100% 0%, #123c3a 0%, rgba(11,15,25,0) 55%),
                     #0B0F19;
         background-attachment: fixed; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1150px; }
footer { visibility: hidden; }
.hero { padding: 2.2rem 2.2rem; border-radius: 18px; margin-bottom: 1.6rem;
        background: linear-gradient(135deg, #0f2027 0%, #203a43 55%, #2c5364 100%);
        border: 1px solid rgba(255,255,255,0.08); }
.hero, .hero h1, .hero p { color: #ffffff !important; }
.hero h1 { font-size: 2.1rem; margin: 0 0 0.6rem 0; line-height: 1.25; padding: 0; }
.hero p { font-size: 1.05rem; opacity: 0.9; margin: 0; }
.card { background: #161B26; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
        padding: 1.1rem 1.25rem; min-height: 165px; }
.card .ttl { font-size: 1.05rem; font-weight: 700; margin-bottom: 0.45rem; color: #ffffff !important; }
.card .txt { font-size: 0.92rem; line-height: 1.5; color: #C9D1E0 !important; }
.mcard { background: #161B26; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
         padding: 0.9rem 1.1rem; }
.mcard .lbl { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.6px; color: #9AA6BD !important; }
.mcard .val { font-size: 1.7rem; font-weight: 800; margin-top: 0.15rem; color: #ffffff !important; }
.mcard .sub { font-size: 0.78rem; color: #9AA6BD !important; }
.banner { border-radius: 14px; padding: 1.1rem 1.5rem; margin-bottom: 1.1rem; }
.banner, .banner .lvl, .banner .sub { color: #ffffff !important; }
.banner .lvl { font-size: 1.7rem; font-weight: 800; letter-spacing: 0.5px; }
.banner .sub { font-size: 0.95rem; }
.badge { display: inline-block; padding: 0.3rem 0.85rem; border-radius: 999px;
         font-weight: 700; color: #ffffff !important; font-size: 0.85rem; }
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