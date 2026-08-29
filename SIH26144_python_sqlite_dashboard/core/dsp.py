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
    # A digital band-pass must be realizable with the 100 Hz sample rate.
    # 0.01 Hz is intentionally not implemented as a short IIR cutoff here;
    # the dashboard treats 0.01–20 Hz as the target measurement band.
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


def metrics(x: np.ndarray, f_psd: np.ndarray, p_psd: np.ndarray):
    if len(x) == 0:
        return {"rms": 0.0, "noise_rms": 0.0, "snr_db": 0.0,
                "noise_floor": 0.0, "dominant_frequency": None,
                "peak": 0.0, "inband_energy": 0.0}
    rms = float(np.sqrt(np.mean(x ** 2)))
    # Estimate noise as residual from a slowly varying trend.
    if len(x) >= 101:
        smooth = signal.savgol_filter(x, 101, 2)
        noise = float(np.std(x - smooth))
    else:
        noise = float(np.std(x))
    snr = float(20 * np.log10(max(rms, 1e-12) / max(noise, 1e-12)))
    dominant = float(f_psd[int(np.argmax(p_psd))]) if len(p_psd) else None
    floor = float(np.median(p_psd)) if len(p_psd) else 0.0
    energy = float(integrate.trapezoid(p_psd, f_psd)) if len(p_psd) else 0.0
    return {"rms": rms, "noise_rms": noise, "snr_db": snr,
            "noise_floor": floor, "dominant_frequency": dominant,
            "peak": float(np.max(np.abs(x))), "inband_energy": energy}


def detect_event(x: np.ndarray, baseline: np.ndarray, psd_f: np.ndarray,
                 psd_p: np.ndarray, threshold_db: float = 10.0):
    """Custom energy-vs-background detector from the project guide.

    A threshold is a demonstration setting until the team's measured quiet
    background is characterized. No stored event flag is used to force the UI.
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
