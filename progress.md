# Project Progress Report: Keysight E4980A Control Dashboard

This progress report summarizes the current implementation status, package structure, and operational steps for your Keysight E4980A C-V Measurement system.

---

## 📁 Package Structure

The following files have been created in the workspace:

```
/Users/tsaiyunchen/Desktop/lab/Auto_KeySight/
├── keysight_control/                   # Core control package
│   ├── __init__.py                     # Package initialization exports
│   ├── e4980a.py                       # KeysightE4980A class (PyVISA wrapper)
│   ├── cv_sweep.py                     # run_cv_sweep function (Sweep orchestrator)
│   ├── run_measurement.py              # CLI background execution engine
│   ├── measure_2d_phototransistor.py   # Interactive console measurement script
│   └── explan.md                       # Comprehensive SCPI command reference
├── app.py                              # Streamlit graphical web application dashboard
└── progress.md                         # This progress report
```

---

## 🛠️ Implemented Functionalities

### 1. Decoupled Architecture (UI vs. Control)
* The dashboard (`app.py`) has been fully decoupled from hardware libraries (`pyvisa`). It does not load or connect to the instrument on startup, preventing blockages or errors on page refreshes.
* Execution is driven via background processes using command-line arguments passed to `run_measurement.py`, streaming hardware output logs to the browser screen in real-time.

### 2. Instrument Calibration (Open/Short Correction)
* Encapsulated E4980A correction commands in `e4980a.py`.
* Automated Open/Short calibration routines through interactive prompts (both in the terminal and in the Streamlit web interface).

### 3. C-V Sweep Engine
* Supports setting DC Bias limits, AC amplitude (30mV/50mV/100mV), AC frequency (1MHz), step settle delay (s), and integration speeds.
* Sequentially sweeps DC bias voltages and logs experimental capacitances.

### 4. 2D Transistor carrier concentration calculations
* Monolayer 2D material sheet density profiling using the **area-integration method**:
  $$N_{\text{induced}}(V_g) = \frac{1}{q} \int_{V_{\text{min}}}^{V_g} (C_A(V_g) - C_{A,\text{min}}) \, dV_g$$
* Automatically subtracts the flat baseline parasitic capacitance ($C_{A,\text{min}}$) and aligns integration starting points with the threshold/depletion point $V_{\text{min}}$.
* Evaluates net photogenerated carrier density profiles by subtracting Dark carriers from Light carriers: $N_{\text{photo}} = N_{\text{light}} - N_{\text{dark}}$.

### 5. Streamlit Dashboard
* Features parameters config inputs, connection status checks, calibration wizard step logs, dual sweep triggers (Dark and Light), and graphical plots comparison.
* Features one-click download buttons for exporting the formatted C-V results dataset (`2d_phototransistor_cv_results.csv`) and the high-resolution charts (`2d_phototransistor_plots.png`).

---

## 🚦 How to Run the Dashboard

1. **Connect Instrument**: Plug the Keysight E4980A LCR meter to your Mac using a USB cable. Short the High contacts together (Gate) and the Low contacts together (Source/Drain).
2. **Install Dependencies**:
   ```bash
   pip install streamlit pandas matplotlib scipy numpy pyvisa pyvisa-py
   ```
3. **Launch**:
   ```bash
   streamlit run app.py
   ```
4. **Use GUI**: Open `http://localhost:8501`, configure parameters, run calibrations, perform Dark and Light measurements sequentially, and download results in the final tab.
