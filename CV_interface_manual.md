# Keysight E4980A C-V Measurement & Interface Manual

This manual explains how to use the Streamlit web dashboard to perform Capacitance-Voltage (C-V) sweeps on 2D material phototransistors using the Keysight E4980A LCR Meter. It integrates hardware setup, parameter definitions, electrical timing physics, and step-by-step experimental procedures.

---

## 🛠️ Step-by-Step Experimental Procedure

### 1. Physical Device Connections (Four-Terminal Pair Configuration)

The E4980A uses a **Four-Terminal Pair (4TP)** configuration via the four BNC ports on the front panel: `Hcur`, `Hpot`, `Lpot`, and `Lcur`. This Kelvin connection is designed to eliminate lead resistance, lead inductance, and contact resistance of the cables during high-precision measurements.

#### The 4 Ports Explained:
* **`Hcur` (High Current)**: Sources the AC test current to the device.
* **`Hpot` (High Potential)**: Senses the voltage at the high-potential side of the device.
* **`Lpot` (Low Potential)**: Senses the voltage at the low-potential side of the device.
* **`Lcur` (Low Current)**: Sinks/returns the AC test current from the device.

#### How to Connect them to your Transistor:
To measure the gate-to-channel capacitance, you must combine these four ports into a two-probe measurement system (High and Low):

```
       E4980A Front Panel
   ┌─────────────────────────┐
   │  Hcur   Hpot   Lpot   Lcur
   └───┬──────┬──────┬──────┬──┘
       │      │      │      │
       └─┬─T──┘      └─┬─T──┘  <--- Short Hcur/Hpot and Lpot/Lcur (e.g. using BNC T-adapters)
         │             │
      [ High ]      [ Low ]    <--- Coaxial BNC cables to Probe Station
         │             │
      Probe 1       Probe 2
      (Gate)     (Source & Drain shorted)
```

1. **High Probe (Gate Connection)**:
   * Short **`Hcur` and `Hpot`** together as close to the device as possible. (Commonly done using a BNC T-adapter directly on the front panel, or at the probe station arm).
   * Route this combined high cable to **Probe 1** and land it on the **Gate electrode** of the transistor.
2. **Low Probe (Channel Connection)**:
   * Short **`Lcur` and `Lpot`** together as close to the device as possible (using a BNC T-adapter).
   * Route this combined low cable to **Probe 2**.
   * On your device or probe card, **short the Source and Drain contacts together** and connect them to this Low Probe.
3. **Shielding & Guarding (Crucial for 1 MHz)**:
   * The outer metal shields of the four BNC cables carry shielding currents to isolate the measurement signals from ambient noise. 
   * Ensure that the outer shields of all four cables are **connected together** (shorted together) near the probe tips. This forms the return loop for the shielding currents and eliminates parasitic capacitance from cable flexing. (Standard triaxial or Kelvin-coaxial probe arms do this automatically).

### 2. Launch the Interface
On the lab computer, run the launcher shortcut:
* Windows: Double-click `run_app.bat`
* Linux/macOS/Git Bash: Run `./run_app.sh`
* Open your browser to `http://localhost:8501`.

### 3. Open & Short Calibrations (Highly Critical)
Monolayer 2D material transistors have very small active contact areas, meaning the channel capacitance is tiny (often $< 30\text{ pF}$). Parasitics from probe cards and cables will dwarf your signal if not removed:
* **Open Correction**: Lift the probes completely off the device contacts and pads (creating an open circuit). Click **Run Open Correction** in the "Calibration" tab.
* **Short Correction**: Bring the probes down onto the same metal pad or short them together (creating a short circuit). Click **Run Short Correction** in the "Calibration" tab.

### 4. Dark State Measurement
* Cover the probe station shield completely to block all ambient light.
* In the "Measurement" tab, click **🌑 Start Dark C-V Sweep**. The live terminal output in the browser will show the sweep progress.

### 5. Illuminated State Measurement
* Turn on your light source (e.g., laser or lamp) and focus it directly onto the 2D channel.
* Click **☀️ Start Light C-V Sweep**.

### 6. Export and Review
* Switch to the **Results & Export** tab.
* Review the C-V curves and the calculated sheet carrier concentration profiles ($N_{\text{dark}}$, $N_{\text{light}}$, and the net photogenerated photocarriers $N_{\text{photo}}$).
* Download the CSV dataset (`2d_phototransistor_cv_results.csv`) and the high-res plot (`2d_phototransistor_plots.png`).

