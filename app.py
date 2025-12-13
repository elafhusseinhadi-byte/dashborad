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

# ===== Compact layout =====
st.markdown("""
<style>
.block-container { padding-top: 0.2rem; padding-bottom: 0.3rem; }
h1, h2, h3 { margin-top: 0.2rem !important; margin-bottom: 0.3rem !important; }
.element-container { margin-top: 0.1rem; margin-bottom: 0.1rem; }
.stAlert { display: none; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.markdown("### UAV Real-Time Monitoring & Collision Avoidance Dashboard")

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
for i, s in enumerate(colors):
    d = dfB[dfB["Status"] == s]
    fig.add_trace(
        go.Scatter(
            x=d["X"], y=d["Y"],
            mode="markers",
            marker=dict(size=9, symbol="circle-open", color=colors[s]),
            name=f"BEFORE {s}",
            legendgroup="before",
            showlegend=True if i == 0 else False
        ),
        row=1, col=1
    )

# PREDICTION
valid = dfB["PredX"].notna()
fig.add_trace(
    go.Scatter(
        x=dfB[valid]["X"], y=dfB[valid]["Y"],
        mode="markers",
        marker=dict(size=8, symbol="circle-open", color="black"),
        name="Before",
        legendgroup="prediction",
        showlegend=True
    ),
    row=1, col=2
)

fig.add_trace(
    go.Scatter(
        x=dfB[valid]["PredX"], y=dfB[valid]["PredY"],
        mode="markers",
        marker=dict(size=9, symbol="circle-open", color="magenta"),
        name="Predicted",
        legendgroup="prediction",
        showlegend=True
    ),
    row=1, col=2
)

# AFTER
for i, s in enumerate(colors):
    d = dfA[dfA["Status"] == s]
    fig.add_trace(
        go.Scatter(
            x=d["X"], y=d["Y"],
            mode="markers",
            marker=dict(size=9, symbol="circle-open", color=colors[s]),
            name=f"AFTER {s}",
            legendgroup="after",
            showlegend=True if i == 0 else False
        ),
        row=2, col=1
    )

# HISTOGRAM
labels = list(colors.keys())
fig.add_trace(
    go.Bar(
        x=labels,
        y=[sum(dfB["Status"] == s) for s in labels],
        name="Before",
        legendgroup="hist",
        showlegend=True
    ),
    row=2, col=2
)

fig.add_trace(
    go.Bar(
        x=labels,
        y=[sum(dfA["Status"] == s) for s in labels],
        name="After",
        legendgroup="hist",
        showlegend=True
    ),
    row=2, col=2
)

fig.update_layout(
    height=620,
    barmode="group",
    margin=dict(l=20, r=160, t=30, b=20),
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.02,
        font=dict(size=11)
    )
)

st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TABLES
# =========================================================
st.subheader("RAW UAV DATA")
c1, c2 = st.columns(2)

with c1:
    st.markdown("**BEFORE**")
    st.dataframe(dfB, use_container_width=True, height=280)

with c2:
    st.markdown("**AFTER**")
    st.dataframe(dfA, use_container_width=True, height=280)

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

# Plot 1: Predicted displacement (scatter)
fig1 = go.Figure()
fig1.add_trace(go.Scatter(y=pred_move, mode="markers", marker=dict(size=6, color="blue")))
fig1.update_layout(
    title="Predicted Displacement",
    xaxis_title="UAV Index",
    yaxis_title="Predicted Displacement (km)",
    height=250,
    margin=dict(t=30)
)

# Plot 2: Δ dmin
fig2 = go.Figure()
fig2.add_trace(go.Bar(y=delta_dmin, marker_color="royalblue"))
fig2.update_layout(
    title="Δ dmin",
    xaxis_title="UAV Index",
    yaxis_title="Δ Minimum Distance (km)",
    height=250,
    margin=dict(t=30)
)

# Plot 3: dmin Before vs After
fig3 = go.Figure()
fig3.add_trace(go.Scatter(y=dmin_before, mode="lines+markers", name="Before"))
fig3.add_trace(go.Scatter(y=dmin_after,  mode="lines+markers", name="After"))
fig3.update_layout(
    title="dmin Before vs After",
    xaxis_title="UAV Index",
    yaxis_title="Minimum Distance (km)",
    height=250,
    margin=dict(t=30)
)

c3, c4, c5 = st.columns(3)
with c3: st.plotly_chart(fig1, use_container_width=True)
with c4: st.plotly_chart(fig2, use_container_width=True)
with c5: st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# AUTO REFRESH
# =========================================================
time.sleep(REFRESH_SEC)
st.rerun()
