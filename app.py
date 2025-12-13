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

st.set_page_config(
    page_title="UAV Real-Time Dashboard",
    layout="wide"
)

# IEEE Colors
COLORS = {
    "safe": "rgb(0,77,255)",
    "outer_near": "rgb(255,204,0)",
    "inner_near": "rgb(255,102,0)",
    "collision": "rgb(255,0,0)",
    "pred": "rgb(255,0,255)",
    "after": "rgb(0,180,0)"
}

# =========================================================
# TITLE
# =========================================================
st.title(" UAV Real-Time Monitoring & Collision Avoidance Dashboard")

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
    st.success("✔ Data fetched from server")
except Exception as e:
    st.error(f" Server connection failed: {e}")
    st.stop()

# =========================================================
# TO DATAFRAME
# =========================================================
def to_df(data):
    rows = []
    for u in data["uavs"]:
        rows.append({
            "ID": u["uav_id"],
            "X": u["x"],
            "Y": u["y"],
            "Status": u["status"],
            "dmin": u["min_distance_km"],
            "PredX": u["predicted"]["x"] if "predicted" in u and u["predicted"] else np.nan,
            "PredY": u["predicted"]["y"] if "predicted" in u and u["predicted"] else np.nan
        })
    return pd.DataFrame(rows)

dfB = to_df(data_before)
dfA = to_df(data_after)

# =========================================================
# 4-PANEL PLOT
# =========================================================
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=[
        "1) BEFORE – Raw UAV Positions",
        "2) Prediction",
        "3) AFTER – Server Avoidance",
        "4) Status Distribution"
    ]
)

# BEFORE
for s in ["safe", "outer_near", "inner_near", "collision"]:
    d = dfB[dfB["Status"] == s]
    fig.add_trace(
        go.Scatter(
            x=d["X"], y=d["Y"],
            mode="markers",
            marker=dict(
                symbol="circle-open",
                size=10,
                color=COLORS[s],
                line=dict(width=2)
            ),
            name=f"BEFORE {s}"
        ),
        row=1, col=1
    )

# PREDICTION
valid = dfB["PredX"].notna()
fig.add_trace(
    go.Scatter(
        x=dfB[valid]["X"],
        y=dfB[valid]["Y"],
        mode="markers",
        marker=dict(symbol="circle-open", size=9, color="black"),
        name="Before"
    ),
    row=1, col=2
)

fig.add_trace(
    go.Scatter(
        x=dfB[valid]["PredX"],
        y=dfB[valid]["PredY"],
        mode="markers",
        marker=dict(symbol="circle-open", size=10, color=COLORS["pred"]),
        name="Predicted"
    ),
    row=1, col=2
)

# AFTER
for s in ["safe", "outer_near", "inner_near", "collision"]:
    d = dfA[dfA["Status"] == s]
    fig.add_trace(
        go.Scatter(
            x=d["X"], y=d["Y"],
            mode="markers",
            marker=dict(
                symbol="circle-open",
                size=10,
                color=COLORS[s],
                line=dict(width=2)
            ),
            name=f"AFTER {s}"
        ),
        row=2, col=1
    )

# HISTOGRAM
labels = ["safe", "outer_near", "inner_near", "collision"]
before_counts = [sum(dfB["Status"] == s) for s in labels]
after_counts  = [sum(dfA["Status"] == s) for s in labels]

fig.add_trace(
    go.Bar(x=labels, y=before_counts, name="Before"),
    row=2, col=2
)
fig.add_trace(
    go.Bar(x=labels, y=after_counts, name="After"),
    row=2, col=2
)

fig.update_layout(
    height=800,
    showlegend=True,
    barmode="group",
    margin=dict(l=20, r=20, t=60, b=20)
)

st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TABLES
# =========================================================
st.subheader(" RAW DATA TABLES")

c1, c2 = st.columns(2)

with c1:
    st.markdown("**BEFORE**")
    st.dataframe(dfB, use_container_width=True)

with c2:
    st.markdown("**AFTER**")
    st.dataframe(dfA, use_container_width=True)

# =========================================================
# AUTO REFRESH
# =========================================================
time.sleep(2)
st.rerun()
