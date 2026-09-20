import os
import time
from collections import deque
import cv2
import pandas as pd
import streamlit as st
import core
import ui

st.title("Live CCTV Monitor")

if not core.files_ready():
    st.error("models/cnn_lstm.pt illa models/threat_config.json illa. "
             "train_lstm.py and threat_score.py mudhal run pannunga.")
    st.stop()
cfg = core.get_cfg()

ctrl, view = st.columns([2, 3], gap="large")

with ctrl:
    st.subheader("Camera source")
    kind = st.radio("Source", ["Webcam (this laptop)",
                               "IP camera / RTSP / phone camera URL",
                               "Simulated CCTV (video file)"],
                    label_visibility="collapsed")
    if kind.startswith("Webcam"):
        source = int(st.number_input("Webcam index", 0, 5, 0))
    elif kind.startswith("IP"):
        source = st.text_input("Stream URL", placeholder="rtsp://user:pass@192.168.1.10:554/stream")
    else:
        source = st.text_input("Video file path", value=r"C:\shanghaitech\sample_videos\01_0135.mp4")
    zone_name = st.selectbox("Camera zone risk", list(core.ZONES))
    thresh = st.slider("Abnormal threshold", 0.05, 0.95, float(cfg["THRESH"]), 0.01)
    show_boxes = st.checkbox("Show person boxes (slower)", value=True)
    on = st.toggle("Start monitoring")
    st.caption("Stop panna toggle-ah off pannunga.")

with view:
    banner_ph = st.empty()
    video_ph = st.empty()
    stats_ph = st.empty()

st.subheader("Live threat timeline")
chart_ph = st.empty()
st.subheader("Alert log")
log_ph = st.empty()

if not on:
    banner_ph.info("Monitoring off. Select source and toggle **Start monitoring**.")
    st.stop()

if source == "" or source is None:
    st.warning("Stream URL / file path kudunga.")
    st.stop()
if isinstance(source, str) and kind.startswith("Simulated") and not os.path.exists(source):
    st.error("Antha video file illa. Path-ah check pannunga.")
    st.stop()

cnn, lstm, yolo = core.load_models()
cap = core.open_capture(source)
if not cap.isOpened():
    st.error("Camera / stream open aagala. Source-ah check pannunga.")
    st.stop()

is_file = kind.startswith("Simulated")
src_fps = cap.get(cv2.CAP_PROP_FPS) or 24
step = max(1, int(round(src_fps / core.TARGET_FPS))) if is_file else 1
interval = 1.0 / core.TARGET_FPS
zone_w = core.ZONES[zone_name]

INIT = {"conf": 0.0, "flag": False, "run": 0, "score": 0.0, "level": "Normal"}
state = dict(INIT)
feats = deque(maxlen=core.CLIP_LEN)
history = deque(maxlen=120)
alerts = []
n_sampled, frame_no, n_clips = 0, 0, 0
last_t = 0.0
proc = deque(maxlen=20)

try:
    while True:
        ok, bgr = cap.read()
        if not ok:
            if is_file:                       # video mudinja marubadi mudhal-la irundhu
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                feats.clear()
                state = dict(INIT)
                n_sampled, frame_no = 0, 0
                continue
            st.warning("Stream nindru pochu.")
            break

        frame_no += 1
        if is_file:
            if frame_no % step:
                continue
        else:
            now = time.time()
            if now - last_t < interval:
                continue
            last_t = now

        tic = time.time()
        rgb = core.prep_frame(bgr)
        feats.append(core.frame_feature(cnn, rgb))
        n_sampled += 1
        boxes = core.yolo_boxes(yolo, rgb) if show_boxes else []

        if len(feats) == core.CLIP_LEN and (n_sampled - core.CLIP_LEN) % core.STRIDE == 0:
            prob = core.clip_prob(lstm, list(feats))
            state = core.threat_step(prob, state["run"], zone_w, thresh)
            n_clips += 1
            history.append({"abnormal confidence": state["conf"], "threat score": state["score"]})
            chart_ph.line_chart(pd.DataFrame(list(history)))
            if state["flag"]:
                alerts.append({"Time": time.strftime("%H:%M:%S"), "Level": state["level"],
                               "Score": round(state["score"], 2),
                               "Confidence": round(state["conf"], 2),
                               "Persistence": state["run"]})
                log_ph.dataframe(pd.DataFrame(alerts[-10:][::-1]), hide_index=True)
            lvl = state["level"]
            if lvl == "Normal":
                banner_ph.markdown(ui.banner("Normal", "NORMAL", "No threat detected"),
                                   unsafe_allow_html=True)
            else:
                banner_ph.markdown(
                    ui.banner(lvl, f"THREAT: {lvl.upper()}",
                              f"score {state['score']:.2f}  |  confidence {state['conf']:.2f}  |  "
                              f"persistence {state['run']} clips"),
                    unsafe_allow_html=True)

        video_ph.image(core.annotate(rgb, boxes, state), channels="RGB")
        proc.append(time.time() - tic)
        fps = len(proc) / max(sum(proc), 1e-6)
        note = "" if fps >= 5 else "  |  processing slow, boxes off panni try pannunga"
        stats_ph.caption(f"Speed: {fps:.1f} fps  |  persons: {len(boxes)}  |  "
                         f"clips analyzed: {n_clips}{note}")
finally:
    cap.release()