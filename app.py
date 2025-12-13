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

st.set_page_config(
    page_title="UAV Dashboard",
    layout="wide"
)

# ===== Compact layout (reduce top space) =====
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}
h1 { margin-bottom: 0.5rem; }
.stAlert { margin-top: 0.5rem; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.markdown("UAV Real-Time Monitoring & Collision Avoidance Dashboard")

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
    st.success(" Data fetched from server")
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
            "UAV_ID": u["uav_id"],
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
# 4 MAIN PLOTS (TOP)
# =========================================================
colors = {
    "safe": "blue",
    "outer_near": "gold",
    "inner_near": "orange",
    "collision": "red"
}

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
for s in colors:
    d = dfB[dfB["Status"] == s]
    fig.add_trace(
        go.Scatter(
            x=d["X"], y=d["Y"],
            mode="markers",
            marker=dict(size=9, symbol="circle-open", color=colors[s]),
            name=f"BEFORE {s}"
        ),
        row=1, col=1
    )

# PREDICTION
valid = dfB["PredX"].notna()
fig.add_trace(go.Scatter(
    x=dfB[valid]["X"], y=dfB[valid]["Y"],
    mode="markers",
    marker=dict(size=8, symbol="circle-open", color="black"),
    name="Before"
), row=1, col=2)

fig.add_trace(go.Scatter(
    x=dfB[valid]["PredX"], y=dfB[valid]["PredY"],
    mode="markers",
    marker=dict(size=9, symbol="circle-open", color="magenta"),
    name="Predicted"
), row=1, col=2)

# AFTER
for s in colors:
    d = dfA[dfA["Status"] == s]
    fig.add_trace(
        go.Scatter(
            x=d["X"], y=d["Y"],
            mode="markers",
            marker=dict(size=9, symbol="circle-open", color=colors[s]),
            name=f"AFTER {s}"
        ),
        row=2, col=1
    )

# HISTOGRAM
labels = list(colors.keys())
fig.add_trace(go.Bar(
    x=labels,
    y=[sum(dfB["Status"] == s) for s in labels],
    name="Before"
), row=2, col=2)

fig.add_trace(go.Bar(
    x=labels,
    y=[sum(dfA["Status"] == s) for s in labels],
    name="After"
), row=2, col=2)

fig.update_layout(
    height=650,
    barmode="group",
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(orientation="h", y=1.02)
)

st.plotly_chart(fig, use_container_width=True)

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
# EXTRA ANALYSIS PLOTS (UNDER TABLES)
# =========================================================
st.subheader("Additional Analysis Metrics")

dmin_before = dfB["dmin"].values
dmin_after  = dfA["dmin"].values
delta_dmin  = dmin_after - dmin_before

pred_move = np.sqrt(
    (dfB["PredX"] - dfB["X"])**2 +
    (dfB["PredY"] - dfB["Y"])**2
)

# Plot 1: Predicted displacement
fig1 = go.Figure()
fig1.add_trace(go.Scatter(y=pred_move, mode="lines+markers"))
fig1.update_layout(title="Predicted Displacement", height=300)

# Plot 2: Δ dmin
fig2 = go.Figure()
fig2.add_trace(go.Bar(y=delta_dmin))
fig2.update_layout(title="Δ dmin", height=300)

# Plot 3: dmin Before vs After
fig3 = go.Figure()
fig3.add_trace(go.Scatter(y=dmin_before, mode="lines+markers", name="Before"))
fig3.add_trace(go.Scatter(y=dmin_after,  mode="lines+markers", name="After"))
fig3.update_layout(title="dmin Before vs After", height=300)

c3, c4, c5 = st.columns(3)
with c3: st.plotly_chart(fig1, use_container_width=True)
with c4: st.plotly_chart(fig2, use_container_width=True)
with c5: st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# AUTO REFRESH
# =========================================================
time.sleep(REFRESH_SEC)
st.rerun()
