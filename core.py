import os, json
import numpy as np
import pandas as pd
import cv2
import torch
import torch.nn as nn
from torchvision import models
from ultralytics import YOLO
import imageio
import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "cnn_lstm.pt")
CFG_PATH = os.path.join(BASE, "models", "threat_config.json")
CLIP_LEN, STRIDE, TARGET_FPS = 16, 8, 6
ORDER = ["Normal", "Low", "Medium", "High", "Critical"]
COLORS = {"Normal": (40, 160, 40), "Low": (200, 160, 0), "Medium": (255, 130, 0),
          "High": (220, 0, 0), "Critical": (170, 0, 170)}          # RGB
ZONES = {"Entrance / gate / narrow exit (high risk)": 1.0,
         "Main walkway / junction (medium risk)": 0.7,
         "Open area (low risk)": 0.5}
device = "cuda" if torch.cuda.is_available() else "cpu"
MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)


def files_ready():
    return os.path.exists(MODEL_PATH) and os.path.exists(CFG_PATH)


def get_cfg():
    with open(CFG_PATH) as f:
        return json.load(f)


class LSTMClassifier(nn.Module):
    def __init__(self, in_dim=512, hidden=128):
        super().__init__()
        self.lstm = nn.LSTM(in_dim, hidden, batch_first=True)
        self.drop = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden, 2)

    def forward(self, x):
        _, (h, _) = self.lstm(x)
        return self.fc(self.drop(h[-1]))


@st.cache_resource(show_spinner="Loading models...")
def load_models():
    cnn = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    cnn.fc = nn.Identity()
    cnn.eval().to(device)
    lstm = LSTMClassifier()
    lstm.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    lstm.eval().to(device)
    yolo = YOLO("yolov8n.pt")
    return cnn, lstm, yolo


def read_video(path, max_seconds):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    step = max(1, int(round(fps / TARGET_FPS)))
    eff_fps = fps / step
    max_samples = int(max_seconds * eff_fps)
    frames, i = [], 0
    while len(frames) < max_samples:
        ok, img = cap.read()
        if not ok:
            break
        if i % step == 0:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            nw = 640
            nh = int(round(h * nw / w))
            nh -= nh % 2
            frames.append(cv2.resize(rgb, (nw, nh)))
        i += 1
    cap.release()
    return frames, eff_fps


def extract_features(cnn, frames, tick):
    feats = []
    with torch.no_grad():
        for i in range(0, len(frames), 32):
            batch = np.stack([cv2.resize(f, (224, 224)) for f in frames[i:i + 32]])
            x = torch.from_numpy(batch).permute(0, 3, 1, 2).float() / 255.0
            x = ((x - MEAN) / STD).to(device)
            feats.append(cnn(x).cpu().numpy())
            tick(min(1.0, (i + 32) / len(frames)))
    return np.concatenate(feats)


def detect_people(yolo, frames, tick):
    boxes = []
    for i in range(0, len(frames), 16):
        chunk = [np.ascontiguousarray(f[:, :, ::-1]) for f in frames[i:i + 16]]   # BGR for YOLO
        res = yolo.predict(chunk, classes=[0], conf=0.25, imgsz=480, verbose=False)
        boxes.extend([r.boxes.xyxy.cpu().numpy() for r in res])
        tick(min(1.0, (i + 16) / len(frames)))
    return boxes


def classify_clips(lstm, feats):
    starts = list(range(0, len(feats) - CLIP_LEN + 1, STRIDE))
    X = np.stack([feats[s:s + CLIP_LEN] for s in starts]).astype(np.float32)
    probs = []
    with torch.no_grad():
        for i in range(0, len(X), 128):
            xb = torch.from_numpy(X[i:i + 128]).to(device)
            probs.append(torch.softmax(lstm(xb), 1)[:, 1].cpu().numpy())
    return starts, np.concatenate(probs)


def threat_table(starts, probs, eff_fps, zone_w, thresh):
    cfg = get_cfg()
    conf = np.asarray(probs)
    flag = conf >= thresh
    run = np.zeros(len(conf), dtype=int)
    r = 0
    for i, f in enumerate(flag):
        r = r + 1 if f else 0
        run[i] = r
    pers = np.clip(run / cfg["P_MAX"], 0, 1)
    wc, wp, wz = cfg["W"]
    score = wc * conf + wp * pers + wz * zone_w
    c = cfg["CUTS"]
    level = np.where(score >= c[2], "Critical",
                     np.where(score >= c[1], "High",
                              np.where(score >= c[0], "Medium", "Low")))
    level = np.where(flag, level, "Normal")
    s = np.array(starts)
    return pd.DataFrame({"clip": range(len(starts)), "start_s": s / eff_fps,
                         "end_s": (s + CLIP_LEN) / eff_fps, "conf": conf, "flag": flag,
                         "run": run, "score": score, "level": level})


def build_events(table):
    events, cur = [], None
    for row in table.itertuples():
        if row.flag:
            if cur is None:
                cur = {"Start (s)": round(row.start_s, 1), "End (s)": round(row.end_s, 1),
                       "Peak level": row.level, "Peak score": row.score}
            else:
                cur["End (s)"] = round(row.end_s, 1)
                cur["Peak score"] = max(cur["Peak score"], row.score)
                if ORDER.index(row.level) > ORDER.index(cur["Peak level"]):
                    cur["Peak level"] = row.level
        elif cur is not None:
            events.append(cur)
            cur = None
    if cur is not None:
        events.append(cur)
    out = pd.DataFrame(events, columns=["Start (s)", "End (s)", "Peak level", "Peak score"])
    out["Peak score"] = out["Peak score"].round(2)
    return out


