import streamlit as st
from core.ui import inject_css, header

inject_css(); header()
st.markdown("## About SIH26144")
st.write("High-Sensitivity Microbarometer for low-frequency atmospheric pressure and infrasound monitoring.")

#st.markdown("## Dashboard Workflow")
st.markdown(
    '<h2 style="font-size:32px !important; margin-bottom:15px;">Dashboard Workflow</h2>',
    unsafe_allow_html=True
)
st.markdown('''<div class="workflow">
<div class="step">1. Acquire 100 Hz samples</div><div class="arrow">→</div>
<div class="step">2. SQLite / rolling buffer</div><div class="arrow">→</div>
<div class="step">3. Offset removal + detrend</div><div class="arrow">→</div>
<div class="step">4. FFT + Welch PSD</div><div class="arrow">→</div>
<div class="step">5. Spectrogram</div><div class="arrow">→</div>
<div class="step">6. SNR + event detection</div><div class="arrow">→</div>
<div class="step">7. Alert + event log</div>
</div>''',unsafe_allow_html=True)

st.markdown("## System Architecture")
st.markdown('''<div class="arch">PRESSURE / INFRASOUND
        ↓
MS5611 / DPS310
        ↓
INA333 + FILTER
        ↓
ADS1115 / ADS1220
        ↓
ESP32 — TIMER-BASED 100 Hz SAMPLING
        ↓ USB SERIAL
PYTHON / PYSERIAL
        ↓
SQLITE + ROLLING BUFFER
        ↓
PREPROCESSING
        ↓
NUMPY FFT + SCIPY WELCH PSD + SCIPY SPECTROGRAM
        ↓
SNR + NOISE FLOOR + DOMINANT FREQUENCY
        ↓
IN-BAND ENERGY / BACKGROUND EVENT DETECTION
        ↓
STREAMLIT
        ↓
LIVE DASHBOARD + ALERT BOARD + EVENT LOG</div>''',unsafe_allow_html=True)

st.markdown("## Data Source")
st.write("Current demonstration: recorded SQLite data at 100 Hz. Future hardware mode: ESP32 → USB Serial → Python → the same DSP and dashboard layers.")

