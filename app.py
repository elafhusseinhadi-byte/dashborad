# =========================================================
# UAV MAP – BAGHDAD (FIXED)
# =========================================================
st.subheader("🗺️ Baghdad Airspace – UAV Positions")

# تأكيد القيم الصحيحة
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
        marker=dict(
            size=16,        # 👈 أكبر
            color=col,
            opacity=0.95
        ),
        text=d["UAV_ID"],
        hovertemplate=
            "<b>UAV ID:</b> %{text}<br>" +
            "<b>Lat:</b> %{lat}<br>" +
            "<b>Lon:</b> %{lon}<br>" +
            "<b>Status:</b> " + s +
            "<extra></extra>",
        name=s
    ))

map_fig.update_layout(
    mapbox=dict(
        style="carto-positron",
        center=dict(
            lat=33.3152,    # 📍 Baghdad ثابت
            lon=44.3661
        ),
        zoom=12
    ),
    height=480,
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", y=0.01)
)

st.plotly_chart(map_fig, use_container_width=True)
