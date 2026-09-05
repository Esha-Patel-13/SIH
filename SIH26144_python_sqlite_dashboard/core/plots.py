import matplotlib.pyplot as plt
import numpy as np


def _apply_dark_theme(fig, ax):
    fig.patch.set_facecolor("#091626")
    ax.set_facecolor("#07111e")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.25, color="#1e3a5f")
    ax.tick_params(colors="#94a3b8", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#162c45")
        spine.set_linewidth(1.0)


def line_fig(x, y, title, xlabel, ylabel, xlim=None, logy=False, hline=None, hline_label=None):
    fig, ax = plt.subplots(figsize=(7.5, 2.7), dpi=120)
    _apply_dark_theme(fig, ax)
    
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    
    if logy:
        valid_pos = y > 0
        x = x[valid_pos]
        y = y[valid_pos]

    if x.size and y.size:
        ax.plot(x, y, linewidth=1.3, color="#00d2ff")
    
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold", color="#ffffff")
    ax.set_xlabel(xlabel, fontsize=8, color="#94a3b8")
    ax.set_ylabel(ylabel, fontsize=8, color="#94a3b8")
    if xlim: ax.set_xlim(*xlim)
    if logy: ax.set_yscale("log")
    if hline is not None and np.isfinite(hline):
        ax.axhline(hline, color="#f59e0b", linestyle="--", linewidth=1.0, label=hline_label or "Threshold")
        ax.legend(loc="upper right", fontsize=7, facecolor="#091626", edgecolor="#162c45", labelcolor="#e2e8f0")
    fig.tight_layout()
    return fig


def spectrogram_fig(f, t, sxx):
    fig, ax = plt.subplots(figsize=(7.5, 2.7), dpi=120)
    _apply_dark_theme(fig, ax)
    
    if sxx.size:
        # Convert power spectral density to dB scale
        power_db = 10 * np.log10(np.maximum(sxx, 1e-16))
        finite = power_db[np.isfinite(power_db)]
        if finite.size:
            vmin, vmax = np.percentile(finite, 5), np.percentile(finite, 99.5)
        else:
            vmin, vmax = None, None
        ax.pcolormesh(t, f, power_db, shading="auto", cmap="plasma", vmin=vmin, vmax=vmax)
    
    ax.set_title("Live Spectrogram", loc="left", fontsize=10, fontweight="bold", color="#ffffff")
    ax.set_xlabel("Time (s)", fontsize=8, color="#94a3b8")
    ax.set_ylabel("Frequency (Hz)", fontsize=8, color="#94a3b8")
    ax.set_ylim(0.01, 20)
    fig.tight_layout()
    return fig
# def spectrogram_fig(f, t, sxx):
#     fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
#     if sxx.size:
#         power_db = 10 * np.log10(np.maximum(sxx, 1e-16))
#         finite = power_db[np.isfinite(power_db)]
#         if finite.size:
#             vmin, vmax = np.percentile(finite, 5), np.percentile(finite, 99.5)
#         else:
#             vmin, vmax = None, None
#         ax.pcolormesh(t, f, power_db, shading="auto", vmin=vmin, vmax=vmax)
#     ax.set_title("Live spectrogram", loc="left", fontsize=11, fontweight="bold")
#     ax.set_xlabel("Time (s)", fontsize=9)
#     ax.set_ylabel("Frequency (Hz)", fontsize=9)
#     ax.set_ylim(0.01, 20)
#     fig.tight_layout()
#     return fig


def calibration_curve_fig(p_ref, v_dut, p_fit, v_fit, slope, intercept, r_squared):
    fig, ax = plt.subplots(figsize=(7, 2.6), dpi=120)
    _apply_dark_theme(fig, ax)
    ax.scatter(p_ref, v_dut, color="#ef4444", s=35, zorder=4, label="Measured Points")
    ax.plot(p_fit, v_fit, color="#00d2ff", linewidth=1.6, label=f"Fit: V={slope:.2f}·ΔP+{intercept:.2f} (R²={r_squared:.4f})")
    ax.set_title("DYNAMIC CALIBRATION CURVE (0.5 – 20 Hz)", loc="left", fontsize=10, fontweight="bold", color="#ffffff")
    ax.set_xlabel("Ref Pressure ΔP (Pa)", fontsize=8, color="#94a3b8")
    ax.set_ylabel("Voltage (mV)", fontsize=8, color="#94a3b8")
    ax.legend(loc="upper left", fontsize=7, facecolor="#091626", edgecolor="#162c45", labelcolor="#e2e8f0")
    fig.tight_layout()
    return fig


def frequency_response_bode_fig(frequencies, gain_db, nominal_sensitivity=20.0):
    fig, ax = plt.subplots(figsize=(7, 2.6), dpi=120)
    _apply_dark_theme(fig, ax)
    ax.plot(frequencies, gain_db, marker="o", markersize=5, linewidth=1.5, color="#10b981", label="DUT Response")
    ax.axhline(0.0, color="#94a3b8", linestyle=":", linewidth=1.0)
    ax.axhline(1.0, color="#f59e0b", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.axhline(-1.0, color="#f59e0b", linestyle="--", linewidth=0.8, alpha=0.7, label="±1 dB Limits")
    ax.set_title("INFRASOUND PASSBAND (BODE MAGNITUDE)", loc="left", fontsize=10, fontweight="bold", color="#ffffff")
    ax.set_xlabel("Frequency (Hz)", fontsize=8, color="#94a3b8")
    ax.set_ylabel("Gain (dB)", fontsize=8, color="#94a3b8")
    ax.legend(loc="lower right", fontsize=7, facecolor="#091626", edgecolor="#162c45", labelcolor="#e2e8f0")
    fig.tight_layout()
    return fig


def syringe_decay_fig(t, v_measured, v_fitted, tau, f_low, delta_p0):
    fig, ax = plt.subplots(figsize=(7, 2.6), dpi=120)
    _apply_dark_theme(fig, ax)
    ax.plot(t, v_measured, color="#94a3b8", alpha=0.5, linewidth=0.9, label="Raw Step (mV)")
    ax.plot(t, v_fitted, color="#00d2ff", linewidth=1.8, label=f"Decay: τ={tau:.1f}s → f_low={f_low*1000:.1f}mHz")
    ax.set_title(f"QUASI-STATIC STEP DECAY (ΔP₀={delta_p0:.1f} Pa)", loc="left", fontsize=10, fontweight="bold", color="#ffffff")
    ax.set_xlabel("Time (s)", fontsize=8, color="#94a3b8")
    ax.set_ylabel("Voltage (mV)", fontsize=8, color="#94a3b8")
    ax.legend(loc="upper right", fontsize=7, facecolor="#091626", edgecolor="#162c45", labelcolor="#e2e8f0")
    fig.tight_layout()
    return fig


def calibration_placeholder_fig():
    fig, ax = plt.subplots(figsize=(7, 2.6), dpi=120)
    _apply_dark_theme(fig, ax)
    ax.text(0.5, 0.5, "NO MEASURED CALIBRATION DATA", ha="center", va="center", fontsize=10, color="#94a3b8")
    ax.set_axis_off()
    fig.tight_layout()
    return fig
