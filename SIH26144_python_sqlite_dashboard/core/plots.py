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


# <<< CHANGED: vmin/vmax are now set from percentiles of the frame's own
# dB values instead of being left to matplotlib's default global-min/max
# autoscale, so one strong early burst can no longer flatten the color scale
# for the rest of the window. Percentile-based (not a hardcoded dB range)
# so it still adapts if your absolute PSD levels change with a real sensor.
def spectrogram_fig(f, t, sxx):
    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
    if sxx.size:
        power_db = 10 * np.log10(np.maximum(sxx, 1e-16))
        finite = power_db[np.isfinite(power_db)]
        if finite.size:
            vmin, vmax = np.percentile(finite, 5), np.percentile(finite, 99.5)
        else:
            vmin, vmax = None, None
        ax.pcolormesh(t, f, power_db, shading="auto", vmin=vmin, vmax=vmax)
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
# import matplotlib.pyplot as plt
# import numpy as np


# def _finish(fig):
#     # Avoid tight_layout() because it can fail on Streamlit Cloud
#     # with some Matplotlib/font combinations.
#     fig.subplots_adjust(
#         left=0.10,
#         right=0.98,
#         bottom=0.20,
#         top=0.88
#     )
#     return fig


# def line_fig(
#     x,
#     y,
#     title,
#     xlabel,
#     ylabel,
#     xlim=None,
#     logy=False,
#     hline=None,
#     hline_label=None
# ):
#     fig, ax = plt.subplots(
#         figsize=(8, 3.2),
#         dpi=120
#     )

#     x = np.asarray(x, dtype=float)
#     y = np.asarray(y, dtype=float)

#     # Remove NaN and infinity values
#     valid = np.isfinite(x) & np.isfinite(y)
#     x = x[valid]
#     y = y[valid]

#     # Logarithmic PSD plots cannot contain zero/negative values
#     if logy:
#         valid = y > 0
#         x = x[valid]
#         y = y[valid]

#     if x.size > 0 and y.size > 0:
#         ax.plot(
#             x,
#             y,
#             linewidth=1.0
#         )

#     ax.set_title(
#         title,
#         loc="left",
#         fontsize=11,
#         fontweight="bold"
#     )

#     ax.set_xlabel(
#         xlabel,
#         fontsize=9
#     )

#     ax.set_ylabel(
#         ylabel,
#         fontsize=9
#     )

#     ax.grid(
#         True,
#         alpha=0.22
#     )

#     if xlim is not None:
#         ax.set_xlim(*xlim)

#     if logy:
#         ax.set_yscale("log")

#     # PSD noise-floor reference
#     if (
#         hline is not None
#         and np.isfinite(hline)
#         and hline > 0
#     ):
#         ax.axhline(
#             hline,
#             linestyle="--",
#             linewidth=1.0,
#             label=hline_label or "Background PSD floor"
#         )

#         if hline_label:
#             ax.legend(
#                 fontsize=8,
#                 loc="best"
#             )

#     return _finish(fig)


# def spectrogram_fig(f, t, sxx):
#     fig, ax = plt.subplots(
#         figsize=(8, 3.2),
#         dpi=120
#     )

#     f = np.asarray(f, dtype=float)
#     t = np.asarray(t, dtype=float)
#     sxx = np.asarray(sxx, dtype=float)

#     if (
#         sxx.size > 0
#         and f.size > 0
#         and t.size > 0
#     ):
#         # Prevent log10(0)
#         power_db = 10 * np.log10(
#             np.maximum(sxx, 1e-16)
#         )

#         ax.pcolormesh(
#             t,
#             f,
#             power_db,
#             shading="auto"
#         )

#     ax.set_title(
#         "Live spectrogram",
#         loc="left",
#         fontsize=11,
#         fontweight="bold"
#     )

#     ax.set_xlabel(
#         "Time (s)",
#         fontsize=9
#     )

#     ax.set_ylabel(
#         "Frequency (Hz)",
#         fontsize=9
#     )

#     ax.set_ylim(
#         0.01,
#         20
#     )

#     return _finish(fig)


# def calibration_placeholder_fig():
#     fig, ax = plt.subplots(
#         figsize=(8, 3.2),
#         dpi=120
#     )

#     ax.text(
#         0.5,
#         0.5,
#         "NO MEASURED CALIBRATION DATA YET\n"
#         "Run reference-pressure calibration before claiming sensitivity.",
#         ha="center",
#         va="center",
#         fontsize=11
#     )

#     ax.set_axis_off()

#     return _finish(fig)
# # import matplotlib.pyplot as plt
# # import numpy as np


# # def line_fig(x, y, title, xlabel, ylabel, xlim=None, logy=False):
# #     fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
# #     ax.plot(x, y, linewidth=1.0)
# #     ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
# #     ax.set_xlabel(xlabel, fontsize=9)
# #     ax.set_ylabel(ylabel, fontsize=9)
# #     ax.grid(True, alpha=.22)
# #     if xlim: ax.set_xlim(*xlim)
# #     if logy: ax.set_yscale("log")
# #     fig.tight_layout()
# #     return fig


# # def spectrogram_fig(f, t, sxx):
# #     fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
# #     if sxx.size:
# #         power_db = 10 * np.log10(np.maximum(sxx, 1e-16))
# #         ax.pcolormesh(t, f, power_db, shading="auto")
# #     ax.set_title("Live spectrogram", loc="left", fontsize=11, fontweight="bold")
# #     ax.set_xlabel("Time (s)", fontsize=9)
# #     ax.set_ylabel("Frequency (Hz)", fontsize=9)
# #     ax.set_ylim(0.01, 20)
# #     fig.tight_layout()
# #     return fig


# # def calibration_placeholder_fig():
# #     fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
# #     ax.text(.5, .5, "NO MEASURED CALIBRATION DATA YET\nRun reference-pressure calibration before claiming sensitivity.",
# #             ha="center", va="center", fontsize=11)
# #     ax.set_axis_off()
# #     fig.tight_layout()
# #     return fig
