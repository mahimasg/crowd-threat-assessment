import os
import time
import base64
from collections import deque
import cv2
import pandas as pd
import streamlit as st
import alerting
import core
import ui

st.markdown(
    '<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">'
    '<div><h1 style="margin-bottom:0.2rem;">Welcome Back!</h1>'
    '<p style="color:#5B6B85;margin:0;">Real-time crowd monitoring and threat assessment using AI</p></div>'
    f'<div style="background:#fff;border:1px solid #E3E8F0;border-radius:12px;padding:0.6rem 1rem;font-weight:600;">'
    f'📅 {time.strftime("%b %d, %Y")}<br><span style="color:#5B6B85;font-weight:500;">{time.strftime("%I:%M %p")}</span></div>'
    '</div>', unsafe_allow_html=True)
st.write("")

if not core.files_ready():
    st.error("Model files missing. Run train_lstm.py and threat_score.py first.")
    st.stop()
cfg = core.get_cfg()

if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "alerts_history" not in st.session_state:
    st.session_state.alerts_history = []
if "prev_people" not in st.session_state:
    st.session_state.prev_people = 0

s1, s2, s3, s4 = st.columns(4)
people_ph, level_ph, status_ph, tg_ph = s1.empty(), s2.empty(), s3.empty(), s4.empty()


def render_top_cards(people=0, level="Normal", score=0.0, monitoring=False):
    trend = people - st.session_state.prev_people
    people_ph.markdown(ui.stat_card("👥", "People Detected", people, "Live count",
                                    trend=abs(trend) if trend != 0 else None, trend_up=trend >= 0),
                       unsafe_allow_html=True)
    level_ph.markdown(ui.stat_card("⚠️", "Current Threat Level", level, f"score {score:.2f}"),
                      unsafe_allow_html=True)
    status_ph.markdown(ui.stat_card("🛡️", "System Status",
                                    "Monitoring" if monitoring else "Idle",
                                    "All systems active" if monitoring else "Start monitoring below"),
                       unsafe_allow_html=True)
    tg_status, _ = alerting.status_text()
    last = st.session_state.alerts_history[-1]["Time"] if st.session_state.alerts_history else "—"
    tg_ph.markdown(ui.stat_card("🔔", "Telegram Alerts", tg_status, f"Last alert: {last}"),
                   unsafe_allow_html=True)


render_top_cards(monitoring=st.session_state.monitoring)
st.write("")

left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown("#### 📹 Live Monitoring")
    video_ph = st.empty()
    ctrl_row = st.columns([2, 2, 1])
    btn_label = "⏹ Stop Monitoring" if st.session_state.monitoring else "▶ Start Monitoring"
    if ctrl_row[0].button(btn_label, use_container_width=True, type="primary"):
        st.session_state.monitoring = not st.session_state.monitoring
        st.rerun()
    kind = ctrl_row[1].selectbox("Camera", ["Webcam (this laptop)",
                                            "IP camera / RTSP / phone camera URL",
                                            "Simulated CCTV (video file)"],
                                 label_visibility="collapsed")
    with ctrl_row[2].popover("⚙️"):
        if kind.startswith("Webcam"):
            source = int(st.number_input("Webcam index", 0, 5, 0))
        elif kind.startswith("IP"):
            source = st.text_input("Stream URL", placeholder="rtsp://user:pass@192.168.1.10:554/stream")
        else:
            source = st.text_input("Video file path", value=r"C:\shanghaitech\sample_videos\01_0135.mp4")
        zone_name = st.selectbox("Camera zone risk", list(core.ZONES))
        thresh = st.slider("Abnormal threshold", 0.05, 0.95, float(cfg["THRESH"]), 0.01)
        show_boxes = st.checkbox("Show person boxes", value=True)

with right:
    st.markdown("#### 🛡️ Threat Assessment")
    gauge_ph = st.empty()
    legend_html = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:0.15rem 0;font-size:0.82rem;">'
        f'<span style="color:{ui.LEVEL_HEX[l]};font-weight:700;">● {l}</span><span style="color:#5B6B85;">{r}</span></div>'
        for l, r in [("Normal", "0 – 20%"), ("Low", "21 – 40%"), ("Medium", "41 – 60%"),
                    ("High", "61 – 80%"), ("Critical", "81 – 100%")])
    st.markdown(legend_html, unsafe_allow_html=True)
    msg_ph = st.empty()
    mini1, mini2 = st.columns(2)
    people_mini_ph, score_mini_ph = mini1.empty(), mini2.empty()

