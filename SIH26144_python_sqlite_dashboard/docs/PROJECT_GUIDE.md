# SIH26144 — High-Sensitivity Microbarometer
## Complete Engineering & Prototype Development Guide

**Team:** 5 ECE (3rd year) + 1 IT (3rd year)
**Problem statement:** SIH26144 — Design & Development of a High-Sensitivity Microbarometer Infrasound Sensor
**Sponsoring body:** National Technical Research Organisation (NTRO) · Track: Hardware · Prize: ₹1,00,000 · Portal: sih.gov.in

> **A note on sourcing, read this first:** The publicly available SIH26144 catalogue entry provides only the title, track (Hardware), theme, sponsor (NTRO), prize, and deadline — it does **not** include a detailed Background/Expected-Solution section (unlike many other SIH26xxx entries which do). Everywhere this guide states a number, frequency range, or target spec, it is labeled **[TARGET — our proposal]**, not an official NTRO requirement, unless explicitly marked **[OFFICIAL]**. Check with your SPOC / sih.gov.in login for any expanded description NTRO may release later.

---

## TABLE OF CONTENTS

1. Understand the Problem
2. What Exactly Are We Building?
3. How Pressure Becomes an Electrical Signal
4. Complete Signal Chain
5. Exact Components Required (BOM)
6. Mechanical Design
7. Electronics Design
8. Microcontroller Selection
9. Data Acquisition
10. DSP Overview
11. FFT
12. PSD
13. Creating Test Pressure Signals
14. Calibration
15. Complete Testing Plan
16. Wind-Noise Test
17. Temperature Compensation
18. Software Architecture
19. Team Division
20. Budget
21. What to Buy First
22. First 7 Days
23. 12-Week Roadmap
24. Failure Modes / Troubleshooting
25. Final SIH Demonstration
26. Final Specifications Table
27. Final Master Plan

---

## SECTION 1 — UNDERSTAND THE PROBLEM

**[OFFICIAL]** SIH26144 asks us to design and develop a high-sensitivity microbarometer infrasound sensor — a hardware track problem sponsored by NTRO.

**[our interpretation, plain language]**

- A **barometer** measures atmospheric pressure — the big, slow number (~101,325 Pa) that tells you if a storm is coming.
- A **microbarometer** measures **tiny, fast wiggles** on top of that number — changes as small as a fraction of a Pascal, happening over seconds.
- **Infrasound** is sound below 20 Hz — too low-pitched to hear, but real: volcanoes, explosions, storms, and meteors all create infrasound that travels as a pressure wave through the air.
- **What our device measures:** not the absolute pressure, but ΔP(t) — the pressure *fluctuation* over time, in a low-frequency band.
- **Final output:** a live pressure-fluctuation waveform, its frequency spectrum (FFT/PSD), and a flag/log when a fluctuation crosses a detection threshold — plus proof (via calibration and noise-floor measurement) that the sensor is actually sensitive and low-noise, not just "a barometer with a graph."

### Block diagram

```
ATMOSPHERE
   |
Pressure fluctuation (the real physical signal)
   |
Pressure inlet (physical opening/port)
   |
Wind-noise reduction (porous inlet / multi-port manifold)
   |
Pressure chamber (reference volume for differential sensing)
   |
Sensing element (transducer: pressure -> electrical parameter)
   |
Electrical signal (raw, weak, noisy)
   |
Analog front-end (amplify + filter)
   |
ADC (digitize)
   |
Microcontroller (sample, timestamp, stream)
   |
DSP (filter, detrend, window)
   |
FFT / PSD (time domain -> frequency domain)
   |
Infrasound detection (threshold/energy logic)
   |
Display / Storage (dashboard + database)
```

| Block | Why required |
|---|---|
| Pressure inlet | Physical entry point for the signal — must be small enough to avoid flow noise |
| Wind-noise reduction | Wind gusts create pressure noise orders of magnitude larger than our target signal — without this, the sensor mostly measures wind |
| Pressure chamber | Gives the sensor a stable reference so it responds to *changes*, not absolute drift |
| Sensing element | Converts a physical quantity (pressure) into something electrical we can measure |
| Analog front-end | The raw signal is often too small/noisy to digitize directly |
| ADC | Bridges analog world to digital world |
| MCU | Times and transports samples reliably |
| DSP/FFT/PSD | Extracts meaning — frequency content, noise floor, events — from raw numbers |
| Detection | Turns "always-on monitoring" into "here's an event" |
| Display/Storage | Lets a human (or a judge) see and verify what happened |

---

## SECTION 2 — WHAT EXACTLY ARE WE BUILDING?

### Physical architecture

```
                [ Wind-noise inlet (porous cap / multi-port) ]
                              |
                    [ Short PTFE/silicone tube ]
                              |
              +-----------------------------------+
              |     Sealed reference chamber       |
              |   (small rigid volume, ~50-200 mL)  |
              |                                     |
              |   [ Pressure sensor (MEMS) ]         |
              +-----------------------------------+
                              |
                     [ ribbon/wire leads ]
                              |
              +-----------------------------------+
              |   Electronics enclosure             |
              |  [ Amp -> Filter -> ADC -> MCU ]     |
              |  [ Temp/humidity sensor ]             |
              |  [ Voltage regulator ]                |
              +-----------------------------------+
                              |
                        USB cable
                              |
                       [ Laptop / PC ]
                 (Python: acquisition, DSP, dashboard)
```

1. **Mechanical system** — a small rigid enclosure housing the sensor + reference chamber, mounted to minimize vibration coupling from the table/ground.
2. **Pressure chamber** — an airtight small volume acting as the sensor's "quiet reference side," so the sensor responds to *changes* relative to it.
3. **Pressure inlet** — a narrow port connecting the chamber to open air.
4. **Wind-noise reduction** — a porous cap or multi-port manifold (a simple, well-known field technique) that averages out local wind gusts before they reach the inlet.
5. **Diaphragm/sensing element** — internal to the MEMS sensor package; we don't build this ourselves, we select a suitable off-the-shelf chip.
6. **Electrical sensing mechanism** — how the chip's internal displacement becomes a voltage/digital reading (Section 3).
7. **Analog electronics** — amplifier + filter stage between sensor and ADC.
8. **ADC** — external, higher resolution than the MCU's built-in ADC.
9. **Microcontroller** — ESP32 (recommended, see Section 8).
10. **Data storage** — SD card (on MCU side, optional) and/or SQLite/CSV on PC.
11. **PC/software** — Python-based acquisition, DSP, dashboard.
12. **Final enclosure** — weatherproof box for outdoor deployment, with the electronics separated from the pressure inlet only by the necessary tubing.

