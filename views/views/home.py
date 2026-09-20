import streamlit as st
import ui

ui.hero("AI-Based Crowd Abnormal Behavior Detection",
        "with Multi-Level Threat Assessment. Upload CCTV footage and every alert is graded "
        "Low, Medium, High or Critical, so security teams know where to respond first.")

st.subheader("How it works")
c1, c2, c3, c4 = st.columns(4)
c1.markdown(ui.card("1. Detect", "YOLOv8 finds every person in each frame and draws the bounding boxes."),
            unsafe_allow_html=True)
c2.markdown(ui.card("2. Understand", "ResNet18 extracts visual features and an LSTM reads them as a "
                    "sequence to judge if the crowd behavior is normal or abnormal."),
            unsafe_allow_html=True)
c3.markdown(ui.card("3. Assess", "The Threat Scoring module combines model confidence, persistence "
                    "over time and zone risk into one score."),
            unsafe_allow_html=True)
c4.markdown(ui.card("4. Alert", "The score is mapped to Low, Medium, High or Critical and shown on "
                    "an annotated video and a timeline."),
            unsafe_allow_html=True)

st.write("")
st.subheader("Why threat grading?")
st.write("Most surveillance systems raise the same 'abnormal detected' alert for everything, "
         "from a small disturbance to a serious fight. When many alerts arrive together, operators "
         "cannot tell which one to handle first. This system ranks the alerts.")

st.subheader("Threat levels")
levels = [("Low", "Slight abnormal signal. Keep watching."),
          ("Medium", "Abnormal behavior is continuing."),
          ("High", "Strong, sustained signal. Prioritize."),
          ("Critical", "Strongest and longest-lasting signal. Respond first.")]
cols = st.columns(4)
for col, (lvl, desc) in zip(cols, levels):
    col.markdown(ui.badge(lvl), unsafe_allow_html=True)
    col.caption(desc)

st.write("")
st.page_link("views/analyze.py", label="Start analysis", icon="🎥")