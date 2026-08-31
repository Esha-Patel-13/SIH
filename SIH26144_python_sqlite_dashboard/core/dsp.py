import numpy as np
from scipy import signal, integrate

from .config import FS, TARGET_LOW_HZ, TARGET_HIGH_HZ


def preprocess(x: np.ndarray):
    """Project-guide DSP order: offset removal -> detrend -> band-pass."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return x
    x = x - np.mean(x)
    x = signal.detrend(x, type="linear")
    high = min(19.5, TARGET_HIGH_HZ)
    if x.size >= 300:
        sos = signal.butter(4, [0.05, high], btype="bandpass", fs=FS, output="sos")
        x = signal.sosfiltfilt(sos, x)
    return x


def fft(x: np.ndarray):
    if len(x) < 16:
        return np.array([]), np.array([])
    y = signal.detrend(x)
    window = np.hanning(len(y))
    spectrum = np.fft.rfft(y * window)
    freq = np.fft.rfftfreq(len(y), 1 / FS)
    mag = (2.0 / np.sum(window)) * np.abs(spectrum)
    mask = (freq >= TARGET_LOW_HZ) & (freq <= TARGET_HIGH_HZ)
    return freq[mask], mag[mask]


def welch_psd(x: np.ndarray):
    if len(x) < 128:
        return np.array([]), np.array([])
    y = signal.detrend(x)
    nperseg = min(1000, len(y))
    noverlap = nperseg // 2
    f, p = signal.welch(y, fs=FS, window="hann", nperseg=nperseg,
                        noverlap=noverlap, detrend="linear", scaling="density")
    mask = (f >= TARGET_LOW_HZ) & (f <= TARGET_HIGH_HZ)
    return f[mask], p[mask]


def spectrogram(x: np.ndarray):
    if len(x) < 256:
        return np.array([]), np.array([]), np.empty((0, 0))
    nperseg = min(256, len(x))
    f, t, sxx = signal.spectrogram(signal.detrend(x), fs=FS, window="hann",
                                   nperseg=nperseg, noverlap=int(nperseg * .75),
                                   scaling="density", mode="psd")
    mask = (f >= TARGET_LOW_HZ) & (f <= TARGET_HIGH_HZ)
    return f[mask], t, sxx[mask, :]


# <<< CHANGED: metrics() now derives dominant_frequency AND snr_db from the
# same PSD peak search, instead of computing SNR from a Savitzky-Golay time-
# domain residual that had no connection to the PSD the plots show.
def metrics(x: np.ndarray, f_psd: np.ndarray, p_psd: np.ndarray):
    if len(x) == 0:
        return {"rms": 0.0, "noise_rms": 0.0, "snr_db": 0.0,
                "noise_floor": 0.0, "dominant_frequency": None,
                "peak": 0.0, "inband_energy": 0.0}
    rms = float(np.sqrt(np.mean(x ** 2)))

    # <<< CHANGED: exclude near-DC bins below the bandpass's real low cutoff
    # (0.05 Hz) so a filter/detrend edge artifact can't be mislabeled as the
    # dominant frequency.
    F_MIN_VALID = 0.05
    dominant = None
    snr = 0.0
    floor = 0.0

    if len(p_psd) and len(f_psd):
        valid = f_psd >= F_MIN_VALID
        f_v = f_psd[valid] if np.any(valid) else f_psd
        p_v = p_psd[valid] if np.any(valid) else p_psd

        if len(p_v):
            peak_idx = int(np.argmax(p_v))
            dominant = float(f_v[peak_idx])
            peak_freq = dominant

            # <<< CHANGED: SNR is now signal-band power vs. noise-floor power,
            # both read straight from the Welch PSD (power ratio -> 10*log10,
            # not an amplitude ratio -> 20*log10).
            df = float(f_v[1] - f_v[0]) if len(f_v) > 1 else 0.1
            signal_bw = max(3 * df, 0.05)
            sig_mask = np.abs(f_v - peak_freq) <= signal_bw
            noise_mask = ~sig_mask

            if np.sum(sig_mask) > 1:
                signal_power = float(integrate.trapezoid(p_v[sig_mask], f_v[sig_mask]))
            else:
                signal_power = float(p_v[sig_mask][0]) * df

            noise_floor_density = float(np.median(p_v[noise_mask])) if np.any(noise_mask) else float(np.median(p_v))
            band_width = float(f_v[-1] - f_v[0]) if len(f_v) > 1 else df
            noise_power = max(noise_floor_density * band_width, 1e-15)

            snr = float(10 * np.log10(max(signal_power, 1e-15) / noise_power))
            floor = noise_floor_density

    # Kept as an auxiliary diagnostic value only — no longer feeds snr_db.
    if len(x) >= 101:
        smooth = signal.savgol_filter(x, 101, 2)
        noise = float(np.std(x - smooth))
    else:
        noise = float(np.std(x))

    energy = float(integrate.trapezoid(p_psd, f_psd)) if len(p_psd) else 0.0
    return {"rms": rms, "noise_rms": noise, "snr_db": snr,
            "noise_floor": floor, "dominant_frequency": dominant,
            "peak": float(np.max(np.abs(x))), "inband_energy": energy}


def detect_event(x: np.ndarray, baseline: np.ndarray, psd_f: np.ndarray,
                 psd_p: np.ndarray, threshold_db: float = 10.0):
    """Custom energy-vs-background detector from the project guide.
    Unchanged — already independent of the (formerly buggy) snr_db metric.
    """
    if len(x) < 300 or len(baseline) < 300 or len(psd_p) == 0:
        return {"status": "MONITORING", "ratio_db": 0.0}
    cur_energy = float(integrate.trapezoid(psd_p, psd_f))
    bf, bp = welch_psd(baseline)
    base_energy = float(integrate.trapezoid(bp, bf)) if len(bp) else 0.0
    ratio_db = 10 * np.log10(max(cur_energy, 1e-15) / max(base_energy, 1e-15))
    if ratio_db >= threshold_db:
        return {"status": "EVENT DETECTED", "ratio_db": float(ratio_db)}
    if ratio_db >= threshold_db * 0.6:
        return {"status": "HIGH ACTIVITY", "ratio_db": float(ratio_db)}
    return {"status": "NORMAL", "ratio_db": float(ratio_db)}
# import numpy as np
# from scipy import signal, integrate

# from .config import FS, TARGET_LOW_HZ, TARGET_HIGH_HZ


# def preprocess(x: np.ndarray):
#     """Project-guide DSP order: offset removal -> detrend -> band-pass."""
#     x = np.asarray(x, dtype=float)
#     if x.size == 0:
#         return x
#     x = x - np.mean(x)
#     x = signal.detrend(x, type="linear")
#     # A digital band-pass must be realizable with the 100 Hz sample rate.
#     # 0.01 Hz is intentionally not implemented as a short IIR cutoff here;
#     # the dashboard treats 0.01–20 Hz as the target measurement band.
#     high = min(19.5, TARGET_HIGH_HZ)
#     if x.size >= 300:
#         sos = signal.butter(4, [0.05, high], btype="bandpass", fs=FS, output="sos")
#         x = signal.sosfiltfilt(sos, x)
#     return x


# def fft(x: np.ndarray):
#     if len(x) < 16:
#         return np.array([]), np.array([])
#     y = signal.detrend(x)
#     window = np.hanning(len(y))
#     spectrum = np.fft.rfft(y * window)
#     freq = np.fft.rfftfreq(len(y), 1 / FS)
#     mag = (2.0 / np.sum(window)) * np.abs(spectrum)
#     mask = (freq >= TARGET_LOW_HZ) & (freq <= TARGET_HIGH_HZ)
#     return freq[mask], mag[mask]


# def welch_psd(x: np.ndarray):
#     if len(x) < 128:
#         return np.array([]), np.array([])
#     y = signal.detrend(x)
#     nperseg = min(1000, len(y))
#     noverlap = nperseg // 2
#     f, p = signal.welch(y, fs=FS, window="hann", nperseg=nperseg,
#                         noverlap=noverlap, detrend="linear", scaling="density")
#     mask = (f >= TARGET_LOW_HZ) & (f <= TARGET_HIGH_HZ)
#     return f[mask], p[mask]


# def spectrogram(x: np.ndarray):
#     if len(x) < 256:
#         return np.array([]), np.array([]), np.empty((0, 0))
#     nperseg = min(256, len(x))
#     f, t, sxx = signal.spectrogram(signal.detrend(x), fs=FS, window="hann",
#                                    nperseg=nperseg, noverlap=int(nperseg * .75),
#                                    scaling="density", mode="psd")
#     mask = (f >= TARGET_LOW_HZ) & (f <= TARGET_HIGH_HZ)
#     return f[mask], t, sxx[mask, :]


# def metrics(x: np.ndarray, f_psd: np.ndarray, p_psd: np.ndarray):
#     if len(x) == 0:
#         return {"rms": 0.0, "noise_rms": 0.0, "snr_db": 0.0,
#                 "noise_floor": 0.0, "dominant_frequency": None,
#                 "peak": 0.0, "inband_energy": 0.0}
#     rms = float(np.sqrt(np.mean(x ** 2)))
#     # Estimate noise as residual from a slowly varying trend.
#     if len(x) >= 101:
#         smooth = signal.savgol_filter(x, 101, 2)
#         noise = float(np.std(x - smooth))
#     else:
#         noise = float(np.std(x))
#     snr = float(20 * np.log10(max(rms, 1e-12) / max(noise, 1e-12)))
#     dominant = float(f_psd[int(np.argmax(p_psd))]) if len(p_psd) else None
#     floor = float(np.median(p_psd)) if len(p_psd) else 0.0
#     energy = float(integrate.trapezoid(p_psd, f_psd)) if len(p_psd) else 0.0
#     return {"rms": rms, "noise_rms": noise, "snr_db": snr,
#             "noise_floor": floor, "dominant_frequency": dominant,
#             "peak": float(np.max(np.abs(x))), "inband_energy": energy}


# def detect_event(x: np.ndarray, baseline: np.ndarray, psd_f: np.ndarray,
#                  psd_p: np.ndarray, threshold_db: float = 10.0):
#     """Custom energy-vs-background detector from the project guide.

#     A threshold is a demonstration setting until the team's measured quiet
#     background is characterized. No stored event flag is used to force the UI.
#     """
#     if len(x) < 300 or len(baseline) < 300 or len(psd_p) == 0:
#         return {"status": "MONITORING", "ratio_db": 0.0}
#     cur_energy = float(integrate.trapezoid(psd_p, psd_f))
#     bf, bp = welch_psd(baseline)
#     base_energy = float(integrate.trapezoid(bp, bf)) if len(bp) else 0.0
#     ratio_db = 10 * np.log10(max(cur_energy, 1e-15) / max(base_energy, 1e-15))
#     if ratio_db >= threshold_db:
#         return {"status": "EVENT DETECTED", "ratio_db": float(ratio_db)}
#     if ratio_db >= threshold_db * 0.6:
#         return {"status": "HIGH ACTIVITY", "ratio_db": float(ratio_db)}
#     return {"status": "NORMAL", "ratio_db": float(ratio_db)}
