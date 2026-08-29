import time
import numpy as np
import streamlit as st
from .config import DB_PATH, FS, LIVE_WINDOW_SAMPLES, DSP_REFRESH_SECONDS, EVENT_THRESHOLD_DB
from .data_source import RecordedSQLiteSource
from .dsp import preprocess, fft, welch_psd, spectrogram, metrics, detect_event


def init_state():
    if "source" not in st.session_state:
        st.session_state.source = RecordedSQLiteSource(DB_PATH)
        st.session_state.source.start()
    if "buffer" not in st.session_state: st.session_state.buffer=[]
    if "baseline" not in st.session_state: st.session_state.baseline=None
    if "last_dsp" not in st.session_state: st.session_state.last_dsp=0.0
    if "analysis" not in st.session_state: st.session_state.analysis=None
    if "last_status" not in st.session_state: st.session_state.last_status="MONITORING"
    if "event_log" not in st.session_state: st.session_state.event_log=[]


def restart_demo():
    init_state()
    st.session_state.source.reset()
    st.session_state.source.start()
    st.session_state.buffer=[]
    st.session_state.baseline=None
    st.session_state.last_dsp=0.0
    st.session_state.analysis=None
    st.session_state.last_status="MONITORING"
    st.session_state.event_log=[]


def update_runtime():
    init_state()
    source=st.session_state.source
    incoming=source.pull_due_samples()
    if incoming:
        st.session_state.buffer.extend(incoming)
        st.session_state.buffer=st.session_state.buffer[-LIVE_WINDOW_SAMPLES:]
    rows=st.session_state.buffer
    if not rows:
        return None
    x_raw=np.array([r["filtered_pressure_pa"] for r in rows],dtype=float)
    x=preprocess(x_raw)
    now=time.monotonic()
    if st.session_state.analysis is None or now-st.session_state.last_dsp>=DSP_REFRESH_SECONDS or source.finished:
        f_fft,m_fft=fft(x); f_psd,p_psd=welch_psd(x); sf,stime,sp=spectrogram(x); met=metrics(x,f_psd,p_psd)
        if st.session_state.baseline is None and len(x)>=int(FS*5): st.session_state.baseline=x[:int(FS*5)].copy()
        detect_window=x[-int(FS*5):] if len(x)>=int(FS*5) else x
        detect_f,detect_p=welch_psd(detect_window)
        baseline=st.session_state.baseline if st.session_state.baseline is not None else x[:int(FS*5)]
        det=detect_event(detect_window,baseline,detect_f,detect_p,EVENT_THRESHOLD_DB)
        st.session_state.analysis={"x":x,"f_fft":f_fft,"m_fft":m_fft,"f_psd":f_psd,"p_psd":p_psd,"sf":sf,"stime":stime,"sp":sp,"metrics":met,"det":det}
        st.session_state.last_dsp=now
        if det["status"]!=st.session_state.last_status and det["status"] in ("EVENT DETECTED","HIGH ACTIVITY"):
            st.session_state.event_log.append({"time":time.strftime("%H:%M:%S"),"event":"Infrasound Event" if det["status"]=="EVENT DETECTED" else "High Activity","frequency_hz":met["dominant_frequency"],"amplitude_pa":met["peak"],"duration_s":5.0,"snr_db":met["snr_db"],"status":det["status"]})
        st.session_state.last_status=det["status"]
    return rows,x_raw,st.session_state.analysis
