import os
import pandas as pd
import streamlit as st
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
import core
import ui

ui.hero("System & Performance", "How the pipeline works and how it performs on held-out test clips.")

st.subheader("Architecture")
a, b, c, d = st.columns(4)
a.markdown(ui.card("YOLOv8n", "Pretrained person detector. Gives bounding boxes and person count."),
           unsafe_allow_html=True)
b.markdown(ui.card("ResNet18", "Pretrained CNN. Turns each frame into a 512-dimension feature vector."),
           unsafe_allow_html=True)
c.markdown(ui.card("LSTM", "Reads 16 frame-features per clip and outputs the probability of abnormal behavior."),
           unsafe_allow_html=True)
d.markdown(ui.card("Threat scoring", "Combines confidence, persistence and zone risk into Low / Medium / High / Critical."),
           unsafe_allow_html=True)

st.write("")
st.subheader("Threat score")
if core.files_ready():
    cfg = core.get_cfg()
    cu = cfg["CUTS"]
    st.markdown(f"`score = {cfg['W'][0]} x confidence + {cfg['W'][1]} x persistence + {cfg['W'][2]} x zone risk`")
    st.caption(f"Persistence = consecutive abnormal clips / {cfg['P_MAX']} (max 1.0). "
               f"Cut-offs: Low < {cu[0]:.2f} <= Medium < {cu[1]:.2f} <= High < {cu[2]:.2f} <= Critical.")

st.subheader("Performance on held-out test clips")
path = os.path.join(core.BASE, "results", "threat_scores.csv")
if os.path.exists(path):
    df = pd.read_csv(path)
    t = df[df["split"] == "test"]
    y = t["label"].values
    pred = t["abn_flag"].astype(int).values
    p, r, f1, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    auc = roc_auc_score(y, t["conf"]) if len(set(y)) > 1 else float("nan")
    st.caption(f"Test split: {len(t)} clips, {int(t['label'].sum())} truly abnormal. "
               f"Dataset: ShanghaiTech Campus (video-level split).")
    m = st.columns(4)
    for col, (lbl, val) in zip(m, [("Precision", p), ("Recall", r), ("F1", f1), ("AUC", auc)]):
        col.markdown(ui.metric_card(lbl, f"{val:.3f}"), unsafe_allow_html=True)

    st.write("")
    st.markdown("**Does a higher threat level mean a higher chance of a real incident?**")
    g = t.groupby("level")["label"].agg(["count", "mean"]).reindex(core.ORDER).dropna()
    g["mean"] = (g["mean"] * 100).round(1)
    g.columns = ["clips", "% truly abnormal"]
    left, right = st.columns([2, 3])
    left.dataframe(g, use_container_width=True)
    chart = g[["% truly abnormal"]].copy()
    chart.index = [f"{i + 1}. {name}" for i, name in enumerate(chart.index)]
    right.bar_chart(chart)