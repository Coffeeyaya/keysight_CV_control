import time
import numpy as np

def run_cv_sweep(instrument, start_voltage, stop_voltage, num_points=21, step_delay=0.1, verbose=True):
    """
    Performs a DC bias sweep (Capacitance-Voltage sweep) using the KeysightE4980A controller.
    
    Parameters:
        instrument (KeysightE4980A): Connected instrument driver instance.
        start_voltage (float): Starting DC bias voltage (V).
        stop_voltage (float): Ending DC bias voltage (V).
        num_points (int): Number of measurement points in the sweep.
        step_delay (float): Time delay (seconds) to wait after setting bias before measuring.
        verbose (bool): If True, prints status and real-time measurements.
        
    Returns:
        list of dict: A list of dicts containing the results of the sweep.
                      Each dict contains: 'bias_voltage', 'param1', 'param2', 'status'
    """
    voltages = np.linspace(start_voltage, stop_voltage, num_points)
    results = []
    
    if verbose:
        print("\n--- Starting C-V Sweep ---")
        print(f"Sweep Range: {start_voltage} V to {stop_voltage} V with {num_points} points.")
        print(f"Step Delay: {step_delay} s\n")
        
    try:
        # Enable DC bias state
        instrument.set_dc_bias_state(True)
        # Set trigger to BUS mode once before entering the loop to avoid GPIB overhead/timeout
        instrument.set_trigger_source("BUS")
        time.sleep(0.5)
        
        for idx, volt in enumerate(voltages):
            # Set the current bias voltage
            instrument.set_dc_bias_voltage(volt)
            
            # Settle time
            time.sleep(step_delay)
            
            # Execute measurement point
            data = instrument.measure_single()
            
            # E4980A usually returns [parameter1, parameter2, status]
            # e.g., Cp (F), D, Status code
            if len(data) >= 3:
                param1, param2, status = data[0], data[1], data[2]
            elif len(data) == 2:
                param1, param2, status = data[0], data[1], 0
            else:
                param1, param2, status = float('nan'), float('nan'), -1
                
            point_result = {
                "point_index": idx + 1,
                "bias_voltage": float(volt),
                "param1": param1,
                "param2": param2,
                "status": int(status)
            }
            results.append(point_result)
            
            if verbose:
                print(f"Point {idx+1}/{num_points} | Bias: {volt:.3f} V | P1: {param1:.6e} | P2: {param2:.6e} | Status: {int(status)}")
                
    finally:
        # Ensure DC bias is turned off/reset to 0V when finished or if an error occurs
        if verbose:
            print("\nSweep complete. Disabling DC bias & restoring trigger to INT...")
        try:
            instrument.set_dc_bias_voltage(0.0)
            instrument.set_dc_bias_state(False)
            # Restore trigger source to internal continuous mode
            instrument.set_trigger_source("INT")
        except Exception as e:
            if verbose:
                print(f"Error resetting instrument state: {e}")
                
    return results
