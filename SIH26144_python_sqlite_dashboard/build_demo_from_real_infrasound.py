import sqlite3
import sys
from pathlib import Path

import numpy as np
from scipy import integrate
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

sys.path.insert(0, r"C:\Users\ompat\Downloads\SIH-2026\Final\SIH26144_python_sqlite_dashboard")
from core.dsp import preprocess, welch_psd, metrics
from core.config import FS

WIN_S = 5.0          # length of each event/baseline window, seconds
MIN_SEP_S = 30.0     # minimum separation between chosen windows in the source recording
FETCH_MINUTES = 30   # how much real data to search through
TOTAL_S = 30.0       # length of the assembled demo, seconds (matches original demo)


def find_infrasound_channel(client, days_back=30):
    end = UTCDateTime()
    start = end - days_back * 86400
    inv = client.get_stations(channel="?DF", starttime=start, endtime=end,
                               level="response", matchtimeseries=True)
    for net in inv:
        for sta in net:
            for cha in sta:
                loc = cha.location_code or "--"
                return net.code, sta.code, loc, cha.code, inv
    raise RuntimeError(
        f"No currently-available public infrasound channel found in the "
        f"last {days_back} days -- try a larger days_back value."
    )


def fetch_real_trace(client):
    net, sta, loc, cha, inv = find_infrasound_channel(client)
    end = UTCDateTime()
    start = end - FETCH_MINUTES * 60
    loc_param = "" if loc == "--" else loc
    st = client.get_waveforms(net, sta, loc_param, cha, start, end)
    if not st:
        raise RuntimeError("No waveform data returned for that channel/window.")
    tr = st[0]
    source_id = f"{net}.{sta}.{loc}.{cha}"
    print(f"Pulled {tr.stats.npts} samples at {tr.stats.sampling_rate} Hz "
          f"from {source_id}, {tr.stats.starttime} to {tr.stats.endtime}")

    units_note = "raw counts (no calibration metadata available)"
    try:
        tr.remove_sensitivity(inv)
        units_note = "physical units via channel sensitivity (remove_sensitivity)"
    except Exception as e:
        print(f"remove_sensitivity failed ({e}); continuing with raw counts.")

    if tr.stats.sampling_rate != FS:
        tr.resample(FS)

    x = tr.data.astype(float)
    x = x - np.mean(x)
    return x, {
        "source_id": source_id,
        "network": net, "station": sta, "location": loc, "channel": cha,
        "fetch_start": str(start), "fetch_end": str(end),
        "units_note": units_note,
    }


def window_energy(x, fs, win_s):
    n = int(win_s * fs)
    out = []
    for start in range(0, len(x) - n, n // 2):
        seg = x[start:start + n]
        f, p = welch_psd(seg)
        e = float(integrate.trapezoid(p, f)) if len(p) else 0.0
        out.append((start, e))
    return out


def pick_windows(x, fs, win_s, n_events, min_sep_s):
    energies = window_energy(x, fs, win_s)
    events = []
    for start, e in sorted(energies, key=lambda z: -z[1]):
        if all(abs(start - c[0]) / fs >= min_sep_s for c in events):
            events.append((start, e))
        if len(events) == n_events:
            break
    if len(events) < n_events:
        raise RuntimeError(
            "Could not find two sufficiently separated active windows in the "
            "fetched recording -- try increasing FETCH_MINUTES."
        )
    ev_starts = [e[0] for e in events]
    candidates = [(s, e) for s, e in energies
                  if all(abs(s - es) / fs >= min_sep_s for es in ev_starts)]
    baseline = min(candidates, key=lambda z: z[1]) if candidates else energies[0]
    return events, baseline


def assemble_demo(x, fs, events, baseline, win_s):
    n = int(win_s * fs)
    b_start = baseline[0]
    e1_start, e2_start = events[0][0], events[1][0]

    def clip(start):
        return x[start:start + n].copy()

    baseline_seg = clip(b_start)
    event_a = clip(e1_start)
    event_b = clip(e2_start)

    pad_s = (TOTAL_S - 3 * win_s) / 4.0
    pad = np.tile(baseline_seg, int(np.ceil(pad_s * fs / n)) + 1)

    def take(seconds):
        m = int(seconds * fs)
        return pad[:m]

    parts = [take(pad_s), event_a, take(pad_s), event_b, take(pad_s + pad_s)]
    demo = np.concatenate(parts)
    n_total = int(TOTAL_S * fs)
    demo = demo[:n_total] if len(demo) >= n_total else np.pad(demo, (0, n_total - len(demo)))

    labels = np.zeros(n_total, dtype=int)
    idx = int(pad_s * fs)
    labels[idx:idx + len(event_a)] = 1
    idx2 = idx + len(event_a) + int(pad_s * fs)
    labels[idx2:idx2 + len(event_b)] = 2
    return demo, labels


def build_database(path: Path, demo, labels, fs, source_meta):
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""CREATE TABLE samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_ms INTEGER NOT NULL,
        pressure_pa REAL NOT NULL,
        temperature_c REAL NOT NULL,
        wind_level REAL NOT NULL,
        filtered_pressure_pa REAL NOT NULL,
        signal_pa REAL NOT NULL,
        wind_noise_pa REAL NOT NULL,
        event_flag INTEGER NOT NULL DEFAULT 0
    )""")
    c.execute("""CREATE TABLE events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_ms INTEGER NOT NULL,
        event TEXT NOT NULL,
        frequency_hz REAL,
        amplitude_pa REAL,
        duration_s REAL,
        snr_db REAL,
        status TEXT NOT NULL
    )""")

    x_filtered = preprocess(demo)
    baseline_mask = labels == 0
    baseline_trend = np.median(x_filtered[baseline_mask]) if baseline_mask.any() else 0.0
    signal_component = np.where(labels > 0, x_filtered - baseline_trend, 0.0)
    wind_component = x_filtered - signal_component

    t0_ms = int(1_700_000_000_000)
    temp_drift = 25.0 + 0.3 * np.sin(np.linspace(0, 2 * np.pi, len(demo)))
    wind_level = 3.0 + 0.5 * np.abs(np.sin(np.linspace(0, 4 * np.pi, len(demo))))

    rows = []
    for i in range(len(demo)):
        rows.append((
            t0_ms + int(i * 1000 / fs),
            float(demo[i]),
            float(temp_drift[i]),
            float(wind_level[i]),
            float(x_filtered[i]),
            float(signal_component[i]),
            float(wind_component[i]),
            1 if labels[i] > 0 else 0,
        ))
    c.executemany(
        "INSERT INTO samples (timestamp_ms, pressure_pa, temperature_c, "
        "wind_level, filtered_pressure_pa, signal_pa, wind_noise_pa, event_flag) "
        "VALUES (?,?,?,?,?,?,?,?)", rows
    )

    noise_rms = float(np.sqrt(np.mean(x_filtered[baseline_mask] ** 2))) if baseline_mask.any() else 1e-9

    for label_id, name in ((1, "Infrasound Event A"), (2, "Infrasound Event B")):
        mask = labels == label_id
        if not mask.any():
            continue
        idx = np.where(mask)[0]
        seg = x_filtered[idx]
        f_psd, p_psd = welch_psd(seg)
        met = metrics(seg, f_psd, p_psd)
        signal_rms = float(np.sqrt(np.mean(seg ** 2)))
        snr_db = float(20 * np.log10(max(signal_rms, 1e-12) / max(noise_rms, 1e-12)))
        c.execute(
            "INSERT INTO events (timestamp_ms, event, frequency_hz, "
            "amplitude_pa, duration_s, snr_db, status) VALUES (?,?,?,?,?,?,?)",
            (
                t0_ms + int(idx[0] * 1000 / fs),
                name,
                met["dominant_frequency"],
                met["peak"],
                len(idx) / fs,
                snr_db,
                "DETECTED",
            ),
        )

    conn.commit()
    conn.close()
    print(f"Wrote {len(demo)} samples and 2 events to {path}")


def write_source_note(path: Path, source_meta, events_info):
    path.write_text(f"""# Data source for microbarometer.db

