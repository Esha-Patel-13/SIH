from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
DB_PATH = APP_DIR / "data" / "microbarometer.db"

# Project guide: practical proposed sampling rate for V1.
FS = 100.0
DT = 1.0 / FS
TARGET_LOW_HZ = 0.01
TARGET_HIGH_HZ = 20.0
LIVE_WINDOW_SECONDS = 20.0
LIVE_WINDOW_SAMPLES = int(FS * LIVE_WINDOW_SECONDS)
REPLAY_CHUNK_SAMPLES = 10          # 10 samples / 100 ms = exactly 100 samples/s
UI_REFRESH_SECONDS = 0.10
DSP_REFRESH_SECONDS = 0.50
EVENT_THRESHOLD_DB = 10.0          # demonstration threshold; must be validated from measured background
