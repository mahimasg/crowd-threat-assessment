import os
import streamlit as st
import ui

st.set_page_config(page_title="Crowd Threat Assessment", page_icon="🛡️", layout="wide")
ui.inject_css()

pages = [st.Page("views/home.py", title="Home", icon="🏠", default=True)]
if os.name == "nt":          # Windows laptop-la mattum Live Monitor
    pages.append(st.Page("views/live.py", title="Live Monitor", icon="📡"))
pages += [
    st.Page("views/analyze.py", title="Analyze Video", icon="🎥"),
    st.Page("views/results.py", title="Results Dashboard", icon="📊"),
    st.Page("views/about.py", title="System & Performance", icon="🧠"),
]
try:
    nav = st.navigation(pages, position="top")
except TypeError:
    nav = st.navigation(pages)
nav.run()