This 30-second demo file is compiled from REAL recorded data, not fully synthetic:

- Source station: {source_meta['source_id']} (network {source_meta['network']}, station {source_meta['station']}), an IRIS/EarthScope (iris.edu) public FDSN data center station -- a university-consortium research network, publicly documented and independently verifiable via https://ds.iris.edu/mda/{source_meta['network']}/{source_meta['station']}/
- Real recording window fetched: {source_meta['fetch_start']} to {source_meta['fetch_end']}
- Units: {source_meta['units_note']}
- NOT CTBTO/IMS data: CTBTO's infrasound network requires a vDEC research contract and has no open API.

## How the 30-second demo was built
Three 5-second windows were selected from the real fetched recording: the two highest-energy, well-separated windows (labeled Event A and Event B below) and one clearly quiet window (baseline). These REAL excerpts were stitched into a 30-second timeline (baseline -> Event A -> baseline -> Event B -> baseline) for a demo of practical length. This is a time-compressed reel of real archived samples, not a live or continuous feed.

{events_info}

## Telemetry
- `temperature_c` and `wind_level`: smooth synthetic drift to populate telemetry cards.
- The `events` table's frequency_hz/amplitude_pa/snr_db values are computed by running this project's own core.dsp.metrics()/welch_psd() on the real extracted segments.
""")


def main():
    client = Client("IRIS")
    print("Searching IRIS for a public infrasound channel...")
    x, source_meta = fetch_real_trace(client)

    print("Scanning the real recording for two active windows + a baseline...")
    events, baseline = pick_windows(x, FS, WIN_S, n_events=2, min_sep_s=MIN_SEP_S)
    print(f"Event A at t={events[0][0]/FS:.1f}s (energy={events[0][1]:.4g})")
    print(f"Event B at t={events[1][0]/FS:.1f}s (energy={events[1][1]:.4g})")
    print(f"Baseline at t={baseline[0]/FS:.1f}s (energy={baseline[1]:.4g})")

    demo, labels = assemble_demo(x, FS, events, baseline, WIN_S)

    out_dir = Path(r"C:\Users\ompat\Downloads\SIH-2026\Final\SIH26144_python_sqlite_dashboard\data")
    out_dir.mkdir(exist_ok=True)
    db_path = out_dir / "microbarometer.db"
    build_database(db_path, demo, labels, FS, source_meta)

    events_info = (
        f"- Event A: real excerpt starting at t={events[0][0]/FS:.1f}s in the source recording\n"
        f"- Event B: real excerpt starting at t={events[1][0]/FS:.1f}s in the source recording\n"
        f"- Baseline: real excerpt starting at t={baseline[0]/FS:.1f}s in the source recording"
    )
    write_source_note(out_dir / "SOURCE.md", source_meta, events_info)
    print(f"Wrote {out_dir / 'SOURCE.md'}")


if __name__ == "__main__":
    main()