**What it should physically look like:** a fist-sized sealed chamber with a thin tube leading to a small weatherproof porous cap outside, wired to a small electronics box (about the size of a deck of cards) that connects via USB to a laptop. Not large, not delicate-looking — closer to a weather-station accessory than a lab instrument.

---

## SECTION 3 — HOW PRESSURE BECOMES AN ELECTRICAL SIGNAL

```
Atmospheric pressure fluctuation
        |
Mechanical displacement (a membrane/diaphragm flexes)
        |
Electrical change (capacitance, resistance, or reflected light changes)
        |
Voltage / digital output
```

### Comparison of transduction methods

| Method | Sensitivity | Noise | Low-freq capability | Cost | Complexity | Availability (India) | Student feasibility |
|---|---|---|---|---|---|---|---|
| Capacitive MEMS (e.g. in DPS310) | High | Low-moderate | Good | Low | Low (integrated chip) | Excellent | **High** |
| Piezoresistive MEMS (e.g. in MS5611, BMP390) | Moderate-high | Moderate | Good | Low | Low (integrated chip) | Excellent | **High** |
| Electromagnetic (moving-coil, like classic seismometers) | Very high | Very low | Excellent | High | High (custom build) | Poor (must fabricate) | Low |
| Optical/interferometric (as in research-grade microbarometers) | Extremely high | Extremely low | Excellent | Very high | Very high | Poor (specialized) | Very low |
| Electret-based | Moderate | Moderate-high | Moderate (AC-coupled, poor at very low f) | Low | Low | Moderate | Moderate |

### Recommended architecture: **Capacitive or piezoresistive MEMS sensor + external precision ADC + low-noise analog front-end**

**Why:** Optical/electromagnetic designs achieve the best raw performance but are not buildable by an undergraduate team in the available time with available lab tools — they need custom mechanical fabrication and precision optics/coils. MEMS-based capacitive/piezoresistive sensors are:
- Available off-the-shelf in India (Robu, Robocraze, etc.)
- Well-documented, I2C/SPI interfaced
- "Good enough" to demonstrate the complete measurement chain and a genuine noise-floor/sensitivity characterization — which is what actually proves the engineering claim in this problem statement

**This is explicitly not the same as "just use a BMP280 as a barometer."** We are using a MEMS pressure chip as a *component* inside a proper instrumentation chain (reference chamber + low-noise amp + filtering + external ADC + rigorous noise-floor characterization) — the difference between "a weather sensor" and "a microbarometer" is the surrounding system and the validation, not just the chip.

---

## SECTION 4 — COMPLETE SIGNAL CHAIN

| Block | Input | Output | Purpose | Why required | Typical specs to look for | Possible problems |
|---|---|---|---|---|---|---|
| Transducer | Pressure (Pa) | Analog electrical signal | Convert physical→electrical | Core sensing | Resolution (Pa), noise (Pa/√Hz or LSB-equivalent) | Wrong range selection wastes resolution |
| Amplifier | µV–mV signal | 100s of mV–V | Boost weak signal | ADC/downstream noise floor otherwise dominates | Input-referred noise (nV/√Hz), gain, CMRR | General-purpose op-amp adds too much noise |
| Filter | Full-band amplified signal | Band-limited signal | Remove drift + prevent aliasing | Protects the frequency band of interest | Cutoffs matched to ~0.01–20 Hz **[TARGET]** | Wrong cutoffs distort real signal |
| ADC | Filtered analog | Digital samples | Digitize | Needed for any DSP | Resolution (bits), ENOB, sample rate | Using MCU's noisy internal ADC |
| MCU | ADC samples | Timestamped digital stream | Reliable acquisition + transport | Needed to get data to PC | Timing jitter, buffer size | Irregular sampling corrupts FFT |
| DSP | Raw digital stream | Cleaned signal | Remove offset/drift/noise | Prepares for analysis | — | Wrong processing order |
| FFT | Time-domain window | Frequency spectrum | Identify frequency content | Core analysis tool | Window length, function | No windowing → leakage |
| PSD | Time series | Power vs frequency | Quantify noise floor properly | Needed to prove "low noise" claim | Welch's method, segment length | Confusing FFT amplitude with PSD scaling |
| Detection | PSD/spectrogram | Event flag | Turn monitoring into alerts | Practical usability | Threshold from measured background | Guessing thresholds instead of measuring them |

---

## SECTION 5 — EXACT COMPONENTS REQUIRED (BOM)

**Legend:** ⚠️ = DO NOT BUY YET — test the previous stage first.

### A. Mechanical components

| Component | Model/spec | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Sealed reference chamber | Small airtight container (e.g. a repurposed metal tin, or 3D-printed sealed box) | 1 | Reference volume for differential sensing | ~50–200 mL, airtight | ₹0–300 (DIY/3D print) | Essential | Repurposed food tin with epoxy-sealed ports |
| Silicone/PTFE tubing | 2–4 mm ID | 0.5 m | Connects inlet to chamber | Flexible, airtight | ₹50–150 | Essential | Aquarium airline tubing |
| Porous wind cap | DIY foam or multi-port manifold | 1 | Wind-noise reduction | Multiple small holes/porous foam | ₹0–100 (DIY) | Recommended | Open-cell foam plug |

### B. Sensing element

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| MEMS pressure sensor | **MS5611** (24-bit ADC built in, I2C/SPI) | 1 | Primary sensing element for testing | ~10 cm-equivalent resolution, ±1.5 mbar accuracy | ₹350–500 | Essential (first buy) | DPS310, BMP390 |
| Alternative MEMS sensor | **DPS310** | 1 | Comparison/backup | Very low noise per datasheet, I2C/SPI | ₹250–400 | Optional (buy after testing MS5611) | BMP390 |

