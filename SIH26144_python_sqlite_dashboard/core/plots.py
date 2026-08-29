import matplotlib.pyplot as plt
import numpy as np


def line_fig(x, y, title, xlabel, ylabel, xlim=None, logy=False):
    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
    ax.plot(x, y, linewidth=1.0)
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(True, alpha=.22)
    if xlim: ax.set_xlim(*xlim)
    if logy: ax.set_yscale("log")
    fig.tight_layout()
    return fig


def spectrogram_fig(f, t, sxx):
    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
    if sxx.size:
        power_db = 10 * np.log10(np.maximum(sxx, 1e-16))
        ax.pcolormesh(t, f, power_db, shading="auto")
    ax.set_title("Live spectrogram", loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel("Time (s)", fontsize=9)
    ax.set_ylabel("Frequency (Hz)", fontsize=9)
    ax.set_ylim(0.01, 20)
    fig.tight_layout()
    return fig


def calibration_placeholder_fig():
    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
    ax.text(.5, .5, "NO MEASURED CALIBRATION DATA YET\nRun reference-pressure calibration before claiming sensitivity.",
            ha="center", va="center", fontsize=11)
    ax.set_axis_off()
    fig.tight_layout()
    return fig
