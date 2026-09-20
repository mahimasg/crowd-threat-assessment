import streamlit as st
import core
import ui

st.title("Results Dashboard")

res = st.session_state.get("res")
if not res:
    st.info("Innum edhuvum analyze pannala. Mudhalla oru video analyze pannunga.")
    st.page_link("views/analyze.py", label="Go to Analyze Video", icon="🎥")
    st.stop()

t, ev, meta = res["table"], res["events"], res.get("meta", {})
level = res["highest"]
flagged = t[t["flag"]]

if level == "Normal":
    ui.show(ui.banner("Normal", "NO THREAT DETECTED", f"{meta.get('file', '')}  |  {meta.get('zone', '')}"))
else:
    ui.show(ui.banner(level, f"HIGHEST THREAT LEVEL: {level.upper()}",
                      f"{len(ev)} alert event(s)  |  {meta.get('file', '')}  |  {meta.get('zone', '')}"))

m1, m2, m3, m4 = st.columns(4)
m1.markdown(ui.metric_card("Alert events", len(ev), "continuous abnormal periods"), unsafe_allow_html=True)
m2.markdown(ui.metric_card("Peak threat score", f"{flagged['score'].max():.2f}" if len(flagged) else "-",
                           "highest score in any alert"), unsafe_allow_html=True)
m3.markdown(ui.metric_card("Alert clips", f"{len(flagged)} / {len(t)}", "flagged / total"),
            unsafe_allow_html=True)
m4.markdown(ui.metric_card("Duration analyzed", f"{res['duration']:.0f} s", ""), unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3, tab4 = st.tabs(["Annotated video", "Threat timeline", "Alert events", "Details"])

with tab1:
    st.video(res["video"])
    st.caption("Box and banner color show the threat level of the current moment.")

with tab2:
    chart = t.set_index("start_s")[["conf", "score"]]
    chart.columns = ["abnormal confidence", "threat score"]
    st.line_chart(chart)
    st.caption("X-axis: time in seconds.")
    st.markdown("**Clips per threat level**")
    counts = t["level"].value_counts()
    cols = st.columns(5)
    for col, lvl in zip(cols, core.ORDER):
        col.markdown(ui.metric_card(lvl, int(counts.get(lvl, 0))), unsafe_allow_html=True)

with tab3:
    if len(ev) == 0:
        st.success("No abnormal behavior detected in this video.")
    else:
        st.dataframe(ev, use_container_width=True, hide_index=True)

with tab4:
    cfg = core.get_cfg()
    c = cfg["CUTS"]
    st.write(f"**File:** {meta.get('file', '-')}")
    st.write(f"**Zone risk:** {meta.get('zone', '-')}")
    st.write(f"**Abnormal threshold:** {meta.get('threshold', '-')}")
    st.write(f"**Score:** {cfg['W'][0]} x confidence + {cfg['W'][1]} x persistence + {cfg['W'][2]} x zone")
    st.write(f"**Level cut-offs:** Low < {c[0]:.2f} <= Medium < {c[1]:.2f} <= High < {c[2]:.2f} <= Critical")
    st.dataframe(t.round(3), use_container_width=True, hide_index=True)
    st.download_button("Download clip-level results (CSV)", t.to_csv(index=False),
                       file_name="threat_results.csv", mime="text/csv")