### C. Analog electronics

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Low-noise instrumentation amp | **INA333** (or INA128) | 1 | Amplify raw sensor signal | Input noise ~50 nV/√Hz (INA333), rail-to-rail | ₹250–450 | ⚠️ DO NOT BUY YET — first test raw sensor noise floor | INA128 (lower noise, higher cost) |
| Precision resistors (1%, metal film) | Assorted 1kΩ–1MΩ | ~15 | Gain-setting, filter design | 1% tolerance | ₹50–100 total | Essential once amp stage is built | — |
| Film capacitors | Assorted nF–µF | ~10 | Filter design | Low-ESR film type | ₹50–100 total | Essential once filter stage is built | — |

### D. Op-amps/amplifiers (if a second stage or buffer is needed)

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| General-purpose low-noise op-amp | **OPA2277** or **TL072** (for buffering/filter stages) | 1–2 | Active filter stages | Low offset, low noise | ₹80–200 | Optional (design-dependent) | LM358 (noisier, cheaper fallback) |

### E. ADC

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| 16-bit external ADC | **ADS1115** | 1 | Better resolution than MCU ADC | 16-bit, I2C, ~860 SPS max | ₹250–450 | Recommended for V1 | — |
| 24-bit external ADC | **ADS1220** or **ADS1262** | 1 | High-resolution upgrade path | 24-bit, SPI, very low noise | ₹700–2,500 | ⚠️ DO NOT BUY YET — only if ADS1115 proves insufficient | ADS1262 (higher performance, higher cost) |

### F. Microcontroller

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| MCU dev board | **ESP32 DevKit (WROOM-32)** | 1 | Sampling, timestamping, streaming | Dual-core, Wi-Fi, I2C/SPI, USB | ₹350–600 | Essential | STM32 Blue Pill/Nucleo (if team prefers STM32 toolchain) |

### G. Temperature sensor

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Temp/humidity sensor | **SHT31** | 1 | Compensation + logging | ±0.3°C accuracy, I2C | ₹200–400 | Recommended | DHT22 (cheaper, slower, less accurate) |

### H. Humidity sensor

*(Covered by SHT31 above — a separate humidity-only sensor is not needed.)*

### I. SD card/storage

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| microSD module + card | Standard SPI microSD breakout, 8–16 GB card | 1 | Onboard backup logging (optional) | SPI interface | ₹150–300 | Optional (PC logging is primary) | Log only to PC via SQLite |

### J. Power supply

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Low-noise linear regulator | **LP2985** or low-noise AMS1117 variant | 1–2 | Clean analog supply rail | Low output noise | ₹50–150 | Essential once analog stage is added | — |
| USB power source | Power bank or bench PSU, 5V | 1 | Powers whole system | Stable 5V | ₹500–1,000 | Essential | Existing lab bench supply |

### K. PCB

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Perfboard (prototyping) | Standard | 1–2 | Move off breadboard | — | ₹50–150 | Recommended | Breadboard only (V1) |
| Custom PCB (later revision) | 2-layer, JLCPCB/local fab | 5 boards | Clean, repeatable, lower-noise layout | — | ₹500–1,500 (batch) | Optional (V2/V3) | Perfboard |

### L. Connectors

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Jumper wires, headers | Standard | set | Prototyping | — | ₹150–300 | Essential | — |

### M. Pressure chamber materials

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Epoxy/sealant | Standard 2-part epoxy | 1 tube | Airtight seals for chamber ports | — | ₹100–200 | Essential | Hot glue (less reliable seal) |

### N. Wind-noise reduction materials

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Open-cell foam | Standard packaging foam | small piece | Porous wind filter | — | ₹0–50 | Recommended | — |

### O. Testing/calibration equipment

| Component | Model | Qty | Purpose | Specs | Approx INR | Essential/Optional | Alternative |
|---|---|---|---|---|---|---|---|
| Reference pressure source | Syringe + tube, or small speaker-driven chamber | 1 | Generate known controlled pressure changes | DIY | ₹0–300 | Essential | — |
| Reference instrument | College lab precision manometer/barometer | — | Cross-validation | Borrow | Borrow | Good to have | — |
| Oscilloscope | College lab | — | Verify analog stage behavior | Borrow | Borrow | Good to have | — |
| Function generator | College lab | — | Drive speaker-based test chamber at known frequency | Borrow | Borrow | Good to have | — |

**Component notes/sources:** Datasheet-level claims above (MS5611 24-bit internal ADC, DPS310 low-noise reputation, INA333 ~50 nV/√Hz input noise, ADS1115/ADS1220 resolution figures) reflect standard, well-documented specifications from these chips' manufacturer datasheets (TE Connectivity/MEAS for MS5611, Infineon for DPS310, Texas Instruments for INA333/ADS1115/ADS1220). Verify current pricing/availability on Robu.in, Robocraze, or your local electronics market before purchase, as prices fluctuate.

---

## SECTION 6 — MECHANICAL DESIGN

> **INITIAL DESIGN — MUST BE EXPERIMENTALLY OPTIMIZED.**

```
        [ Porous wind cap ]
               |
        [ Inlet tube: ~3 mm ID, ~10-15 cm length ]  <- INITIAL, TUNE LATER
               |
     +-------------------------+
     |   Reference chamber      |
     |   ~100 mL (INITIAL)       |
     |                           |
     |   [ MEMS sensor mounted    |
     |     on chamber wall ]      |
     +-------------------------+
```

- **Chamber volume:** larger volume = lower sensitivity to fast changes but more thermal stability; smaller volume = more sensitive but more prone to leaks/thermal noise. **Start at ~100 mL, adjust based on measured response.**
- **Tube diameter/length:** narrow, long tubes add acoustic resistance (can filter high frequencies, which may help or hurt depending on target band) — must be tuned once we know actual sensor bandwidth.
- **Leakage:** even a tiny leak in the chamber ruins low-frequency response (the whole point is a sealed reference) — test with soap-water bubble check before proceeding.
- **Diaphragm size/thickness:** internal to the MEMS chip — not something we design, but it's why chip selection matters.
- **Mechanical resonance:** avoid mounting the sensor rigidly to a vibrating surface (like directly on a desk near equipment) — isolate with foam/rubber standoffs.

