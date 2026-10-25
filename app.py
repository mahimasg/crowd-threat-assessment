import streamlit as st
import alerting
import ui

st.set_page_config(page_title="Crowd Threat Assessment", page_icon="🛡️", layout="wide")
ui.inject_css()

st.sidebar.markdown(
    '<div style="display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0 1.2rem 0;">'
    '<span style="font-size:1.6rem;">🛡️</span>'
    '<div style="font-family:\'Lora\',serif;font-weight:700;font-size:1.05rem;color:#FFFFFF;">'
    'Crowd Threat<br>Assessment</div></div>', unsafe_allow_html=True)

pages = [
    st.Page("views/home.py", title="Dashboard", icon="🏠", default=True),
    st.Page("views/live.py", title="Live Monitoring", icon="📡"),
    st.Page("views/analyze.py", title="Video Analysis", icon="🎥"),
    st.Page("views/results.py", title="Alert History", icon="🔔"),
]
nav = st.navigation(pages)

st.sidebar.markdown("---")
tg_status, tg_color = alerting.status_text()
st.sidebar.markdown(
    f'<div style="padding:0.8rem;background:rgba(255,255,255,0.06);border-radius:10px;">'
    f'<div style="font-weight:700;color:#FFFFFF;">📨 Telegram Alerts</div>'
    f'<div style="color:{tg_color};font-weight:700;font-size:0.85rem;">● {tg_status}</div></div>',
    unsafe_allow_html=True)

nav.run()