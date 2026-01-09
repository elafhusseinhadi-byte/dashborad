import time
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================================================
# CONFIG
# =========================================================
SERVER = "https://drns-1.onrender.com"
REFRESH_SEC = 2

st.set_page_config(page_title="UAV Dashboard", layout="wide")

# =========================================================
# STYLE
# =========================================================
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 0.5rem;
}
h2 {
    margin-top: 0;
    margin-bottom: 0.6rem;
}
.stAlert { display: none; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.markdown(
    "<h2>UAV Real-Time Monitoring & Collision Avoidance Dashboard</h2>",
    unsafe_allow_html=True
)

# =========================================================
# FETCH DATA
# =========================================================
@st.cache_data(ttl=2)
def fetch_data():
    before = requests.get(SERVER + "/uavs?process=false", timeout=20).json()
    after  = requests.get(SERVER + "/uavs?process=true",  timeout=20).json()
    return before, after

try:
    data_before, data_after = fetch_data()
except Exception as e:
    st.error(f"Server connection failed: {e}")
    st.stop()

# =========================================================
# DATAFRAME
# =========================================================
def to_df(data):
    rows = []
    for u in data["uavs"]:
        rows.append({
            "UAV_ID": u["uav_id"],
            "X": u["x"],
            "Y": u["y"],
            "Status": u["status"],
            "dmin": u["min_distance_km"],
            "PredX": u["predicted"]["x"] if u.get("predicted") else np.nan,
            "PredY": u["predicted"]["y"] if u.get("predicted") else np.nan
        })
    return pd.DataFrame(rows)

dfB = to_df(data_before)
dfA = to_df(data_after)

# =========================================================
# COLLISION ALERT
# =========================================================
collision_count = sum(dfA["Status"] == "collision")
if collision_count > 0:
    st.error(f"🚨 COLLISION ALERT: {collision_count} UAV(s) detected!")
else:
    st.success("✅ No collisions detected")

# =========================================================
# COLORS
# =========================================================
colors = {
    "safe": "blue",
    "outer_near": "gold",
    "inner_near": "orange",
    "collision": "red"
}

# =========================================================
# TOP ROW PLOTS
# =========================================================
fig_top = make_subplots(
    rows=1, cols=4,
    subplot_titles=[
        "BEFORE – Raw Positions",
        "Prediction",
        "AFTER – Avoidance",
        "Status Distribution"
    ]
)

for s in colors:
    d = dfB[dfB["Status"] == s]
    fig_top.add_trace(go.Scatter(
        x=d["X"], y=d["Y"],
        mode="markers",
        marker=dict(size=8, color=colors[s], symbol="circle-open"),
        name=f"BEFORE {s}"
    ), row=1, col=1)

valid = dfB["PredX"].notna()
fig_top.add_trace(go.Scatter(
    x=dfB[valid]["X"], y=dfB[valid]["Y"],
    mode="markers",
    marker=dict(color="black"),
    name="Before"
), row=1, col=2)

fig_top.add_trace(go.Scatter(
    x=dfB[valid]["PredX"], y=dfB[valid]["PredY"],
    mode="markers",
    marker=dict(color="magenta"),
    name="Predicted"
), row=1, col=2)

for s in colors:
    d = dfA[dfA["Status"] == s]
    fig_top.add_trace(go.Scatter(
        x=d["X"], y=d["Y"],
        mode="markers",
        marker=dict(size=8, color=colors[s], symbol="circle-open"),
        name=f"AFTER {s}"
    ), row=1, col=3)

labels = list(colors.keys())
fig_top.add_trace(go.Bar(
    x=labels,
    y=[sum(dfB["Status"] == s) for s in labels],
    name="Before"
), row=1, col=4)

fig_top.add_trace(go.Bar(
    x=labels,
    y=[sum(dfA["Status"] == s) for s in labels],
    name="After"
), row=1, col=4)

fig_top.update_layout(
    height=360,
    barmode="group",
    legend=dict(orientation="h", y=-0.28)
)

st.plotly_chart(fig_top, use_container_width=True)

# =========================================================
# MAP (IMPROVED)
# =========================================================
# =========================================================
# UAV MAP (CLEAN & SIMPLE)
# =========================================================
st.subheader("🗺️ UAV Geographical Map")

map_fig = go.Figure()

size_map = {
    "safe": 9,
    "outer_near": 11,
    "inner_near": 13,
    "collision": 15
}

for s, col in colors.items():
    d = dfA[dfA["Status"] == s]
    map_fig.add_trace(go.Scattermapbox(
        lat=d["Y"],
        lon=d["X"],
        mode="markers",
        marker=dict(
            size=size_map[s],
            color=col,
            opacity=0.85
        ),
        name=s,
        hovertemplate=
        "UAV %{customdata}<br>Status: " + s + "<extra></extra>",
        customdata=d["UAV_ID"]
    ))

map_fig.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(
            lat=dfA["Y"].mean(),
            lon=dfA["X"].mean()
        ),
        zoom=10.5
    ),
    height=420,
    margin=dict(l=0, r=0, t=20, b=0),
    legend=dict(
        orientation="h",
        y=-0.15
    )
)

st.plotly_chart(map_fig, use_container_width=True)

# =========================================================
# MAP SUMMARY
# =========================================================
# =========================================================
# MAP SUMMARY (BY STATUS)
# =========================================================
st.markdown("### 📌 Map Summary")

safe_count      = int(sum(dfA["Status"] == "safe"))
near_count      = int(sum(dfA["Status"].isin(["outer_near", "inner_near"])))
collision_count = int(sum(dfA["Status"] == "collision"))

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(" Safe UAVs", safe_count)

with c2:
    st.metric(" Near UAVs", near_count)

with c3:
    st.metric(" Collisions", collision_count)

st.info(
    "This summary shows the number of UAVs classified as safe, near-risk, "
    "and collision after applying the cloud-based avoidance algorithm."
)


# =========================================================
# AUTO REFRESH
# =========================================================
time.sleep(REFRESH_SEC)
st.rerun()