---

## SECTION 7 — ELECTRONICS DESIGN

### Conceptual circuit

```
[MEMS sensor] --raw signal--> [INA333 instrumentation amp] --> [RC high-pass] --> [RC low-pass] --> [ADS1115] --> [ESP32]
```

### Practical circuit considerations

- **Gain:** set based on measured raw sensor output amplitude vs. ADC full-scale range — do not fix a gain value before measuring Stage 1 output. **[to be determined experimentally]**
- **Resistor/capacitor values for filters:** cutoff frequency `fc = 1/(2πRC)`. For a high-pass cutoff near 0.01 Hz **[TARGET]**, you need fairly large R and C values (e.g., R=1MΩ, C=15µF gives fc ≈ 0.0106 Hz) — verify with actual component tolerances.
- **Supply voltage:** 3.3V (matches ESP32 logic level) with a clean, separate linear-regulated rail for the analog front-end — do not share this rail directly with digital switching noise from the MCU.
- **Expected signal range:** depends on measured sensor output — establish this from Day 4–5 bench testing before finalizing gain.
- **ADC resolution:** ADS1115 gives 16-bit resolution across its selected input range — confirm this maps usefully onto your amplified signal's expected swing.
- **Noise considerations:** keep analog wiring short, use twisted-pair or shielded cable from sensor to amp, and separate analog ground from digital ground where possible (star grounding).

**We deliberately do not give you final R/C numbers yet** — per the engineering rules, filter cutoffs must follow from the *measured* target frequency band and *measured* raw sensor bandwidth, not be assumed in advance.

---

## SECTION 8 — MICROCONTROLLER

| Feature | ESP32 | STM32 (Blue Pill/Nucleo) | Arduino Uno/Nano | Raspberry Pi Pico |
|---|---|---|---|---|
| ADC/interface | Internal ADC noisy; good I2C/SPI for external ADC | Internal ADC decent; good I2C/SPI | Internal ADC 10-bit, basic | Internal ADC 12-bit; good I2C/SPI |
| Processing capability | Dual-core, decent for light DSP | Strong, real-time capable | Weak | Dual-core, decent |
| Power | Moderate (Wi-Fi draws more) | Low | Low | Low |
| Sampling capability | Good with external ADC via I2C/SPI | Very good, precise timers | Limited | Good |
| Software support | Arduino IDE/PlatformIO, huge community | STM32Cube/PlatformIO, steeper learning curve | Easiest, most beginner-friendly | Good, growing community |
| Cost | ₹350–600 | ₹300–700 | ₹250–400 | ₹300–500 |
| Availability (India) | Excellent | Good | Excellent | Good |
| Suitability for this project | **Recommended** | Good alternative if team knows it | Not recommended (too weak) | Viable alternative |

**Recommendation: ESP32.** It balances ease of use, community support (critical for a beginner team), sufficient processing for streaming + light real-time filtering, and built-in Wi-Fi for later dashboard/remote-monitoring upgrades.

**Exact MCU job:**
```
Initialize I2C/SPI to ADC and sensors
   |
Set fixed sampling interval (timer-based, not loop-based, to avoid jitter)
   |
Read ADC sample
   |
Attach timestamp
   |
Package into a simple binary or CSV-line packet
   |
Send over USB serial to PC
   |
Repeat
```
The MCU should **not** attempt FFT/PSD itself for V1 — stream raw timestamped data to the PC and do all DSP there in Python. This keeps the embedded side simple and reliable, and keeps the DSP flexible for iteration.

---

## SECTION 9 — DATA ACQUISITION

- **Sampling rate:** for a target band of 0.01–20 Hz **[TARGET]**, Nyquist requires fs > 40 Hz — but to have comfortable margin for filtering and to safely allow future upward revision of the band, a practical target is **fs = 100 Hz**. **[our proposal, to be validated]**
- **Sampling interval:** 1/100 Hz = 10 ms per sample.
- **ADC resolution:** 16-bit (ADS1115) for V1 gives 65,536 levels across the selected input range — sufficient to start; 24-bit is an upgrade path if noise-floor testing shows we need more headroom.
- **Data format example (CSV row):** `timestamp_ms, raw_adc_value, temperature_C`
- **Timestamping:** use the MCU's internal timer, not "time since last sample" measured in the loop (accumulates drift/jitter).
- **Storage:** stream to PC in real time, write incrementally to CSV or SQLite — do not buffer everything in RAM before writing.

**Example — data volume estimate:** at fs=100 Hz, 3 bytes/sample (raw value) + 4 bytes (timestamp) ≈ 7 bytes/sample → 700 bytes/sec → ~2.5 MB/hour → ~60 MB/day. Very manageable on any laptop.

---

## SECTION 10 — DSP (BEGINNER LEVEL)

```
RAW DATA
   |
Offset removal (subtract mean, or subtract long-term rolling average)
   |
Detrending (remove slow linear/polynomial drift)
   |
Filtering (band-pass to target infrasound range)
   |
Windowing (taper edges before FFT, e.g. Hann window)
   |
FFT
   |
PSD
   |
Detection (compare energy-in-band against measured background)
```

- **Offset removal:** raw pressure sits around ~101,325 Pa — if you FFT that directly, the huge DC component swamps everything; always remove it first.
- **Detrending:** slow drift (temperature, very slow real atmospheric change) isn't the fast infrasound signal we want — remove it so it doesn't distort the spectrum.
- **Filtering:** isolates our band of interest, reduces both very slow drift and very fast noise.
- **Windowing:** prevents "spectral leakage" — sudden edges in a finite time segment otherwise smear frequency content across bins.

---

## SECTION 11 — FFT

**FFT (Fast Fourier Transform)** converts a time-domain signal into its frequency-domain representation — it tells you *which frequencies are present and how strong they are*, instead of just showing amplitude vs. time.

- Sampling frequency: `Fs` (samples per second)
- Number of samples in the analysis window: `N`
- **Frequency resolution:** `Δf = Fs / N`

