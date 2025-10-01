import streamlit as st
import pandas as pd
import requests
import datetime
import numpy as np
import os
from streamlit_autorefresh import st_autorefresh

from io import BytesIO

try:
    import qrcode
except ModuleNotFoundError:
    st.error("⚠️ qrcode module not installed. Add it to requirements.txt")

# --------------------------
# Auto-refresh every 5 minutes
# --------------------------
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=300000, key="datarefresh")  # 5 minutes

# --------------------------
# Page configuration
# --------------------------
st.set_page_config(
    page_title="Construction Site AQI Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏗 Construction Site AQI & Community Compliance")
st.markdown("**Quick info for site workers – Live AQI and Community Planning**")

# --------------------------
# Live AQI Section
# --------------------------
st.subheader("🌫 Live Air Quality")

token = os.getenv("WAQI_TOKEN", "demo")  
station_id = 14127
url = f"https://api.waqi.info/feed/@{station_id}/?token={token}"
resp = requests.get(url)

pm25, pm10 = None, None
if resp.status_code == 200:
    data = resp.json()
    if data["status"] == "ok":
        iaqi = data["data"]["iaqi"]
        pm25 = iaqi.get("pm25", {}).get("v", None)
        pm10 = iaqi.get("pm10", {}).get("v", None)

# --------------------------
# Color-coded AQI metrics
# --------------------------
def colored_metric(label, value, safe_limit):
    if value is None:
        st.markdown(f"**{label}: N/A**")
    elif value > safe_limit:
        st.markdown(f"<span style='color:red;font-size:22px'>{label}: {value} 🔥</span>", unsafe_allow_html=True)
    elif value > safe_limit * 0.5:
        st.markdown(f"<span style='color:orange;font-size:22px'>{label}: {value} ⚠️</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='color:green;font-size:22px'>{label}: {value} ✅</span>", unsafe_allow_html=True)

colored_metric("PM2.5 (µg/m³)", pm25, 60)
colored_metric("PM10 (µg/m³)", pm10, 100)

# --------------------------
# Historical AQI (persistent)
# --------------------------
st.subheader("📈 24h AQI Trend")

HISTORY_FILE = "aqi_history.csv"

# Load history from CSV
if os.path.exists(HISTORY_FILE):
    history = pd.read_csv(HISTORY_FILE, parse_dates=["time"])
else:
    history = pd.DataFrame(columns=["time", "pm25", "pm10"])

# Append new reading
now = datetime.datetime.now()
if pm25 is not None and pm10 is not None:
    new_row = pd.DataFrame([{"time": now, "pm25": pm25, "pm10": pm10}])
    history = pd.concat([history, new_row], ignore_index=True)
    history.to_csv(HISTORY_FILE, index=False)

# Keep only last 24 hours
recent = history[history["time"] > (now - pd.Timedelta(hours=24))]

if not recent.empty:
    st.line_chart(recent.set_index("time")[["pm25", "pm10"]])
else:
    st.info("Not enough data yet. Keep running the app.")

# --------------------------
# CPCB Guidelines
# --------------------------
st.subheader("📋 CPCB Guidelines")
cpcb_guidelines = pd.DataFrame({
    "Parameter": ["PM2.5", "PM10", "Noise", "Waste Management"],
    "CPCB Limit": ["60 µg/m³", "100 µg/m³", "75 dB", "No open dumping"],
    "Action Required": [
        "Water sprinkling, cover debris 💦",
        "Dust suppression, cover materials 🏗",
        "Wear ear protection 🦻",
        "Proper disposal 🗑️"
    ]
})
st.table(cpcb_guidelines)

# --------------------------
# Compliance Checklist
# --------------------------
st.subheader("✅ Site Compliance Checklist")
wheel_wash = st.checkbox("Wheel washing 🚿")
water_spray = st.checkbox("Water spraying 💦")
covering = st.checkbox("Covering debris/material 🏗")
waste_handling = st.checkbox("Waste handling 🗑️")
ppe = st.checkbox("PPE worn 🦺")

completed = sum([wheel_wash, water_spray, covering, waste_handling, ppe])
st.progress(completed / 5)

# --------------------------
# Mitigation Tips
# --------------------------
st.subheader("⚠️ Mitigation Tips")
if pm25 is not None:
    if pm25 > 60:
        st.warning("PM2.5 above limit! Water sprinkle & cover debris 💦🏗")
    elif pm25 > 30:
        st.info("Moderate PM2.5 – maintain dust control ⚠️")
    else:
        st.success("PM2.5 safe ✅")

if pm10 is not None:
    if pm10 > 100:
        st.warning("PM10 above limit! Increase dust suppression 🔥")
    elif pm10 > 50:
        st.info("Moderate PM10 – maintain dust control ⚠️")
    else:
        st.success("PM10 safe ✅")

# --------------------------
# Predicted AQI
# --------------------------
st.subheader("🔮 Predicted Next Hour AQI")
if not recent.empty:
    pm25_next = recent["pm25"].rolling(3).mean().iloc[-1]
    pm10_next = recent["pm10"].rolling(3).mean().iloc[-1]
    st.markdown(f"**Predicted PM2.5:** {pm25_next:.1f} µg/m³")
    st.markdown(f"**Predicted PM10:** {pm10_next:.1f} µg/m³")

# --------------------------
# Community Chat QR Code
# --------------------------
st.subheader("💬 Join the Community Chat")
community_url = os.getenv("COMMUNITY_URL", "https://t.me/clear_a1r")  
qr = qrcode.QRCode(box_size=8, border=2)
qr.add_data(community_url)
qr.make(fit=True)
img = qr.make_image(fill_color="blue", back_color="white")
buf = BytesIO()
img.save(buf)
st.image(buf.getvalue(), width=200)
st.markdown("Scan this QR code to join the community chat and plan clean-up events! 🚧")

