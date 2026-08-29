# SIH26144 Microbarometer Dashboard

Streamlit + Python + SQLite demonstration dashboard.

## Run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Demonstration

- 3,000 recorded samples at 100 Hz (30 seconds).
- Starts automatically once when the session loads.
- Stops at the end of the dataset; it does not loop.
- Use **Restart demonstration** to replay from sample 1.
- Pages: Live Dashboard, Signal Analysis, Events, System, Prototype, About.

## Hardware path

ESP32 → USB Serial → Python/PySerial → SQLite/rolling buffer → NumPy/SciPy DSP → Streamlit.

The current data source is recorded SQLite data; it is not presented as measured hardware data.
