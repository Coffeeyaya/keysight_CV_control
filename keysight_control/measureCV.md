To perform a Capacitance-Voltage ($C-V$) measurement and calculate the gate-induced carrier concentration of a **two-dimensional (2D) monolayer semiconductor transistor** (such as $\text{MoS}_2$), the guidelines must be modified.

Traditional $C-V$ calculations rely on the 3D differential depletion-depth approximation ($W$), which breaks down for a atomically thin 2D sheet because the channel has no physical thickness for a depletion width to move through. Instead, you must use the **area-integration method** to calculate the sheet carrier density ($N_{\text{induced}}$ in $\text{cm}^{-2}$).

Here is the rewritten 2D-specific workflow:

### Phase 1: Data Acquisition (Instrument Control)

To measure the $C-V$ characteristics of the 2D transistor gate stack, utilize the following parameters and instrument steps:

1. **`KeysightE4980A()` Connect**: Establish communication with your LCR meter.
    
2. **Execute Open/Short Corrections**: **Extremely Critical.** Monolayer 2D channels have microscopic surface areas, meaning the total gate capacitance is exceptionally small (often under $30\text{ pF}$, as seen in the paper's data). Cable and fixture parasitic capacitances will easily dwarf your signal if not completely calibrated out.
    
3. **`set_measurement_function("CPD")`**: Set the measurement mode to Parallel Capacitance ($C_p$) and Dissipation factor ($D$). Parallel mode is standard because it properly models any gate dielectric leakage ($R_p$) running parallel to your 2D channel capacitance.
    
4. **`set_ac_signal(frequency=1e6, voltage=0.03)`**: Set the test frequency to **1 MHz** (High-Frequency $C-V$) and the AC amplitude to a small value ($30\text{ mV}$ or $50\text{ mV}$). High frequencies freeze out slow interface traps common in CVD-grown 2D heterostructures, ensuring you measure the true channel capacitance.
    
5. **`run_cv_sweep(meter, start_voltage, stop_voltage, num_points)`**:
    
    - **Gate Voltage Range**: Symmetrically sweep the gate (e.g., **$-10\text{ V}$ to $+10\text{ V}$** as used in this paper).
        
    - **Sweep Direction**: Sweep from a strong negative bias (where the n-type $\text{MoS}_2$ channel is completely empty/depleted) toward a positive bias (where electrons rapidly accumulate).
        
    - **Terminal Routing**: Connect the high-voltage terminal to the gate electrode, and short the source and drain contacts together to the low-voltage terminal.
        

### Phase 2: Post-Processing 2D Carrier Concentration Calculation

Instead of calculating a volumetric doping density at a changing depth, you will compute the accumulated 2D sheet carrier density ($N_{\text{induced}}$) by integrating the area under the measured capacitance curve starting from the full-depletion voltage baseline ($V_{\text{min}}$).

#### Equations for 2D Geometry:

1. **Capacitance per unit area ($C_A$):**
    
    $$C_A(V_g) = \frac{C_{\text{measured}}(V_g)}{\text{Area}_{\text{channel}}}$$
    
2. **Gated-Induced 2D Carrier Concentration ($N_{\text{induced}}$):**
    
    $$N_{\text{induced}}(V_g) = \frac{1}{q} \int_{V_{\text{min}}}^{V_g} (C_A(V_g) - C_{A,\text{min}}) \, dV_g$$
    

Where:

- $\text{Area}_{\text{channel}}$ = The physical overlap area of the $\text{MoS}_2$ channel directly above the gate ($\text{cm}^2$).
    
- $q$ = Elementary charge ($1.602 \times 10^{-19}\text{ C}$).
    
- $V_{\text{min}}$ = The threshold voltage at strong negative bias where the capacitance curve flattens out to its minimum value, meaning the 2D channel is fully depleted.

- $C_{A,\text{min}}$ = The minimum capacitance per unit area at $V_{\text{min}}$, representing the baseline parasitic/overlap capacitance when the channel is fully depleted.
    
- $V_g$ = Applied gate DC bias voltage ($\text{V}$).
    

#### Python Calculation Script for 2D Devices:

Replace your original script with this integration-based model. It uses cumulative trapezoidal integration to track the carrier concentration build-up across the voltage sweep:

Python

```python
import numpy as np
from scipy.integrate import cumulative_trapezoid

def calculate_2d_carrier_concentration(sweep_results, channel_area_cm2):
    """
    Calculates the 2D sheet carrier concentration (cm^-2) for a monolayer 
    semiconductor transistor by integrating the experimental C-V curve.
    """
    # Constants
    q = 1.602e-19  # Coulombs
    
    # Sort results by voltage to ensure correct sequential integration
    sorted_pts = sorted(sweep_results, key=lambda x: x['bias_voltage'])
    
    voltages = np.array([pt['bias_voltage'] for pt in sorted_pts])
    capacitances = np.array([pt['param1'] for pt in sorted_pts]) # Cp (F)
    
    # 1. Normalize capacitance by the physical 2D channel area (F/cm^2)
    C_A = capacitances / channel_area_cm2
    
    # 2. Identify V_min (the baseline depletion point) and C_A_min
    min_idx = np.argmin(C_A)
    C_A_min = C_A[min_idx]
    
    # Subtract baseline parasitic capacitance to isolate true channel capacitance
    # When depleted (V_g < V_min), channel contribution is 0
    C_channel = C_A - C_A_min
    C_channel = np.maximum(C_channel, 0)  # Remove negative values due to measurement noise
    
    # 3. Perform cumulative trapezoidal integration
    integrated_area = cumulative_trapezoid(C_channel, voltages, initial=0)
    
    # 4. Shift integration reference to V_min so that N_2D(V_min) = 0
    # For n-type transistor:
    #   - V_g > V_min: Accumulation of electrons
    #   - V_g < V_min: Channel is depleted, carrier density is 0
    integrated_area_shifted = integrated_area - integrated_area[min_idx]
    
    N_2D = integrated_area_shifted / q
    N_2D = np.where(voltages < voltages[min_idx], 0.0, N_2D)
    
    # Output structured data
    profile = []
    for i in range(len(voltages)):
        profile.append({
            "voltage": voltages[i],
            "capacitance_pF": capacitances[i] * 1e12, # Convert to pF for readability
            "sheet_carrier_density_cm2": float(N_2D[i])
        })
        
    return profile
```

### Environmental Characterization Note

Because you are working with a **phototransistor**, execute this Python processing function twice: once on your data array collected in the **Dark** and once on the array collected under **Illumination**. Subtracting the two final values at a given gate bias ($N_{\text{light}} - N_{\text{dark}}$) provides the exact metric for your net photogenerated carrier density.