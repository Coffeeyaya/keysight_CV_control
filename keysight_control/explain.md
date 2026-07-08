
# Keysight E4980A Driver Function Documentation

This document explains the purpose of each function implemented in `keysight_control/e4980a.py`, maps them to their underlying **SCPI (Standard Commands for Programmable Instruments)** commands, and points to the corresponding sections in the official *Keysight E4980A SCPI Command Reference* manual.

---

### SCPI Commands Reference Mapping Table

| Python Function / Method | Underlying SCPI Command(s) | SCPI Reference Section / Chapter | Purpose |
| :--- | :--- | :--- | :--- |
| `__init__` | `*IDN?` | IEEE 488.2 Common Commands | Initializes the PyVISA Resource Manager, opens a connection to the selected USB instrument, and queries its identification string to verify connection. |
| `write` | *N/A (Helper)* | *N/A* | Sends a raw SCPI command string to the instrument. |
| `query` | *N/A (Helper)* | *N/A* | Sends a raw SCPI query and returns the instrument's text response. |
| `query_values` | *N/A (Helper)* | *N/A* | Sends a query and parses the return ASCII comma-separated values into Python float elements. |
| `reset` | `*RST`<br>`*CLS` | IEEE 488.2 Common Commands | `*RST` resets instrument settings to factory defaults; `*CLS` clears the status byte register and error queue. |
| `enable_display` | `:DISPlay:ENABle <ON\|OFF>` | DISPlay Subsystem | Enables or disables display screen updates. Disabling display updates can improve sweep measurement speed. |
| `set_display_page` | `:DISPlay:PAGE <page>` | DISPlay Subsystem | Changes the active menu screen page (e.g. `MEAS` for measurement page, `LIST` for list sweep page). |
| `set_measurement_function` | `:FUNCtion:IMPedance:TYPE <type>` | FUNCtion Subsystem | Selects the dual measurement parameters (e.g., `CPD` for Parallel Capacitance-Dissipation factor, `CPRP` for Parallel Capacitance-Parallel Resistance). |
| `set_aperture_time` | `:APERture <speed>` | APERture Subsystem | Configures the measurement integration time / speed (`SHOR` for short/fast, `MED` for medium, `LONG` for long/accurate). |
| `set_auto_range` | `:FUNCtion:IMPedance:RANGe:AUTO <ON\|OFF>` | FUNCtion Subsystem | Toggles automatic ranging mode of the internal measurement bridge. |
| `set_ac_signal` | `:FREQuency <value>`<br>`:VOLTage[:LEVel] <value>` | FREQuency Subsystem<br>VOLTage Subsystem | Sets the test signal's AC frequency (Hz) and voltage amplitude (V). |
| `set_dc_bias_state` | `:BIAS:STATe <ON\|OFF>` | BIAS Subsystem | Enables or disables the internal DC bias voltage source. |
| `set_dc_bias_voltage` | `:BIAS:VOLTage[:LEVel] <value>` | BIAS Subsystem | Sets the output level of the DC bias voltage source (crucial for C-V measurements). |
| `set_trigger_source` | `:TRIGger:SOURce <source>` | TRIGger Subsystem | Selects trigger source (`INT` for automatic free-running, `BUS` for remote software trigger, `EXT` for physical hardware trigger). |
| `configure_cable_correction` | `:CORRection:LENGth <length>` | CORRection Subsystem | Sets the user test port cable length (0m, 1m, 2m, or 4m) for parasitic compensation. |
| `configure_open_correction` | `:CORRection:OPEN:STATe <ON\|OFF>`<br>`:CORRection:OPEN:EXECute` | CORRection Subsystem | Enables/disables open-circuit correction or performs a new open calibration sweep to zero out fixture stray capacitances. |
| `configure_short_correction` | `:CORRection:SHORt:STATe <ON\|OFF>`<br>`:CORRection:SHORt:EXECute` | CORRection Subsystem | Enables/disables short-circuit correction or performs a new short calibration sweep to zero out residual impedances. |
| `measure_single` | `:TRIGger:SOURce BUS`<br>`*TRG` | TRIGger Subsystem<br>IEEE 488.2 Common Commands | Switches the trigger source to software bus control, sends the `*TRG` command to execute a single measurement, and reads the returned data string. |
| `close` | *N/A (Helper)* | *N/A* | Safely closes the PyVISA resource connection and releases hardware communication ports. |

---

