from pathlib import Path
import streamlit as st

CSS = r'''
:root{--ink:#dce9ef;--muted:#8fa7b3;--panel:#091720;--line:#1d3540;--teal:#55d8ca;--ok:#67e59a;--danger:#ff6673;--warn:#f0bd62}
.stApp{background:#061118;color:var(--ink)}
.block-container{padding-top:1rem;padding-bottom:1.5rem;max-width:1500px}
[data-testid="stSidebar"]{background:#08151c}
[data-testid="stSidebar"] .block-container{padding-top:1.2rem}
.hero{border:1px solid var(--line);border-radius:12px;padding:18px 22px;background:linear-gradient(145deg,#0b1a22,#071119);margin-bottom:12px}
.eyebrow{color:var(--teal);font-size:10px;font-weight:800;letter-spacing:.14em}
.hero h1{margin:5px 0 2px;font-size:27px}.hero p{margin:0;color:#91a9b5}
.status{color:var(--ok);font-weight:800}.badge{display:inline-block;border:1px solid #294a55;border-radius:99px;padding:3px 8px;color:#91cfc8;font-size:9px;margin-left:4px}
.alert-board{display:flex;justify-content:space-between;gap:16px;align-items:center;border:1px solid #24434c;border-radius:11px;padding:13px 16px;background:#0b1b22;margin-bottom:12px}
.alert-board.danger{border-color:#8b3e49;background:#231116}.alert-board.warn{border-color:#715b2d;background:#211b0d}
.alert-icon{font-size:25px}.alert-title{font-size:17px;font-weight:850}.alert-message{color:#9db0b9;font-size:11px}
.metric{border:1px solid var(--line);border-radius:9px;padding:11px 12px;background:var(--panel);min-height:78px}
.metric-label{color:#7f98a5;font-size:8px;letter-spacing:.11em;font-weight:800}.metric-value{font-size:19px;font-weight:800;margin-top:6px}.metric-help{color:#708a97;font-size:8px;margin-top:2px}
.card{border:1px solid var(--line);border-radius:10px;padding:13px 15px;background:var(--panel);margin-bottom:12px}
.section-title{font-size:16px;font-weight:800;margin:0 0 8px}.muted{color:var(--muted);font-size:11px}
.arch{font-family:Consolas,monospace;white-space:pre-wrap;font-size:12px;line-height:1.55;background:#07131a;border:1px solid var(--line);border-radius:10px;padding:16px;color:#c8d8df}
.workflow{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
.step{
    border:1px solid #294a55;
    border-radius:8px;
    padding:12px 14px;
    background:#0b1b22;
    font-size:16px !important;
    font-weight:700;
}
.small-note{color:#78909e;font-size:10px}
[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:9px}
[data-testid="stMetricLabel"]{color:#7f98a5}
.stButton>button{border:1px solid #31505b;background:#0b1b22;color:#dce9ef}
.stButton>button:hover{border-color:#55d8ca;color:#55d8ca}
.workflow .step {
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 12px 14px !important;
}
.workflow {
    gap: 10px !important;
}
@media(max-width:900px){.alert-board{align-items:flex-start;flex-direction:column}}
'''

def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

def header(source_label="RECORDED SQLITE"):
    st.markdown(f'''<div class="hero"><div class="eyebrow">SIH26144 • ENGINEERING PROTOTYPE</div>
<h1>HIGH-SENSITIVITY MICROBAROMETER</h1><p>Real-Time Infrasound Monitoring &amp; Signal Analysis</p>
<p style="margin-top:8px"><span class="status">● SYSTEM ONLINE</span><span class="badge">{source_label}</span><span class="badge">100 Hz / 10 ms</span></p></div>''', unsafe_allow_html=True)

def alert_board(metrics, det):
    status = det["status"]
    cls = "danger" if status == "EVENT DETECTED" else "warn" if status == "HIGH ACTIVITY" else ""
    icon = "⚠" if status != "NORMAL" else "✓"
    title = "INFRASOUND EVENT DETECTED" if status == "EVENT DETECTED" else "HIGH SIGNAL ACTIVITY" if status == "HIGH ACTIVITY" else "SYSTEM NORMAL"
    msg = "Threshold exceeded. Event added to the log." if status == "EVENT DETECTED" else "Signal activity is elevated." if status == "HIGH ACTIVITY" else "No significant event detected."
    freq = "—" if metrics["dominant_frequency"] is None else f'{metrics["dominant_frequency"]:.2f} Hz'
    st.markdown(f'''<div class="alert-board {cls}"><div style="display:flex;gap:14px;align-items:center"><div class="alert-icon">{icon}</div><div>
<div class="eyebrow">REAL-TIME ALERT</div><div class="alert-title">{title}</div><div class="alert-message">{msg}</div></div></div>
<div style="display:flex;gap:18px;font-size:10px"><div><span class="muted">SNR</span><br><b>{metrics["snr_db"]:.1f} dB</b></div><div><span class="muted">DOMINANT PSD</span><br><b>{freq}</b></div><div><span class="muted">STATUS</span><br><b>{status}</b></div></div></div>''', unsafe_allow_html=True)

def metric_cards(rows, x_raw, metrics, det):
    cols = st.columns(8)
    vals = [
        ("CURRENT ΔP", f"{x_raw[-1]:.4f} Pa"),
        ("RMS PRESSURE", f"{metrics['rms']:.4f} Pa"),
        ("DOMINANT PSD", "—" if metrics["dominant_frequency"] is None else f"{metrics['dominant_frequency']:.2f} Hz"),
        ("NOISE FLOOR", f"{metrics['noise_floor']:.3g}"),
        ("SNR", f"{metrics['snr_db']:.1f} dB"),
        ("TEMPERATURE", f"{rows[-1]['temperature_c']:.2f} °C"),
        ("WIND LEVEL", f"{rows[-1]['wind_level']:.1f}"),
        ("EVENT STATUS", det["status"]),
    ]
    for c,(label,value) in zip(cols,vals):
        c.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)
