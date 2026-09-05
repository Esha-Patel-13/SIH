import time
import numpy as np
import streamlit as st
from core.ui import inject_css, header, alert_board, metric_cards
from core.runtime import update_runtime
from core.config import FS, LIVE_WINDOW_SECONDS, UI_REFRESH_SECONDS
from core.plots import line_fig, spectrogram_fig

inject_css()
header()

@st.fragment(run_every=f"{UI_REFRESH_SECONDS}s")
def live():
    result = update_runtime()
    if result is None:
        st.warning("Waiting for recorded samples…")
        return
    
    rows, x_raw, a = result
    metrics = a["metrics"]
    det = a["det"]
    x = a["x"]
    t = np.arange(len(x)) / FS
    
    # 1. Alert Board & 8 Metric Cards (Original Content)
    alert_board(metrics, det)
    metric_cards(rows, x_raw, metrics, det)
    
    # 2. 4 Core Infrasound Graphs (2x2 Grid)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.pyplot(line_fig(t, x, "Pressure waveform", "Time (s)", "ΔP (Pa)", xlim=(max(0, t[-1] - LIVE_WINDOW_SECONDS), max(LIVE_WINDOW_SECONDS, t[-1]))), clear_figure=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.pyplot(line_fig(a["f_fft"], a["m_fft"], "FFT magnitude", "Frequency (Hz)", "Magnitude (Pa)", xlim=(0, 20)), clear_figure=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.pyplot(line_fig(a["f_psd"], a["p_psd"], "Welch power spectral density", "Frequency (Hz)", "Power (Pa²/Hz)", xlim=(0.01, 20), logy=True), clear_figure=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.pyplot(spectrogram_fig(a["sf"], a["stime"], a["sp"]), clear_figure=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    # 3. Environmental Telemetry (Temperature)
    with st.expander("🌡️ Environmental Telemetry (Temperature Stability & Thermal Drift)", expanded=False):
        tt = np.arange(len(rows)) / FS
        st.pyplot(line_fig(tt, np.array([r["temperature_c"] for r in rows]), "Ambient Temperature Stability", "Time (s)", "°C", xlim=(max(0, tt[-1] - LIVE_WINDOW_SECONDS), max(LIVE_WINDOW_SECONDS, tt[-1]))), clear_figure=True, use_container_width=True)
        
    if st.session_state.source.finished:
        st.success("Demonstration complete. Use Restart demonstration in the sidebar to replay.")

live()