---

## 📈 Parameter Configuration Guide

Configure these parameters in the sidebar panel before starting measurements:

| Section | Parameter | Recommended Value for 2D Devices | Physics & Purpose |
| :--- | :--- | :--- | :--- |
| **Geometry** | Channel Width ($W$) & Length ($L$) | *Device-specific* (e.g., $10\text{ µm}$) | Used to calculate the gate overlap area ($\text{cm}^2$) to convert capacitance $C$ to capacitance-per-unit-area ($C_A$), which is required to calculate sheet carrier density. |
| **Sweep** | Start / Stop Voltage | Symmetrical (e.g., $-10\text{ V}$ to $+10\text{ V}$) | Defines the Gate DC voltage range. Ensure it starts in full depletion (off state, lowest capacitance) and ends in carrier accumulation (on state, highest capacitance). |
| **Sweep** | Number of Points | `41` or `51` points | Balances voltage resolution for numerical integration with measurement speed. |
| **Sweep** | Step Settle Delay | `0.20 s` to `0.50 s` | The wait time after stepping the gate DC voltage before measurement begins. Allows transient currents to decay and slow dielectric interface traps to relax. |
| **AC Stimulus** | AC Frequency | **`1e6` (1 MHz)** | High-frequency (HF) C-V is critical to "freeze out" slow interface traps. At lower frequencies, trap states respond to the AC signal, adding parasitic capacitance. |
| **AC Stimulus** | AC Amplitude | **`0.03 V` (30 mV)** | The small-signal AC amplitude. Keeping it small (30-50 mV) prevents the AC oscillation from perturbing the DC depletion state. |
| **AC Stimulus** | Aperture Speed | **`MED` (Medium)** or `LONG` | Integration speed of the measurement bridge. Medium/Long speed averages thousands of AC cycles to filter out noise, which is essential for tiny 2D capacitance signals. |

---

## ⏱️ Sourcing Timeline (Measurement Physics)

For each voltage step in the sweep, the E4980A executes the following pattern in the time domain:

```
          DC Gate voltage steps to V
                      │
                      ▼
          ┌───────────────────────┐  ◄─── AC Perturbation is already running (superimposed)
          │  Step Settle Delay    │
          │  (Wait: 0.2s - 0.5s)  │  ─── DC charging currents decay to zero.
          │                       │      Interface traps adjust to new DC level.
          └───────────┬───────────┘      No measurement integration occurs yet.
                      │
                      ▼  Settle Delay expires
          ┌───────────────────────┐
          │  Aperture Integration  │  ─── Instrument vector detectors integrate AC signals.
          │  (MED speed: 77ms)    │  ─── Averages 77,000 cycles (at 1 MHz) to extract
          │                       │      capacitance (Cp) and dissipation factor (D).
          └───────────┬───────────┘
                      │
                      ▼  Integration ends
          ┌───────────────────────┐
          │  Calculated Output    │  ─── Computes Cp/D and transfers values to computer.
          └───────────┬───────────┘
                      │
                      ▼
          Step voltage to V + ΔV (Restart loop)
```

---

## ⚡ DC Bias vs. DC Source Modes

The Keysight E4980A front panel features both **DC Bias** and **DC Source** settings. It is critical to understand their distinct functions:

1. **DC Bias (Internal DC Bias)**:
   * **Function**: Superimposes the DC voltage directly onto the AC test signal at the front panel `UNKNOWN` terminals.
   * **Role**: This is the mode used during C-V sweeps. It applies the gate bias voltage directly through the measurement path.
   * **SCPI Commands**: `:BIAS:STAT ON` and `:BIAS:VOLT <value>` (controlled by `set_dc_bias_state` and `set_dc_bias_voltage` in `e4980a.py`).
2. **DC Source (Independent DC Source)**:
   * **Function**: An auxiliary voltage output (0 to $\pm10\text{ V}$) fed through a separate BNC connector on the **rear panel**.
   * **Role**: It acts as an independent DC power supply channel. It is **not** combined with the measurement signal. It is typically used if you need to bias a third terminal of the device (like an independent back-gate) while measuring C-V on the front panel.
   * **SCPI Command**: `:SOURce:DCV <value>`.