### Detailed Command Explanations & Manual Sections

#### 1. Device Identification & Reset (`__init__`, `reset`, `close`)
* **SCPI Command**: `*IDN?`, `*RST`, `*CLS`
* **Reference**: *SCPI Command Reference -> IEEE 488.2 Common Commands*
* **Explanation**: Common commands mandated by IEEE 488.2 standard.
  - `*IDN?` returns vendor, model number, serial number, and firmware version.
  - `*RST` resets instrument configurations but does not affect the correction data.
  - `*CLS` clears status registers.

#### 2. Display Subsystem (`enable_display`, `set_display_page`)
* **SCPI Command**: `:DISPlay:ENABle {ON|OFF|1|0}`, `:DISPlay:PAGE {MEAS|LIST|MSET|LSET|CORR|SYS}`
* **Reference**: *SCPI Command Reference -> DISPlay Subsystem*
* **Explanation**: Controls the front panel display screen. Setting display updates to `OFF` frees up microcontroller clock cycles, speeding up continuous measurements or automated software sweeps.

#### 3. Measurement Subsystem (`set_measurement_function`, `set_auto_range`)
* **SCPI Command**: `:FUNCtion:IMPedance:TYPE {CPD|CPQ|CPG|CPRP|CSD|CSQ|CSRS|...}`, `:FUNCtion:IMPedance:RANGe:AUTO {ON|OFF|1|0}`
* **Reference**: *SCPI Command Reference -> FUNCtion Subsystem*
* **Explanation**: Configures the mathematical calculations used by the instrument bridge. For example, `CPD` measures the parallel equivalent capacitance ($C_p$) and dissipation factor ($D$). The range auto command allows the instrument to choose the optimal measurement range automatically for maximum accuracy.

#### 4. Aperture / Speed Subsystem (`set_aperture_time`)
* **SCPI Command**: `:APERture {SHORt|MEDium|LONG}[,<value>]`
* **Reference**: *SCPI Command Reference -> APERture Subsystem*
* **Explanation**: Configures the integration time. Longer integration periods filter out high-frequency noise at the cost of slower measurement times.

#### 5. Signal Source Subsystem (`set_ac_signal`)
* **SCPI Command**: `:FREQuency <value>`, `:VOLTage[:LEVel] <value>`
* **Reference**: *SCPI Command Reference -> FREQuency Subsystem* & *VOLTage Subsystem*
* **Explanation**: Sets the frequency and voltage amplitude of the AC test stimulus signal.

#### 6. Bias Subsystem (`set_dc_bias_state`, `set_dc_bias_voltage`)
* **SCPI Command**: `:BIAS:STATe {ON|OFF|1|0}`, `:BIAS:VOLTage[:LEVel] <value>`
* **Reference**: *SCPI Command Reference -> BIAS Subsystem*
* **Explanation**: Configures the internal DC bias source of the E4980A. C-V profiling sweeps the DC bias voltage while recording capacitance. `:BIAS:STATe ON` activates the DC source, and `:BIAS:VOLTage` changes the bias voltage value.

#### 7. Correction / Calibration Subsystem (`configure_cable_correction`, `configure_open_correction`, `configure_short_correction`)
* **SCPI Command**: 
  - `:CORRection:LENGth <value>`
  - `:CORRection:OPEN:STATe {ON|OFF|1|0}` / `:CORRection:OPEN:EXECute`
  - `:CORRection:SHORt:STATe {ON|OFF|1|0}` / `:CORRection:SHORt:EXECute`
* **Reference**: *SCPI Command Reference -> CORRection Subsystem*
* **Explanation**: 
  - `:CORRection:LENGth` specifies the extension cable length to ensure phase calibration is correctly aligned.
  - `:CORRection:OPEN:EXECute` measures open-circuit stray parameters to eliminate fixture parasitic capacitance.
  - `:CORRection:SHORt:EXECute` measures short-circuit residual parameters to eliminate fixture lead resistance and inductance.

#### 8. Trigger Subsystem & Bus Trigger (`set_trigger_source`, `measure_single`)
* **SCPI Command**: `:TRIGger:SOURce {INTernal|EXTernal|BUS|HOLD}`, `*TRG`
* **Reference**: *SCPI Command Reference -> TRIGger Subsystem*
* **Explanation**: To perform software-controlled measurements, the trigger source is set to `BUS`. The program then initiates a single measurement using the `*TRG` command, which immediately returns the measured values.