st.write("")
st.markdown("#### 🔔 Recent Alerts")
alerts_ph = st.empty()


def render_alerts():
    rows = st.session_state.alerts_history[-3:][::-1]
    if not rows:
        alerts_ph.caption("No alerts yet.")
        return
    html = "".join(ui.alert_row(r["Level"], f"{r['Level']} Threat Detected", r["Time"], r["Desc"], r.get("Thumb"))
                   for r in rows)
    alerts_ph.markdown(html, unsafe_allow_html=True)


render_alerts()
st.write("")
st.markdown("#### 📈 Threat Trend (This Session)")
trend_ph = st.empty()

LEVEL_MSG = {
    "Normal": "Situation is normal. No suspicious activity detected.",
    "Low": "Minor deviation noticed. Monitoring continues.",
    "Medium": "Crowd movement anomaly detected.",
    "High": "Aggressive or unusual behavior detected.",
    "Critical": "Immediate attention required.",
}


def thumb_b64(bgr):
    small = cv2.resize(bgr, (96, 72))
    ok, buf = cv2.imencode(".jpg", small)
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode() if ok else None


if not st.session_state.monitoring:
    gauge_ph.plotly_chart(ui.gauge_fig("Normal", 0.0), use_container_width=True, config={"displayModeBar": False})
    msg_ph.caption(LEVEL_MSG["Normal"])
    people_mini_ph.markdown(ui.metric_card("People in Frame", "0"), unsafe_allow_html=True)
    score_mini_ph.markdown(ui.metric_card("Threat Score", "0.00"), unsafe_allow_html=True)
    video_ph.info("Monitoring stopped. Click **Start Monitoring** to begin.")
    st.stop()

if kind.startswith("Simulated") and (not source or not os.path.exists(source)):
    st.error("Video file not found. Check the path in settings (⚙️).")
    st.session_state.monitoring = False
    st.stop()

cnn, lstm, yolo = core.load_models()
cap = core.open_capture(source)
if not cap.isOpened():
    st.error("Could not open camera/stream.")
    st.session_state.monitoring = False
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
n_sampled, frame_no, last_t = 0, 0, 0.0

try:
    while True:
        ok, bgr = cap.read()
        if not ok:
            if is_file:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                feats.clear(); state = dict(INIT); n_sampled, frame_no = 0, 0
                continue
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

        rgb = core.prep_frame(bgr)
        feats.append(core.frame_feature(cnn, rgb))
        n_sampled += 1
        boxes = core.yolo_boxes(yolo, rgb) if show_boxes else []

        if len(feats) == core.CLIP_LEN and (n_sampled - core.CLIP_LEN) % core.STRIDE == 0:
            prob = core.clip_prob(lstm, list(feats))
            state = core.threat_step(prob, state["run"], zone_w, thresh)
            history.append(state["score"])

            if state["flag"]:
                alerting.send_alert(bgr, state["level"], state["score"])
                st.session_state.alerts_history.append({
                    "Time": time.strftime("%I:%M %p"), "Level": state["level"],
                    "Desc": LEVEL_MSG[state["level"]], "Thumb": thumb_b64(bgr),
                })
                render_alerts()

            render_top_cards(len(boxes), state["level"], state["score"], True)
            gauge_ph.plotly_chart(ui.gauge_fig(state["level"], state["score"]),
                                  use_container_width=True, config={"displayModeBar": False})
            msg_ph.caption(LEVEL_MSG[state["level"]])
            people_mini_ph.markdown(ui.metric_card("People in Frame", len(boxes)), unsafe_allow_html=True)
            score_mini_ph.markdown(ui.metric_card("Threat Score", f"{state['score']:.2f}"), unsafe_allow_html=True)
            trend_ph.area_chart(pd.DataFrame({"threat score": list(history)}))
            st.session_state.prev_people = len(boxes)

        video_ph.image(core.annotate(rgb, boxes, state), channels="RGB", use_container_width=True)
finally:
    cap.release()