import streamlit as st
import numpy as np

CSS = r"""
:root {
  --bg-app: #060c14;
  --bg-card: #091626;
  --bg-card-subtle: #0e1e33;
  --border-card: #162c45;
  --border-light: #203e61;
  --text-main: #f1f5f9;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --cyan: #00d2ff;
  --blue: #0ea5e9;
  --green: #10b981;
  --yellow: #f59e0b;
  --red: #ef4444;
  --purple: #8b5cf6;
}

.stApp {
  background-color: var(--bg-app);
  color: var(--text-main);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.block-container {
  padding-top: 0.8rem !important;
  padding-bottom: 1.5rem !important;
  max-width: 1550px !important;
}

[data-testid="stSidebar"] {
  background-color: #07101c;
  border-right: 1px solid var(--border-card);
}

/* Header Bar */
.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: linear-gradient(180deg, #0d1e34 0%, #091524 100%);
  border: 1px solid var(--border-card);
  border-radius: 8px;
  margin-bottom: 12px;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #00d2ff, #0284c7);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 16px;
  color: #03101c;
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.35);
}

.brand-title {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #ffffff;
  margin: 0;
  line-height: 1.2;
}

.brand-sub {
  font-size: 10px;
  color: var(--cyan);
  font-weight: 700;
  letter-spacing: 0.05em;
  margin: 0;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title-box {
  text-align: right;
}

.header-main-title {
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}

.header-main-sub {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  font-size: 11px;
  font-weight: 700;
  color: #34d399;
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

/* Alert Board */
.alert-board {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  border: 1px solid var(--border-card);
  border-radius: 8px;
  padding: 12px 16px;
  background: #091626;
  margin-bottom: 12px;
}

.alert-board.danger {
  border-color: rgba(239, 68, 68, 0.6);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, #091626 100%);
}

.alert-board.warn {
  border-color: rgba(245, 158, 11, 0.6);
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, #091626 100%);
}

.alert-icon {
  font-size: 24px;
}

.alert-title {
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.alert-message {
  color: var(--text-muted);
  font-size: 11px;
}

/* 8 Metric Cards */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
  margin-bottom: 14px;
}

.metric-card {
  background: #091626;
  border: 1px solid var(--border-card);
  border-radius: 6px;
  padding: 10px 10px 8px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 78px;
}

.metric-card:hover {
  border-color: var(--border-light);
}

.metric-card-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.metric-card-value {
  font-size: 16px;
  font-weight: 800;
  color: #ffffff;
  margin-top: 4px;
}

.chart-card {
  background: #091626;
  border: 1px solid var(--border-card);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
}

.arch {
  font-family: Consolas, monospace;
  white-space: pre-wrap;
  font-size: 12px;
  line-height: 1.55;
  background: #07131a;
  border: 1px solid var(--border-card);
  border-radius: 8px;
  padding: 16px;
  color: #c8d8df;
}

.workflow {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.step {
  border: 1px solid #162c45;
  border-radius: 6px;
  padding: 10px 12px;
  background: #091626;
  font-size: 14px !important;
  font-weight: 700;
  color: #f1f5f9;
}
"""

def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def header(source_label=None):
    chip_text = f"SYSTEM ONLINE • {source_label} • 100 Hz" if source_label else "SYSTEM ONLINE • 100 Hz"
    st.markdown(f"""
    <div class="top-header">
      <div class="brand-section">
        <div class="brand-logo">⬡</div>
        <div>
          <h1 class="brand-title">SIH26144</h1>
          <p class="brand-sub">HIGH-SENSITIVITY MICROBAROMETER</p>
        </div>
      </div>
      <div class="header-meta">
        <div class="header-title-box">
          <p class="header-main-title">Real-Time Infrasound Monitoring &amp; Signal Analysis</p>
          <p class="header-main-sub">Atmospheric pressure wave detection &amp; spectral characterization (0.01 – 20 Hz)</p>
        </div>
        <div class="status-chip">
          <span class="pulse-dot"></span>
          <span>{chip_text}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def alert_board(metrics, det):
    status = det["status"]
    cls = "danger" if status == "EVENT DETECTED" else "warn" if status == "HIGH ACTIVITY" else ""
    icon = "🚨" if status == "EVENT DETECTED" else "⚠" if status == "HIGH ACTIVITY" else "🛡"
    title = "INFRASOUND EVENT DETECTED" if status == "EVENT DETECTED" else "HIGH SIGNAL ACTIVITY" if status == "HIGH ACTIVITY" else "SYSTEM NORMAL"
    msg = "Threshold exceeded. Anomaly added to event log." if status == "EVENT DETECTED" else "Signal activity is elevated above baseline." if status == "HIGH ACTIVITY" else "Background ambient noise nominal."
    freq = "—" if metrics["dominant_frequency"] is None else f"{metrics['dominant_frequency']:.2f} Hz"
    
    st.markdown(f"""
    <div class="alert-board {cls}">
      <div style="display:flex;gap:14px;align-items:center">
        <div class="alert-icon">{icon}</div>
        <div>
          <div style="font-size:10px;font-weight:700;letter-spacing:0.08em;color:{'#ef4444' if status=='EVENT DETECTED' else '#f59e0b' if status=='HIGH ACTIVITY' else '#00d2ff'};">REAL-TIME ALERT</div>
          <div class="alert-title">{title}</div>
          <div class="alert-message">{msg}</div>
        </div>
      </div>
      <div style="display:flex;gap:20px;font-size:11px;text-align:right;">
        <div><span style="color:#94a3b8;">SNR</span><br><b style="color:#00d2ff;">{metrics['snr_db']:.1f} dB</b></div>
        <div><span style="color:#94a3b8;">DOMINANT PSD</span><br><b style="color:#ffffff;">{freq}</b></div>
        <div><span style="color:#94a3b8;">STATUS</span><br><b style="color:{'#ef4444' if status=='EVENT DETECTED' else '#f59e0b' if status=='HIGH ACTIVITY' else '#34d399'};">{status}</b></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def metric_cards(rows, x_raw, metrics, det):
    dom = "—" if metrics["dominant_frequency"] is None else f"{metrics['dominant_frequency']:.2f} Hz"
    temp = f"{rows[-1]['temperature_c']:.2f} °C" if rows else "25.0 °C"
    wind = f"{rows[-1]['wind_level']:.1f}" if rows else "4.0"
    
    vals = [
        ("CURRENT ΔP", f"{x_raw[-1]:.4f} Pa" if len(x_raw) else "0.0000 Pa", "#00d2ff"),
        ("RMS PRESSURE", f"{metrics['rms']:.4f} Pa", "#ffffff"),
        ("DOMINANT PSD", dom, "#00d2ff"),
        ("NOISE FLOOR", f"{metrics['noise_floor']:.2e}", "#94a3b8"),
        ("SNR", f"{metrics['snr_db']:.1f} dB", "#34d399"),
        ("TEMPERATURE", temp, "#f59e0b"),
        ("WIND LEVEL", wind, "#94a3b8"),
        ("EVENT STATUS", det["status"], "#ef4444" if det["status"]=="EVENT DETECTED" else "#f59e0b" if det["status"]=="HIGH ACTIVITY" else "#34d399"),
    ]
    
    cards_html = "".join([
        f'<div class="metric-card"><div class="metric-card-label">{label}</div><div class="metric-card-value" style="color:{color};">{val}</div></div>'
        for label, val, color in vals
    ])
    
    st.markdown(f'<div class="metric-grid">{cards_html}</div>', unsafe_allow_html=True)
