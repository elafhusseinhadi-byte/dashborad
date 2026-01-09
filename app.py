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

data_before, data_after = fetch_data()

# =========================================================
# TO DATAFRAME
# =========================================================
def to_df(data):
    rows = []
    for u in data["uavs"]:
        rows.append({
            "UAV_ID": u["uav_id"],
            "X": float(u["x"]),   # longitude
            "Y": float(u["y"]),   # latitude
            "Status": u["status"],
            "dmin": u["min_distance_km"]
        })
    return pd.DataFrame(rows)

dfB = to_df(data_before)
dfA = to_df(data_after)

# تنظيف البيانات
dfA = dfA.dropna(subset=["X","Y"])

# =========================================================
# STATUS COLORS
# =========================================================
colors = {
    "safe": "blue",
    "outer_near": "gold",
    "inner_near": "orange",
    "collision": "red"
}

# =========================================================
# MAP – BAGHDAD
# =========================================================
st.subheader("🗺️ Baghdad Airspace – UAV Positions")

map_fig = go.Figure()

for status, color in colors.items():
    d = dfA[dfA["Status"] == status]

    map_fig.add_trace(go.Scattermapbox(
        lat=d["Y"],
        lon=d["X"],
        mode="markers",
        marker=dict(size=12, color=color),
        text=d["UAV_ID"],
        hovertemplate=
            "UAV ID: %{text}<br>" +
            "Lat: %{lat}<br>" +
            "Lon: %{lon}<br>" +
            "Status: " + status +
            "<extra></extra>",
        name=status
    ))

map_fig.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=33.3152, lon=44.3661),  # Baghdad
        zoom=11
    ),
    height=500,
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", y=0.02)
)

st.plotly_chart(map_fig, use_container_width=True)

# =========================================================
# STATUS COUNTS
# =========================================================
st.subheader("📊 UAV Status Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Safe", (dfA["Status"]=="safe").sum())
col2.metric("Outer Near", (dfA["Status"]=="outer_near").sum())
col3.metric("Inner Near", (dfA["Status"]=="inner_near").sum())
col4.metric("Collision", (dfA["Status"]=="collision").sum())

# =========================================================
# TABLE
# =========================================================
st.subheader("📋 UAV Data")
st.dataframe(dfA, use_container_width=True, height=350)

# =========================================================
# AUTO REFRESH
# =========================================================
time.sleep(REFRESH_SEC)
st.rerun()