**Numerical example:** if `Fs = 100 Hz` and we take `N = 1000` samples (10 seconds of data), then `Δf = 100/1000 = 0.1 Hz`. This means the FFT can distinguish frequency components that are at least 0.1 Hz apart. If we need finer resolution near 0.01 Hz, we need a longer window (more samples) — e.g., `N = 10,000` (100 seconds) gives `Δf = 0.01 Hz`.

**Reading the FFT graph:** x-axis is frequency (Hz), y-axis is amplitude/magnitude. A peak at a particular frequency means a real oscillation at that frequency is present in the signal — e.g., a peak at 2 Hz means something is fluctuating the pressure roughly twice per second.

**FFT ≠ DSP.** FFT is one specific tool (a way of viewing frequency content). DSP is the overall discipline — filtering, detrending, windowing, detection logic, PSD, spectrograms — of which FFT is just one part.

---

## SECTION 12 — PSD

**PSD (Power Spectral Density)** shows how the signal's *power* (not just raw amplitude) is distributed across frequency — normalized per unit bandwidth (e.g., units of Pa²/Hz).

- **Why better than raw FFT for noise analysis:** a single FFT snapshot is noisy and depends on exact window choice; PSD (typically computed via Welch's method — averaging multiple overlapping windows) gives a much more stable, statistically meaningful estimate of where the sensor's noise "lives" in frequency.
- **Identifying persistent components:** a real, ongoing noise source (like mains hum at 50 Hz, or a constant mechanical vibration) shows up as a stable, repeatable peak across many averaged PSD estimates — while a one-off event does not.
- **Use in this project:** PSD is *the* tool for measuring and reporting our sensor's noise floor — the number that proves (or disproves) the "high-sensitivity, low-noise" claim.

---

## SECTION 13 — HOW DO WE CREATE PRESSURE FOR TESTING?

| Method | Frequency range | Control | Advantages | Disadvantages | Calibration difficulty | Suitability |
|---|---|---|---|---|---|---|
| Speaker + sealed chamber | ~0.5 Hz–20+ Hz (limited at very low f by speaker mechanics) | Good (via function generator) | Precise frequency control, repeatable, safe | Harder to reach <0.1 Hz cleanly | Moderate | **Best general-purpose option** |
| Piston/syringe (manual or motor-driven) | Very low frequency (<1 Hz), good for near-DC tests | Moderate | Simple, safe, cheap, great for very low frequency | Hard to get precise sinusoidal control manually | Low (simple volume-based calc) | **Best for very-low-frequency/step tests** |
| Motorized piston + function generator | 0.01 Hz–few Hz | Good | Combines syringe simplicity with repeatable control | More build effort (needs a motor/linear actuator) | Moderate | Good upgrade path |
| Large room/door-slam pressure transient | Uncontrolled, broadband | Poor | Zero cost, quick sanity check | Not calibrated, not repeatable | High (hard to quantify) | Only for quick sanity checks, not real validation |

**Recommendation:** Start with a **speaker-driven sealed test chamber** (safe, precise, easy to control via a function generator or even a laptop's audio output at very low frequencies) for the frequency-response tests, and a **manual syringe/piston** for very-low-frequency / step-response tests. Both are safe, low-cost, and buildable by students.

---

## SECTION 14 — HOW DO WE KNOW THE PRESSURE WE CREATED?

```
CONTROLLED PRESSURE SOURCE
        |
   PRESSURE CHAMBER
      /        \
REFERENCE    OUR SENSOR
 SENSOR
```

We need a **known-good reference measurement** (a lab manometer, or a second commercial pressure sensor with a trusted datasheet/calibration) measuring the *same* chamber at the *same* time as our sensor, so we can directly compare.

- **Sensitivity:** `Sensitivity = ΔV / ΔP` (or Δ(digital counts)/ΔP for a digital sensor) — the slope of output vs. known input pressure change.
- **Offset:** the reading when ΔP = 0 (should ideally be zero after calibration).
- **Linearity:** how well the sensitivity stays constant across the full test range (a straight calibration line vs. a curved one).
- **Repeatability:** how consistent readings are when you repeat the *same* pressure change multiple times.
- **Resolution:** the smallest ΔP that produces a distinguishable change in output, given the sensor's own noise.
- **Noise floor:** measured via PSD of the sensor's output with *no* intentional input (Section 12).

**Hypothetical example calculation (clearly hypothetical, not measured):**
Suppose a controlled ΔP = 5 Pa produces a measured output change of ΔV = 12.5 mV.
`Sensitivity = 12.5 mV / 5 Pa = 2.5 mV/Pa`
If the measured RMS noise floor (from PSD) is 0.05 mV, then the minimum detectable pressure ≈ `0.05 mV / 2.5 mV/Pa = 0.02 Pa`.
**These numbers are illustrative only — your actual sensitivity and noise floor must come from real experiments.**

---

## SECTION 15 — COMPLETE TESTING PLAN

For each test: **SETUP → INPUT → MEASUREMENT → CALCULATION → GRAPH → ACCEPTANCE CRITERION**

### 1. Noise floor
- Setup: sensor sealed, no intentional pressure input, quiet room
- Input: none (background only)
- Measurement: long recording (≥10 min) of raw output
- Calculation: PSD via Welch's method
- Graph: PSD vs. frequency (log-log)
- Acceptance criterion: **must be experimentally determined** — no invented number; report the measured noise floor as your result.

### 2. Sensitivity
- Setup: speaker/syringe test chamber + reference sensor
- Input: known ΔP steps or sine sweeps
- Measurement: sensor output vs. known ΔP
- Calculation: slope of best-fit line (Sensitivity = ΔV/ΔP)
- Graph: Output vs. input pressure (calibration curve)
- Acceptance criterion: linearity within an experimentally-assessed tolerance (report R² of fit)

### 3. Calibration
- Setup: same as sensitivity test, multiple repetitions
- Input: repeated known pressure steps
- Measurement: output at each step, across repetitions
- Calculation: mean, standard deviation at each step
- Graph: calibration curve with error bars
- Acceptance criterion: to be defined once first-pass repeatability is measured

### 4. Frequency response
- Setup: speaker-driven chamber + function generator
- Input: sine sweep across target band (e.g., 0.05–20 Hz)
- Measurement: output amplitude at each frequency
- Calculation: gain (dB) vs. frequency
- Graph: Bode-style magnitude plot
- Acceptance criterion: flat response (±X dB, to be defined) across target band — X determined after first sweep

### 5. Dynamic range
- Setup: same test chamber
- Input: smallest detectable ΔP up to largest before saturation
- Measurement: output vs. input across full range
- Calculation: ratio of max usable signal to noise floor, in dB
- Graph: input vs. output (log scale)
- Acceptance criterion: to be measured, not assumed

### 6. Stability
- Setup: sensor at rest, constant conditions
- Input: none
- Measurement: output over several hours
- Calculation: variance over time windows
- Graph: output vs. time (long duration)
- Acceptance criterion: TBD from measured baseline variance

### 7. Drift
- Setup: same as stability test, extended to 24+ hours
- Input: none
- Measurement: slow trend in output
- Calculation: drift rate (Pa/hour, from linear fit)
- Graph: output vs. time, trend line overlaid
- Acceptance criterion: TBD from measurement

### 8. Temperature dependence
- Setup: sensor in a temperature-controlled environment (or natural day/night cycle if no chamber available)
- Input: varying ambient temperature
- Measurement: output vs. temperature (with reference temp sensor)
- Calculation: fit Output = f(Temperature) at constant pressure
- Graph: output vs. temperature
- Acceptance criterion: TBD; use this fit for compensation (Section 17)

### 9. Wind noise
- See Section 16 in detail.

### 10. Repeatability
- Setup: same as sensitivity test
- Input: identical pressure stimulus repeated N times
- Measurement: output for each repetition
- Calculation: standard deviation across repetitions
- Graph: overlaid repeated trials
- Acceptance criterion: TBD from measurement

### 11. Long-term operation
- Setup: full system running unattended
- Input: natural environment
- Measurement: continuous logging over days
- Calculation: uptime %, data-loss rate, any anomalies
- Graph: full time-series with annotated gaps/issues
- Acceptance criterion: system should run without manual intervention for the test duration — target duration to be agreed by the team

---

## SECTION 16 — WIND-NOISE TEST

Compare: **WITHOUT wind protection** vs. **WITH wind protection (porous cap/manifold)**, ideally on a mildly breezy day (or using a fan as a controlled wind source indoors).

- **RMS noise:** `RMS = sqrt(mean(x(t)²))` computed over a fixed window, for both conditions.
- **SNR:** `SNR (dB) = 20 * log10(Signal_RMS / Noise_RMS)` — compute with and without wind protection, using the same controlled test signal in both cases.
- **Noise reduction:** `Reduction (dB) = 20 * log10(RMS_without_protection / RMS_with_protection)`
- **Spectral comparison:** overlay PSD plots (with vs. without protection) — wind noise typically shows up as elevated low-frequency broadband energy; the porous cap should visibly reduce this.

---

## SECTION 17 — TEMPERATURE COMPENSATION

From the temperature-dependence test (Section 15, test 8), fit a model:

`Output_corrected = Output_raw − f(Temperature)`

where `f(Temperature)` is the experimentally-fitted relationship (e.g., a linear or low-order polynomial fit of output vs. temperature at constant known pressure). Apply this correction in software (Python, post-processing) before further DSP. **The exact form of f() must come from your own calibration data — do not assume a generic temperature coefficient from a datasheet without verifying it in your actual assembled system**, since chamber materials, sealing, and mounting all affect real thermal behavior.

---

## SECTION 18 — SOFTWARE ARCHITECTURE

### MCU-side (embedded, in C/C++ via Arduino IDE or PlatformIO)
- Data acquisition (fixed-interval timer-based sampling)
- Timestamp attachment
- Basic packaging (CSV line or lightweight binary frame)
- Serial communication over USB
- (Optional) SD card backup logging

### PC-side (Python)
- **Acquisition module:** PySerial-based reader, parses incoming packets, writes to a buffer/queue
- **Live waveform:** Matplotlib (or PyQtGraph for smoother real-time updates) plotting pressure vs. time
- **FFT/PSD module:** NumPy `fft`, SciPy `signal.welch`
- **Spectrogram:** SciPy `signal.spectrogram`
- **Event detection:** custom threshold logic comparing in-band energy to a rolling background estimate
- **Data logging:** SQLite (structured, queryable) or CSV (simple, portable)
- **Dashboard:** PyQt/PySide (native desktop) or Streamlit/Dash (simpler, browser-based — recommended for a 3rd-year team building this for the first time)

### What the IT student should build
The IT student owns the **entire PC-side software stack**: acquisition parsing, the DSP pipeline (working closely with the DSP-focused ECE member), the database schema, and the live dashboard — this is a substantial, technically meaningful software engineering role (not just UI), including responsibility for data integrity, real-time performance, and the event-detection logic's software implementation.

---

## SECTION 19 — TEAM DIVISION

| Member | Role | Tasks | Components owned | Testing responsibility | Deliverables | Skills to learn |
|---|---|---|---|---|---|---|
| ECE 1 | Sensor & mechanical | Select/mount sensor, build chamber, tubing, wind protection | Sensor, chamber, tubing, enclosure | Noise floor, wind-noise test | Working sealed sensor assembly | MEMS datasheets, basic mechanical fabrication |
| ECE 2 | Analog electronics | Design amp + filter stage, PCB/perfboard layout | INA333, filter components, regulator | Frequency response, gain verification | Working analog front-end | Instrumentation amplifiers, active filter design |
| ECE 3 | Embedded/DAQ | MCU firmware, ADC interfacing, timing | ESP32, ADS1115/ADS1220 | Sampling jitter/timing verification | Reliable data stream to PC | Embedded C, I2C/SPI, timer-based sampling |
| ECE 4 | DSP/signal processing | Filtering, FFT/PSD pipeline, detection logic (algorithm design) | — (software, works with IT student on implementation) | Sensitivity, calibration, dynamic range tests | Validated DSP pipeline + noise-floor report | NumPy/SciPy, digital filter design |
| ECE 5 | Power/mechanical/system integration | Power supply design, enclosure integration, overall system assembly | Regulators, power source, final enclosure | Stability, drift, long-term operation tests | Fully integrated, weatherproofed prototype | Power supply design, system integration |
| IT student | Full PC-side software | Acquisition parser, database, dashboard, DSP implementation, event detection software | Python software stack | Software reliability, data integrity, live demo readiness | Complete dashboard + logging system | Python, real-time visualization, SQLite, signal processing implementation |

**Dependencies:** ECE 3's DAQ output format must be agreed with the IT student early (Week 1) since everything downstream depends on it; ECE 2's front-end design depends on ECE 1's raw sensor noise measurement; ECE 4 and the IT student should pair closely since DSP algorithm design and its software implementation are tightly coupled.

---

## SECTION 20 — BUDGET

| Tier | Approx. cost | What it buys |
|---|---|---|
| **Minimum prototype** | ₹2,500–4,000 | MEMS sensor + ESP32 + breadboard + basic tubing/chamber (no analog front-end, MCU's own I2C read of sensor) |
| **Recommended prototype** | ₹5,000–9,000 | Adds ADS1115, INA333 analog front-end, temp sensor, proper perfboard build, basic enclosure |
| **Advanced prototype** | ₹12,000–20,000 | Adds ADS1220/ADS1262 24-bit ADC, custom PCB, weatherproof enclosure, SD backup logging |

| Category | Items |
|---|---|
| **MUST BUY** | MEMS sensor, ESP32, ADS1115, basic passives, tubing, enclosure materials |
| **CAN BORROW** | Oscilloscope, function generator, reference manometer/barometer, temperature chamber (if available) |
| **CAN FABRICATE** | Reference chamber (3D print or repurposed container), wind-noise cap, mounting brackets |
| **OPTIONAL** | 24-bit ADC upgrade, custom PCB, SD card module, second sensor for comparison |

---

## SECTION 21 — WHAT TO BUY FIRST

1. **FIRST PURCHASE:** MEMS pressure sensor (MS5611) + ESP32 + breadboard/jumpers — *why:* answers the single most important question (what does the raw sensor noise floor look like) before spending on anything else.
2. **SECOND PURCHASE:** Tubing + chamber materials — *why:* needed to test the sensor in its actual sealed/differential configuration, not just open-air.
3. **THIRD PURCHASE (⚠️ only after measuring raw noise):** INA333 amp + filter passives + ADS1115 — *why:* only justified once you know the raw signal needs boosting/filtering and by how much.
4. **FOURTH PURCHASE:** Temperature sensor + regulator + power source — *why:* needed once you're ready to run longer stability/drift/temperature tests.
5. **FIFTH PURCHASE (⚠️ only if V1 proves insufficient):** 24-bit ADC upgrade, custom PCB, weatherproof enclosure — *why:* justified only after V1 testing reveals specific limitations these would solve.

---

## SECTION 22 — FIRST 7 DAYS

- **Day 1:** Read datasheets for MS5611, DPS310, BMP390. Understand resolution/noise specs. Decide on MS5611 as the first test sensor.
- **Day 2:** Order first-purchase components (Section 21, item 1).
- **Day 3:** While waiting for delivery, set up Arduino IDE/PlatformIO for ESP32; write and test basic I2C scan code.
- **Day 4:** Wire MEMS sensor directly to ESP32, get first raw pressure readings over serial.
- **Day 5:** Log raw data to a file via Python (PySerial), plot P(t) for a few minutes at rest.
- **Day 6:** Compute a first-pass PSD of this raw data — this is your first (rough) noise-floor estimate.
- **Day 7:** Team review: discuss what the raw noise floor looks like, and decide (as a team) whether an analog front-end is clearly needed or whether more raw-sensor testing is needed first.

**At the end of Day 7:** you should have a working raw sensor → ESP32 → PC pipeline, a real (if preliminary) noise-floor plot, and a team decision on what to buy next.

---

## SECTION 23 — 12-WEEK ROADMAP

| Week | Focus | Output/deliverable | Testing milestone |
|---|---|---|---|
| 1 | Research + first bench test | Raw sensor + ESP32 + PC pipeline working | Preliminary noise floor |
| 2 | Chamber + tubing build | Sealed reference chamber assembled | Leak check (soap-bubble test) |
| 3 | Analog front-end design | Amp + filter breadboarded | Gain/filter response bench-verified |
| 4 | ADC integration | ADS1115 wired and reading via ESP32 | Compare ADC-based readings vs. direct I2C sensor readings |
| 5 | Python DSP pipeline | Filtering, FFT, PSD scripts working on logged data | First "real" noise-floor PSD plot |
| 6 | Calibration rig build | Speaker/syringe test chamber built | First calibration curve (sensitivity) |
| 7 | Frequency response testing | Sine-sweep test completed | Bode-style response plot |
| 8 | Wind-noise + temperature testing | Wind cap tested, temp logging running | Wind-noise reduction (dB) measured |
| 9 | Dashboard development | Live waveform + FFT + PSD dashboard working | Demo-ready visualization |
| 10 | Enclosure + integration | Full system in enclosure, outdoor-testable | Stability/drift test running |
| 11 | Long-duration testing + optimization | 24+ hour unattended run completed | Long-term data reviewed, issues fixed |
| 12 | Documentation + SIH demo rehearsal | Final report, demo script rehearsed | Full mock demonstration run |

---

## SECTION 24 — FAILURE MODES / TROUBLESHOOTING

| # | Problem | Symptom | Likely cause | How to test | Solution |
|---|---|---|---|---|---|
| 1 | No sensor reading | I2C read fails/timeouts | Wiring error, wrong address | I2C scanner sketch | Recheck wiring, pull-up resistors |
| 2 | Output stuck at one value | Flat-line reading | Sensor not initialized properly | Check init sequence in datasheet | Fix firmware init sequence |
| 3 | Excessive noise even at rest | Very noisy P(t) plot | Poor grounding, long unshielded wires | Shorten wires, check grounding | Star grounding, shielded cable |
| 4 | Signal saturates | Output clips at max/min | Gain set too high | Reduce gain, recheck amplifier design | Lower gain or use auto-ranging |
| 5 | No response to test pressure | Flat output despite known input | Leak in chamber, disconnected tubing | Soap-bubble leak test | Reseal chamber, check connections |
| 6 | Drifting baseline | Output slowly rises/falls over hours | Temperature drift, chamber leak | Compare with temp log | Apply temperature compensation, fix leaks |
| 7 | Aliased/garbled frequency content | Unexpected high-frequency peaks | Missing anti-aliasing filter, low sample rate | Check filter design, check fs | Add/verify anti-aliasing filter, raise fs |
| 8 | Irregular sample timing | Jittery timestamps | Loop-based (not timer-based) sampling | Log timestamp deltas | Use hardware timer interrupt for sampling |
| 9 | Data loss over serial | Missing/corrupted samples | Buffer overflow, slow Python read loop | Monitor serial buffer, check for dropped packets | Increase buffer size, optimize read loop |
| 10 | Wind dominates signal | Huge low-freq noise outdoors | No/poor wind protection | Compare indoor vs outdoor PSD | Add porous cap/manifold |
| 11 | Inconsistent calibration | Calibration curve not repeatable | Loose tubing connections, inconsistent test setup | Repeat calibration multiple times | Tighten connections, standardize test procedure |
| 12 | Temperature sensor readings don't match ambient | Offset temperature readings | Self-heating from nearby electronics | Move sensor away from heat sources | Better thermal placement/isolation |
| 13 | System crashes during long test | Dashboard/logging stops overnight | Memory leak in Python script, USB disconnect | Monitor resource usage over time | Fix memory leaks, add auto-reconnect logic |
| 14 | Mechanical vibration corrupts data | Spikes correlated with footsteps/desk bumps | Poor vibration isolation | Tap desk near sensor, observe response | Add foam/rubber isolation mounts |
| 15 | ADC readings don't match direct sensor readings | Discrepancy between ADS1115 and I2C-direct values | Wrong ADC gain/reference setting | Cross-check with known voltage source | Recalibrate ADC gain settings |
| 16 | SD card logging fails | Missing/corrupted log files | SPI conflict with other peripherals | Check SPI bus sharing | Use separate SPI/CS lines, verify wiring |

---

## SECTION 25 — FINAL SIH DEMONSTRATION

**Suggested 5–10 minute sequence:**

1. **(30 sec)** Show the physical prototype — chamber, tubing, wind cap, electronics box.
2. **(1 min)** Explain the problem in one sentence: "We built a sensor that can detect pressure changes 1000x smaller than a normal weather sensor can see."
3. **(1 min)** Trigger a controlled pressure excitation (speaker-driven test chamber) live.
4. **(1 min)** Show the reference measurement alongside our sensor's output, side by side.
5. **(1 min)** Show the real-time waveform on the dashboard responding to the excitation.
6. **(1 min)** Show the live FFT — a clear peak appearing at the excitation frequency.
7. **(1 min)** Show the PSD — highlight the measured noise floor.
8. **(30 sec)** Show automatic event detection flagging the induced signal.
9. **(1 min)** Show the calibration curve/result (sensitivity in mV/Pa or equivalent).
10. **(1 min)** Show a before/after wind-noise comparison plot.
11. **(30 sec)** Mention temperature compensation and show the compensated vs. raw comparison.
12. **(30 sec)** Close with cost: "This system costs approximately ₹X, versus commercial microbarometers costing significantly more."

---

## SECTION 26 — FINAL SPECIFICATIONS

| Spec | TARGET (our proposal) | MEASURED (fill in after testing) |
|---|---|---|
| Frequency range | 0.01–20 Hz | *(to be measured)* |
| Noise floor | As low as achievable with chosen components | *(to be measured via PSD)* |
| Sensitivity | *(to be measured — no target invented)* | *(to be measured)* |
| Resolution | Best achievable with 16-bit ADC (V1) / 24-bit (upgrade) | *(to be measured)* |
| Dynamic range | *(to be measured)* | *(to be measured)* |
| Stability | Minimal drift over multi-hour runs | *(to be measured)* |
| Temperature range | Standard indoor/outdoor ambient (0–40°C, India context) | *(to be measured)* |
| Wind-noise reduction | Measurable improvement with porous cap | *(to be measured in dB)* |
| Power consumption | Low enough for extended battery/power-bank operation | *(to be measured)* |
| Size | Compact, portable (fits in a small bag) | *(actual dimensions once built)* |
| Cost | ₹2,500–20,000 depending on tier | *(actual BOM total)* |
| Calibration accuracy | *(to be measured against reference instrument)* | *(to be measured)* |

**No value above is claimed as achieved until backed by an actual measurement — this table must be filled in with real data before the SIH demonstration, not populated with assumed numbers.**

---

## SECTION 27 — FINAL MASTER PLAN

```
WHAT WE BUILD
  A high-sensitivity microbarometer that detects and characterizes
  tiny, low-frequency atmospheric pressure fluctuations (infrasound)
       |
HOW IT WORKS
  MEMS sensor in a sealed reference chamber -> low-noise analog
  front-end -> external precision ADC -> MCU -> PC-based DSP
  (filtering, FFT, PSD) -> event detection -> live dashboard
       |
COMPONENTS
  MS5611/DPS310 sensor, INA333 amp, ADS1115/ADS1220 ADC, ESP32,
  SHT31 temp sensor, basic mechanical + power components
       |
MECHANICAL DESIGN
  Sealed chamber + porous wind-noise inlet + isolated mounting
       |
ELECTRONICS
  Amp + filter stage tuned to measured sensor characteristics
       |
SOFTWARE
  ESP32 firmware (acquisition/streaming) + Python DSP/dashboard
  (owned primarily by the IT student, in close collaboration with
  the DSP-focused ECE member)
       |
CALIBRATION
  Speaker/syringe-driven known pressure inputs vs. reference sensor
       |
TESTING
  Noise floor, sensitivity, frequency response, wind-noise reduction,
  temperature dependence, stability/drift — all experimentally measured
       |
FINAL DEMO
  Live controlled excitation -> real-time detection -> proven,
  measured specifications shown to judges
```

### FIRST THING WE SHOULD DO TOMORROW

**Order the MS5611 pressure sensor and an ESP32 dev board, and start reading their datasheets tonight.** Everything else in this roadmap depends on getting real, measured data from this first sensor as early as possible — don't let any other decision (analog front-end design, ADC choice, enclosure design) block this first step.
