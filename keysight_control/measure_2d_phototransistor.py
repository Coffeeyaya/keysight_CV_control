import os
import csv
import time
import numpy as np
from scipy.integrate import cumulative_trapezoid

# Try importing matplotlib to plot, handle gracefully if not installed
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from keysight_control.e4980a import KeysightE4980A
from keysight_control.cv_sweep import run_cv_sweep

def calculate_2d_carrier_concentration(sweep_results, channel_area_cm2):
    """
    Calculates the 2D sheet carrier concentration (cm^-2) for a monolayer 
    semiconductor transistor by integrating the experimental C-V curve.
    """
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
    C_channel = C_A - C_A_min
    C_channel = np.maximum(C_channel, 0)
    
    # 3. Perform cumulative trapezoidal integration
    integrated_area = cumulative_trapezoid(C_channel, voltages, initial=0)
    
    # 4. Shift integration reference to V_min so that N_2D(V_min) = 0
    integrated_area_shifted = integrated_area - integrated_area[min_idx]
    
    N_2D = integrated_area_shifted / q
    N_2D = np.where(voltages < voltages[min_idx], 0.0, N_2D)
    
    return voltages, capacitances, N_2D

def plot_results(voltages, c_dark, c_light, n_dark, n_light, n_photo):
    """
    Plots Capacitance-Voltage (C-V) curves and calculated Carrier Density profiles.
    """
    if not HAS_MATPLOTLIB:
        print("\n[Warning] matplotlib is not installed. Skipping graphical plot.")
        print("To enable plotting, run: pip install matplotlib")
        return
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Convert Capacitance to pF for plotting
    c_dark_pf = c_dark * 1e12
    c_light_pf = c_light * 1e12
    
    # Subplot 1: C-V Characteristics
    ax1.plot(voltages, c_dark_pf, 'ko-', label='Dark', linewidth=2, markersize=4)
    ax1.plot(voltages, c_light_pf, 'ro-', label='Illuminated', linewidth=2, markersize=4)
    ax1.set_xlabel('Gate Bias Voltage $V_g$ (V)', fontsize=11)
    ax1.set_ylabel('Gate Capacitance $C_p$ (pF)', fontsize=11)
    ax1.set_title('Capacitance-Voltage (C-V) Curves', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(fontsize=10)
    
    # Subplot 2: Sheet Carrier Density Profile
    ax2.plot(voltages, n_dark, 'k--', label='$N_{dark}$ (Dark Carriers)', linewidth=1.8)
    ax2.plot(voltages, n_light, 'r--', label='$N_{light}$ (Illuminated Carriers)', linewidth=1.8)
    ax2.plot(voltages, n_photo, 'b-', label='$N_{photo}$ (Net Photocarriers)', linewidth=2.2)
    ax2.set_xlabel('Gate Bias Voltage $V_g$ (V)', fontsize=11)
    ax2.set_ylabel('2D Sheet Carrier Density $N_{2D}$ ($cm^{-2}$)', fontsize=11)
    ax2.set_title('Carrier Concentration Profile', fontsize=12, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(fontsize=10)
    
    plt.tight_layout()
    plot_filename = "2d_phototransistor_plots.png"
    plt.savefig(plot_filename, dpi=300)
    print(f"Plot successfully saved to: {os.path.abspath(plot_filename)}")
    plt.show()

def main():
    print("=====================================================================")
    print("      2D Material Phototransistor C-V Measurement & Profiling       ")
    print("=====================================================================")
    print("\n--- PROCEDURAL STEPS FOR MEASUREMENT ---")
    print("1. Connection: Connect Gate to LCR high terminal (HCUR/HPOT shorted).")
    print("   Short Source & Drain together to LCR low terminal (LCUR/LPOT shorted).")
    print("2. Calibration: Run Open/Short corrections to subtract probe parasitics.")
    print("3. Dark Sweep: Measure C-V with shield closed (DARK state).")
    print("4. Light Sweep: Measure C-V with light source active (LIGHT state).")
    print("5. Analysis: Integration isolates active photogenerated sheet carriers.")
    print("=====================================================================\n")
    
    # Inputs for calculation
    try:
        width_um = float(input("Enter 2D channel width (W) in micrometers: "))
        length_um = float(input("Enter 2D channel length (L) in micrometers: "))
    except ValueError:
        print("Invalid input. Defaulting to W = 10 um, L = 10 um.")
        width_um = 10.0
        length_um = 10.0
        
    channel_area_cm2 = (width_um * 1e-4) * (length_um * 1e-4)
    print(f"Calculated 2D Channel Area: {channel_area_cm2:.6e} cm^2\n")
    
    # 1. Initialize instrument connection
    try:
        meter = KeysightE4980A()
    except RuntimeError as err:
        print(f"Connection Error: {err}")
        return

    try:
        # 2. Reset and configure calibration parameters
        print("\nResetting instrument settings...")
        meter.reset()
        meter.configure_cable_correction(length=1)
        
        run_cal = input("Do you want to run new Open/Short corrections? (y/N): ").strip().lower()
        if run_cal == 'y':
            input("\n[Action 1] Disconnect probes from contacts (Open Circuit).\nPress Enter when ready...")
            meter.configure_open_correction(enable=True, execute=True)
            
            input("\n[Action 2] Place probes on same pad or short all terminals (Short Circuit).\nPress Enter when ready...")
            meter.configure_short_correction(enable=True, execute=True)
        else:
            print("Skipping active calibration. Using stored parameters...")
            meter.configure_open_correction(enable=True, execute=False)
            meter.configure_short_correction(enable=True, execute=False)

        # 3. Configure measurement parameters
        meter.set_measurement_function("CPD")
        meter.set_ac_signal(frequency=1e6, voltage=0.03)
        meter.set_aperture_time("MED")
        meter.set_auto_range(True)
        
        sweep_start = -10.0
        sweep_stop = 10.0
        num_points = 41
        step_delay = 0.2
        
        # 4. MEASUREMENT 1: DARK STATE
        print("\n----------------------------------------------------------")
        print(" PHASE 1: DARK STATE MEASUREMENT")
        print("----------------------------------------------------------")
        input("[Action Required] Turn off light source & cover shield (DARK).\nPress Enter to start dark C-V sweep...")
        
        dark_results = run_cv_sweep(
            instrument=meter,
            start_voltage=sweep_start,
            stop_voltage=sweep_stop,
            num_points=num_points,
            step_delay=step_delay,
            verbose=True
        )
        
        # 5. MEASUREMENT 2: ILLUMINATED STATE
        print("\n----------------------------------------------------------")
        print(" PHASE 2: ILLUMINATED STATE MEASUREMENT")
        print("----------------------------------------------------------")
        input("[Action Required] Turn on the excitation light source.\nPress Enter to start light C-V sweep...")
        
        light_results = run_cv_sweep(
            instrument=meter,
            start_voltage=sweep_start,
            stop_voltage=sweep_stop,
            num_points=num_points,
            step_delay=step_delay,
            verbose=True
        )
        
        # 6. Post-Processing & Calculations
        print("\nProcessing C-V curves and calculating sheet carrier densities...")
        v_dark, c_dark, n_dark = calculate_2d_carrier_concentration(dark_results, channel_area_cm2)
        v_light, c_light, n_light = calculate_2d_carrier_concentration(light_results, channel_area_cm2)
        
        n_photo = n_light - n_dark
        
        # 7. Save results to CSV file
        csv_filename = "2d_phototransistor_cv_results.csv"
        with open(csv_filename, mode='w', newline='') as csv_file:
            fieldnames = [
                'voltage_V', 
                'c_dark_pF', 'c_light_pF', 
                'n_dark_cm2', 'n_light_cm2', 'n_photo_cm2'
            ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            
            for i in range(len(v_dark)):
                writer.writerow({
                    'voltage_V': v_dark[i],
                    'c_dark_pF': c_dark[i] * 1e12,
                    'c_light_pF': c_light[i] * 1e12,
                    'n_dark_cm2': n_dark[i],
                    'n_light_cm2': n_light[i],
                    'n_photo_cm2': n_photo[i]
                })
                
        print("\n==========================================================")
        print(" DATA SAVED")
        print(f"Data saved to: {os.path.abspath(csv_filename)}")
        print("==========================================================\n")
        
        # 8. Plot results
        plot_results(v_dark, c_dark, c_light, n_dark, n_light, n_photo)
        
    finally:
        meter.close()

if __name__ == "__main__":
    main()
