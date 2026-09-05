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
    """Custom energy-vs-background detector from the project guide."""
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


# ==============================================================================
# CALIBRATION METHODOLOGY MODULE (Dynamic Comparison & Quasi-Static Syringe)
# ==============================================================================

def calculate_dynamic_calibration(ref_pressures: np.ndarray, dut_voltages: np.ndarray, frequencies: np.ndarray = None):
    """Calculate sensitivity (mV/Pa), linearity (R^2), and frequency response (Bode dB).
    
    Dynamic Comparison Method (0.5 - 20 Hz):
    V_DUT = S * Delta_P_ref + V_offset
    """
    p = np.asarray(ref_pressures, dtype=float)
    v = np.asarray(dut_voltages, dtype=float)
    if len(p) < 2 or len(v) < 2 or len(p) != len(v):
        return {
            "slope": 20.0, "intercept": 0.0, "r_squared": 1.0,
            "p_fit": p, "v_fit": v, "sensitivities": np.array([20.0]), "gain_db": np.array([0.0])
        }

    # Linear regression
    poly = np.polyfit(p, v, 1)
    slope = float(poly[0])        # Sensitivity in mV/Pa
    intercept = float(poly[1])    # Offset in mV
    
    v_pred = slope * p + intercept
    ss_res = np.sum((v - v_pred) ** 2)
    ss_tot = np.sum((v - np.mean(v)) ** 2)
    r_squared = float(1.0 - (ss_res / max(ss_tot, 1e-15)))
    r_squared = max(0.0, min(1.0, r_squared))

    p_sorted_idx = np.argsort(p)
    p_line = np.linspace(min(p), max(p), 100)
    v_line = slope * p_line + intercept

    # Frequency response if frequencies are supplied
    sensitivities = []
    gain_db = []
    if frequencies is not None and len(frequencies) == len(p):
        for p_i, v_i in zip(p, v):
            s_i = (v_i - intercept) / max(p_i, 1e-6)
            sensitivities.append(s_i)
            gain_db.append(20 * np.log10(max(s_i, 1e-6) / 20.0))
    else:
        sensitivities = [slope] * len(p)
        gain_db = [0.0] * len(p)

    return {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "p_fit": p_line,
        "v_fit": v_line,
        "sensitivities": np.array(sensitivities),
        "gain_db": np.array(gain_db)
    }


def calculate_syringe_decay(time_s: np.ndarray, voltage_mv: np.ndarray, delta_v_ml: float = 1.0, chamber_vol_ml: float = 100.0, atm_pressure_pa: float = 101325.0):
    """Quasi-Static Syringe Method (Boyle's Law for <0.1 Hz & Leak Time Constant):
    
    1. Applied Pressure Step: Delta_P0 = - P0 * (Delta_V / V0)
    2. Exponential Leak Decay: V(t) = V0 * exp(-t / tau) + V_offset
    3. Low Cutoff Frequency: f_low = 1 / (2 * pi * tau)
    """
    t = np.asarray(time_s, dtype=float)
    v = np.asarray(voltage_mv, dtype=float)
    
    # Calculate applied step using Boyle's Law (isothermal)
    delta_p0 = float(atm_pressure_pa * (delta_v_ml / max(chamber_vol_ml, 1e-3)))

    if len(t) < 5 or len(v) < 5:
        # Default nominal fallback
        tau = 18.0
        f_low = 1.0 / (2 * np.pi * tau)
        return {
            "delta_p0": delta_p0, "tau": tau, "f_low": f_low,
            "static_sensitivity": 20.0, "v_fit": v, "is_valid": False
        }

    t_norm = t - t[0]
    v_baseline = float(np.median(v[-int(len(v)*0.1):])) if len(v) >= 10 else float(v[-1])
    v_peak = float(np.max(np.abs(v - v_baseline)))
    v_rel = np.abs(v - v_baseline)

    # Fit exponential decay: ln(v_rel) = ln(v_0) - (1/tau) * t
    valid_mask = v_rel > max(0.05 * v_peak, 1e-3)
    if np.sum(valid_mask) >= 3:
        t_fit = t_norm[valid_mask]
        y_fit = np.log(v_rel[valid_mask])
        poly = np.polyfit(t_fit, y_fit, 1)
        decay_rate = -poly[0]
        tau = float(1.0 / max(decay_rate, 1e-4))
        v0_fit = float(np.exp(poly[1]))
    else:
        tau = 18.0
        v0_fit = v_peak

    tau = max(1.0, min(300.0, tau))
    f_low = float(1.0 / (2.0 * np.pi * tau))
    static_sensitivity = float(v0_fit / max(delta_p0, 1e-3))
    
    # Fitted curve
    v_fitted = v_baseline + np.sign(v[0] - v_baseline) * v0_fit * np.exp(-t_norm / tau)

    return {
        "delta_p0": delta_p0,
        "tau": tau,
        "f_low": f_low,
        "static_sensitivity": static_sensitivity,
        "v_fit": v_fitted,
        "is_valid": True
    }


def voltage_to_pressure(voltage_mv: float, sensitivity_mv_pa: float = 20.0, offset_mv: float = 0.0) -> float:
    """Convert raw sensor voltage (mV) to physical differential pressure (Pa)."""
    return float((voltage_mv - offset_mv) / max(sensitivity_mv_pa, 1e-6))

