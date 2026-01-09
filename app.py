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
# TO DATAFRAME
# =========================================================
def to_df(data):
    rows = []
    for u in data["uavs"]:
        rows.append({
            "UAV_ID": u["uav_id"],
            "X": u["x"],          # longitude
            "Y": u["y"],          # latitude
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
# MAIN PLOTS
# =========================================================
colors = {
    "safe": "blue",
    "outer_near": "gold",
    "inner_near": "orange",
    "collision": "red"
}

fig_top = make_subplots(
    rows=1, cols=4,
    subplot_titles=[
        "BEFORE – Raw Positions",
        "Prediction",
        "AFTER – Avoidance",
        "Status Distribution"
    ]
)

# BEFORE
for s in colors:
    d = dfB[dfB["Status"] == s]
    fig_top.add_trace(go.Scatter(
        x=d["X"], y=d["Y"],
        mode="markers",
        marker=dict(size=8, color=colors[s], symbol="circle-open"),
        name=f"BEFORE {s}"
    ), row=1, col=1)

# PREDICTION
valid = dfB["PredX"].notna()
fig_top.add_trace(go.Scatter(
    x=dfB[valid]["X"], y=dfB[valid]["Y"],
    mode="markers",
    marker=dict(size=7, color="black"),
    name="Before"
), row=1, col=2)

fig_top.add_trace(go.Scatter(
    x=dfB[valid]["PredX"], y=dfB[valid]["PredY"],
    mode="markers",
    marker=dict(size=8, color="magenta"),
    name="Predicted"
), row=1, col=2)

# AFTER
for s in colors:
    d = dfA[dfA["Status"] == s]
    fig_top.add_trace(go.Scatter(
        x=d["X"], y=d["Y"],
        mode="markers",
        marker=dict(size=8, color=colors[s], symbol="circle-open"),
        name=f"AFTER {s}"
    ), row=1, col=3)

# STATUS BAR
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
    legend=dict(orientation="h", y=-0.3),
    margin=dict(l=10, r=10, t=40, b=10)
)

st.plotly_chart(fig_top, use_container_width=True)

# =========================================================
# ANALYSIS PLOTS
# =========================================================
pred_move = np.sqrt((dfB["PredX"] - dfB["X"])**2 + (dfB["PredY"] - dfB["Y"])**2)
delta_dmin = dfA["dmin"].values - dfB["dmin"].values

c1, c2, c3 = st.columns(3)

with c1:
    st.plotly_chart(go.Figure(
        go.Scatter(y=pred_move, mode="lines+markers")
    ).update_layout(title="Predicted Displacement", height=260), use_container_width=True)

with c2:
    st.plotly_chart(go.Figure(
        go.Bar(y=delta_dmin)
    ).update_layout(title="Δ dmin", height=260), use_container_width=True)

with c3:
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=dfB["dmin"], mode="lines+markers", name="Before"))
    fig.add_trace(go.Scatter(y=dfA["dmin"], mode="lines+markers", name="After"))
    fig.update_layout(title="dmin Before vs After", height=260)
    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# BAGHDAD MAP (FIXED)
# =========================================================
st.subheader("🗺️ Baghdad Airspace – UAV Positions")

map_df = dfA.dropna(subset=["X", "Y"])

map_fig = go.Figure()

for s, col in colors.items():
    d = map_df[map_df["Status"] == s]
    if len(d) == 0:
        continue

    map_fig.add_trace(go.Scattermapbox(
        lat=d["Y"].astype(float),
        lon=d["X"].astype(float),
        mode="markers",
        marker=dict(size=16, color=col, opacity=0.95),
        text=d["UAV_ID"],
        hovertemplate=
            "<b>UAV:</b> %{text}<br>" +
            "<b>Status:</b> " + s +
            "<extra></extra>",
        name=s
    ))

map_fig.update_layout(
    mapbox=dict(
        style="carto-positron",
        center=dict(lat=33.3152, lon=44.3661),  # بغداد
        zoom=12
    ),
    height=480,
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", y=0.02)
)

st.plotly_chart(map_fig, use_container_width=True)

# =========================================================
# TABLES
# =========================================================
st.subheader("RAW UAV DATA")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**BEFORE**")
    st.dataframe(dfB, use_container_width=True, height=300)
with c2:
    st.markdown("**AFTER**")
    st.dataframe(dfA, use_container_width=True, height=300)

# =========================================================
# AUTO REFRESH
# =========================================================
time.sleep(REFRESH_SEC)
st.rerun()
