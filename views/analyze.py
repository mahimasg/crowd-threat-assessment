import os
import tempfile
import streamlit as st
import core

st.title("Analyze Video")

if not core.files_ready():
    st.error("models/cnn_lstm.pt illa models/threat_config.json illa. "
             "train_lstm.py and threat_score.py mudhal run pannunga.")
    st.stop()
cfg = core.get_cfg()

left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("1. Upload CCTV video")
    up = st.file_uploader("Video file", type=["mp4", "avi", "mov", "mkv"],
                          label_visibility="collapsed")
    if up is not None:
        st.caption(f"{up.name}  |  {up.size / 1e6:.1f} MB")
with right:
    st.subheader("2. Settings")
    zone_name = st.selectbox("Camera zone risk", list(core.ZONES))
    zone_w = core.ZONES[zone_name]
    thresh = st.slider("Abnormal threshold", 0.05, 0.95, float(cfg["THRESH"]), 0.01)
    max_sec = st.slider("Max seconds to analyze", 10, 120, 30, 5)
    st.caption(f"Running on: {core.device}")

st.divider()
run = st.button("Analyze video", type="primary", disabled=up is None, use_container_width=True)

if run and up is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(up.name)[1]) as tmp:
        tmp.write(up.read())
        src = tmp.name
    bar = st.progress(0.0, text="Starting...")
    try:
        res = core.analyze(src, zone_w, thresh, max_sec,
                           lambda f, t: bar.progress(min(f, 1.0), text=t))
    finally:
        os.remove(src)
    if res is None:
        bar.empty()
        st.error("Video romba short. Kuraindha 3-4 seconds venum.")
    else:
        res["meta"] = {"file": up.name, "zone": zone_name, "threshold": thresh}
        st.session_state["res"] = res
        st.switch_page("views/results.py")