def frame_states(n, starts):
    state = [None] * n
    for k, s in enumerate(starts):
        rng = range(s, s + CLIP_LEN) if k == 0 else range(s + CLIP_LEN - STRIDE, s + CLIP_LEN)
        for i in rng:
            state[i] = k
    return [k if k is not None else len(starts) - 1 for k in state]


def render_video(frames, boxes, state, table, eff_fps, zone_w, out_path):
    rows = table.to_dict("records")
    writer = imageio.get_writer(out_path, fps=eff_fps, codec="libx264", quality=7,
                                pixelformat="yuv420p", macro_block_size=1)
    for i, img in enumerate(frames):
        img = img.copy()
        row = rows[state[i]]
        level = row["level"]
        color = COLORS[level]
        for b in boxes[i]:
            cv2.rectangle(img, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 2)
        cv2.rectangle(img, (0, 0), (img.shape[1], 56), color, -1)
        title = "NORMAL" if level == "Normal" else f"THREAT: {level.upper()} (score {row['score']:.2f})"
        cv2.putText(img, title, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        detail = (f"conf {row['conf']:.2f} | persistence {int(row['run'])} clips | "
                  f"zone {zone_w:.1f} | persons {len(boxes[i])}")
        cv2.putText(img, detail, (10, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        writer.append_data(img)
    writer.close()


def analyze(src, zone_w, thresh, max_sec, tick):
    cnn, lstm, yolo = load_models()
    tick(0.02, "Reading video...")
    frames, eff_fps = read_video(src, max_sec)
    if len(frames) < CLIP_LEN:
        return None
    feats = extract_features(cnn, frames, lambda f: tick(0.05 + 0.30 * f, "Extracting CNN features..."))
    boxes = detect_people(yolo, frames, lambda f: tick(0.35 + 0.40 * f, "Detecting people (YOLO)..."))
    tick(0.78, "Classifying behavior (LSTM)...")
    starts, probs = classify_clips(lstm, feats)
    table = threat_table(starts, probs, eff_fps, zone_w, thresh)
    events = build_events(table)
    state = frame_states(len(frames), starts)
    tick(0.85, "Rendering annotated video...")
    out_path = os.path.join(BASE, "results", "app_output.mp4")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    render_video(frames, boxes, state, table, eff_fps, zone_w, out_path)
    with open(out_path, "rb") as f:
        video_bytes = f.read()
    tick(1.0, "Done")
    highest = max(table["level"], key=ORDER.index)
    return {"table": table, "events": events, "video": video_bytes,
            "highest": highest, "duration": len(frames) / eff_fps}
# ---------------- LIVE MONITORING helpers ----------------
def open_capture(source):
    """source: int (webcam) illa str (RTSP/HTTP url illa video file path)"""
    if isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(source)
    else:
        cap = cv2.VideoCapture(source)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    return cap


def prep_frame(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    nw = 640
    nh = int(round(h * nw / w))
    nh -= nh % 2
    return cv2.resize(rgb, (nw, nh))


def frame_feature(cnn, rgb):
    x = torch.from_numpy(cv2.resize(rgb, (224, 224))).permute(2, 0, 1).float().unsqueeze(0) / 255.0
    x = ((x - MEAN) / STD).to(device)
    with torch.no_grad():
        return cnn(x).cpu().numpy()[0]


def clip_prob(lstm, feat_list):
    x = torch.from_numpy(np.stack(feat_list).astype(np.float32)).unsqueeze(0).to(device)
    with torch.no_grad():
        return torch.softmax(lstm(x), 1)[0, 1].item()


def threat_step(prob, prev_run, zone_w, thresh):
    cfg = get_cfg()
    flag = prob >= thresh
    run = prev_run + 1 if flag else 0
    pers = min(run / cfg["P_MAX"], 1.0)
    wc, wp, wz = cfg["W"]
    score = wc * prob + wp * pers + wz * zone_w
    c = cfg["CUTS"]
    if not flag:
        level = "Normal"
    elif score >= c[2]:
        level = "Critical"
    elif score >= c[1]:
        level = "High"
    elif score >= c[0]:
        level = "Medium"
    else:
        level = "Low"
    return {"conf": prob, "flag": flag, "run": run, "score": score, "level": level}


def yolo_boxes(yolo, rgb):
    r = yolo.predict(np.ascontiguousarray(rgb[:, :, ::-1]), classes=[0], conf=0.25,
                     imgsz=320, verbose=False)[0]
    return r.boxes.xyxy.cpu().numpy()


def annotate(rgb, boxes, state):
    img = rgb.copy()
    level = state["level"]
    color = COLORS[level]
    for b in boxes:
        cv2.rectangle(img, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 2)
    cv2.rectangle(img, (0, 0), (img.shape[1], 40), color, -1)
    title = "NORMAL" if level == "Normal" else f"THREAT: {level.upper()} ({state['score']:.2f})"
    cv2.putText(img, title, (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return img