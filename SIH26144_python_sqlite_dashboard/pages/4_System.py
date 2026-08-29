import streamlit as st
from core.ui import inject_css, header
from core.database import source_info
from core.config import DB_PATH, FS, TARGET_LOW_HZ, TARGET_HIGH_HZ

inject_css(); header()
info=source_info(DB_PATH)
st.markdown("## System Status")
c1,c2,c3,c4=st.columns(4)
c1.metric("Data source","Sample"); c2.metric("Sampling rate",f"{int(FS)} Hz"); c3.metric("Sample interval","10 ms"); c4.metric("Samples",info["count"])
st.markdown("## Signal Chain")
st.markdown('''<div class="arch">ATMOSPHERE / INFRASOUND
↓
PRESSURE INLET + WIND-NOISE REDUCTION
↓
REFERENCE CHAMBER
↓
MS5611 / DPS310
↓
INA333 + FILTER
↓
ADS1115 / ADS1220
↓
ESP32 · 100 Hz SAMPLING + TIMESTAMP
↓ USB SERIAL
PYTHON / PYSERIAL
↓
SQLITE + ROLLING BUFFER
↓
PREPROCESSING → FFT → WELCH PSD → SPECTROGRAM
↓
SNR + DOMINANT FREQUENCY + EVENT DETECTION
↓
STREAMLIT DASHBOARD → ALERT BOARD</div>''',unsafe_allow_html=True)
st.markdown("## Current Demonstration")
st.write(f"Target analysis band: {TARGET_LOW_HZ:g}–{TARGET_HIGH_HZ:g} Hz. Data source is recorded SQLite demonstration data; hardware values are not claimed as measured results.")
