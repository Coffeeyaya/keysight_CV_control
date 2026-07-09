import argparse
import sys
import csv
import os
import time

from keysight_control.e4980a import KeysightE4980A
from keysight_control.cv_sweep import run_cv_sweep

def main():
    parser = argparse.ArgumentParser(description="Keysight E4980A Standalone Measurement CLI")
    
    # CLI Arguments
    parser.add_argument("--visa", type=str, default=None, help="VISA Address of the instrument")
    parser.add_argument("--mode", type=str, required=True, 
                        choices=["test_conn", "open_cal", "short_cal", "dark_sweep", "light_sweep"],
                        help="Operating mode")
    parser.add_argument("--v-start", type=float, default=-10.0, help="Gate sweep start voltage (V)")
    parser.add_argument("--v-stop", type=float, default=10.0, help="Gate sweep stop voltage (V)")
    parser.add_argument("--num-pts", type=int, default=41, help="Number of sweep points")
    parser.add_argument("--step-delay", type=float, default=0.2, help="Settle time per step (s)")
    parser.add_argument("--ac-freq", type=float, default=1e6, help="AC signal frequency (Hz)")
    parser.add_argument("--ac-volt", type=float, default=0.03, help="AC signal amplitude (V)")
    parser.add_argument("--aperture", type=str, default="MED", choices=["SHOR", "MED", "LONG"], 
                        help="Aperture integration speed")
    parser.add_argument("--func", type=str, default="CPD", choices=["CPD", "CPRP", "CSD"],
                        help="Measurement parameter function type")
    parser.add_argument("--output", type=str, default="temp_sweep_output.csv", 
                        help="Output path to save temporary sweep data")
    
    args = parser.parse_args()
    
    # Mode 1: Test Connection
    if args.mode == "test_conn":
        print(f"Attempting connection to VISA address: {args.visa or 'Auto-detect'}")
        try:
            meter = KeysightE4980A(resource_name=args.visa)
            print(f"SUCCESS: Connected to {meter.idn}")
            meter.close()
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: Connection failed: {e}", file=sys.stderr)
            sys.exit(1)
            
    # Mode 2 & 3: Calibration
    elif args.mode in ["open_cal", "short_cal"]:
        try:
            meter = KeysightE4980A(resource_name=args.visa)
            meter.reset()
            meter.configure_cable_correction(length=1)
            
            if args.mode == "open_cal":
                print("Starting Open Circuit Correction sweep...")
                meter.configure_open_correction(enable=True, execute=True)
                print("Open correction completed.")
            else:
                print("Starting Short Circuit Correction sweep...")
                meter.configure_short_correction(enable=True, execute=True)
                print("Short correction completed.")
                
            meter.close()
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: Calibration failed: {e}", file=sys.stderr)
            sys.exit(1)
            
    # Mode 4 & 5: C-V Sweeps (Dark & Light)
    elif args.mode in ["dark_sweep", "light_sweep"]:
        try:
            print(f"Initializing sweep for mode: {args.mode.upper()}")
            meter = KeysightE4980A(resource_name=args.visa)
            meter.reset()
            
            # Configure calibrations and settings
            meter.configure_cable_correction(length=1)
            meter.configure_open_correction(enable=True, execute=False)
            meter.configure_short_correction(enable=True, execute=False)
            
            meter.set_measurement_function(args.func)
            meter.set_ac_signal(frequency=args.ac_freq, voltage=args.ac_volt)
            meter.set_aperture_time(args.aperture)
            meter.set_auto_range(True)
            
            # Execute C-V sweep
            results = run_cv_sweep(
                instrument=meter,
                start_voltage=args.v_start,
                stop_voltage=args.v_stop,
                num_points=args.num_pts,
                step_delay=args.step_delay,
                verbose=True
            )
            meter.close()
            
            # Save raw sweep results to output file
            print(f"Saving sweep results to: {args.output}")
            with open(args.output, mode='w', newline='') as f:
                fieldnames = ['point_index', 'bias_voltage', 'param1', 'param2', 'status']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in results:
                    writer.writerow(row)
                    
            print("Sweep execution completed successfully.")
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: Sweep failed: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
