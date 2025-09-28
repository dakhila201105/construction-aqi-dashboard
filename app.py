import streamlit as st
import pandas as pd
import requests
import datetime
import numpy as np
import qrcode
from io import BytesIO

st.set_page_config(page_title="Construction Site AQI & CPCB Compliance", layout="wide")
st.title("Construction Site Air Quality & CPCB Compliance")

# ---- Live AQI Section ----
st.subheader("Live AQI")

# Replace these with your station token/id
token = "44192d58f58d96613ec4baa6fc99637b2d33956f"
station_id = 14127  # Kokapet station index
url = f"https://api.waqi.info/feed/@{station_id}/?token={token}"

resp = requests.get(url)

pm25, pm10 = None, None
if resp.status_code == 200:
    data = resp.json()
    if data["status"] == "ok":
        iaqi = data["data"]["iaqi"]
        pm25 = iaqi.get("pm25", {}).get("v", None)
        pm10 = iaqi.get("pm10", {}).get("v", None)
    else:
        st.error("API returned error: " + str(data.get("data", "")))
else:
    st.error("Could not fetch AQ data.")

cols = st.columns(2)
with cols[0]:
    st.metric("PM2.5 (µg/m³)", pm25 if pm25 is not None else "N/A")
with cols[1]:
    st.metric("PM10 (µg/m³)", pm10 if pm10 is not None else "N/A")

# ---- History Tracking (CSV-based) ----
st.subheader("Last 24 Hours AQI Trend")

now = datetime.datetime.now()
new_row = {"time": now, "pm25": pm25, "pm10": pm10}
history_file = "aqi_history.csv"

try:
    df_history = pd.read_csv(history_file, parse_dates=["time"])
except FileNotFoundError:
    df_history = pd.DataFrame(columns=["time", "pm25", "pm10"])

# Append new data if valid
if pm25 is not None and pm10 is not None:
    df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
    df_history.to_csv(history_file, index=False)

# Filter last 24 hours
recent = df_history[df_history["time"] > (now - pd.Timedelta(hours=24))]
if not recent.empty:
    st.line_chart(recent.set_index("time")[["pm25", "pm10"]])
else:
    st.info("Not enough data collected yet. Keep the app running to build history.")

# ---- CPCB Compliance Checklist ----
st.subheader("CPCB Compliance Checklist")
wheel_wash = st.checkbox("Wheel washing done")
water_spray = st.checkbox("Water spraying done")
covering = st.checkbox("Covering debris/material")
waste_handling = st.checkbox("Waste handling managed")

# ---- Mitigation Tips ----
st.subheader("Mitigation Tips")
if pm25 is not None and pm25 > 60:
    st.warning("PM2.5 above CPCB limit — sprinkle water and cover materials.")
if pm10 is not None and pm10 > 100:
    st.warning("PM10 above CPCB limit — increase dust suppression measures.")

# ---- Community QR ----
st.subheader("Community QR Code")
dashboard_url = "http://localhost:8501"  # Change to your deployed Streamlit Cloud URL later
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=6,
    border=2,
)
qr.add_data(dashboard_url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
buf = BytesIO()
img.save(buf)
st.image(buf.getvalue(), caption="Scan to View Dashboard")
