import numpy as np
import streamlit as st
from core.ui import inject_css, header
from core.runtime import update_runtime
from core.plots import line_fig, spectrogram_fig

inject_css(); header()
result=update_runtime()
if result is None: st.info("No samples available. Open Live Dashboard to start the demonstration.")
else:
    _,_,a=result; m=a["metrics"]
    c1,c2,c3=st.columns(3)
    c1.metric("Dominant PSD frequency", "—" if m["dominant_frequency"] is None else f'{m["dominant_frequency"]:.2f} Hz')
    c2.metric("SNR",f'{m["snr_db"]:.1f} dB'); c3.metric("In-band energy",f'{m["inband_energy"]:.4g}')
    c1,c2=st.columns(2)
    with c1: st.pyplot(line_fig(a["f_fft"],a["m_fft"],"FFT magnitude","Frequency (Hz)","Magnitude (Pa)",xlim=(0,20)),clear_figure=True,use_container_width=True)
    with c2: st.pyplot(line_fig(a["f_psd"],a["p_psd"],"Welch PSD","Frequency (Hz)","Power (Pa²/Hz)",xlim=(0.01,20),logy=True),clear_figure=True,use_container_width=True)
    st.pyplot(spectrogram_fig(a["sf"],a["stime"],a["sp"]),clear_figure=True,use_container_width=True)
