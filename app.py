import time
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# =========================================================
# CONFIG
# =========================================================
SERVER = "https://drns-1.onrender.com"
REFRESH_SEC = 2

BAGHDAD_LAT = 33.3152
BAGHDAD_LON = 44.3661

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
    return requests.get(SERVER + "/uavs?process=true", timeout=20).json()

try:
    data = fetch_data()
except Exception as e:
    st.error(f"Server connection failed: {e}")
    st.stop()

# =========================================================
# DATAFRAME
# =========================================================
rows = []
for u in data["uavs"]:
    rows.append({
        "UAV_ID": u["uav_id"],
        "lon": u["x"],
        "lat": u["y"],
        "status": u["status"]
    })

df = pd.DataFrame(rows)

# =========================================================
# UAV MAP (BAGHDAD ONLY)
# =========================================================
st.subheader("🗺️ UAV Airspace – Baghdad")

colors = {
    "safe": "blue",
    "outer_near": "gold",
    "inner_near": "orange",
    "collision": "red"
}

map_fig = go.Figure()

# ---- UAVs ----
for s, c in colors.items():
    d = df[df["status"] == s]
    map_fig.add_trace(go.Scattermapbox(
        lat=d["lat"],
        lon=d["lon"],
        mode="markers",
        marker=dict(size=12, color=c),
        name=s
    ))

# ---- BAGHDAD DISTRICT LABELS ----
districts = {
    "Karkh": (33.3060, 44.3470),
    "Rusafa": (33.3150, 44.3950),
    "Kadhimiya": (33.3790, 44.3390),
    "Adhamiya": (33.3660, 44.3930),
    "Sadr City": (33.3810, 44.4500),
    "Mansour": (33.3140, 44.3180),
    "Dora": (33.2550, 44.3900),
    "New Baghdad": (33.3000, 44.4700)
}

map_fig.add_trace(go.Scattermapbox(
    lat=[v[0] for v in districts.values()],
    lon=[v[1] for v in districts.values()],
    mode="text",
    text=list(districts.keys()),
    textfont=dict(size=14, color="black"),
    name="Baghdad Districts"
))

map_fig.update_layout(
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=BAGHDAD_LAT, lon=BAGHDAD_LON),
        zoom=10.8
    ),
    height=520,
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h")
)

st.plotly_chart(map_fig, use_container_width=True)

# =========================================================
# STATUS SUMMARY (UNDER MAP)
# =========================================================
st.markdown("### 📊 UAV Status Summary")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Safe", sum(df["status"] == "safe"))
with c2:
    st.metric("Outer Near", sum(df["status"] == "outer_near"))
with c3:
    st.metric("Inner Near", sum(df["status"] == "inner_near"))
with c4:
    st.metric("Collision", sum(df["status"] == "collision"))

# =========================================================
# AUTO REFRESH
# =========================================================
time.sleep(REFRESH_SEC)
st.rerun()
