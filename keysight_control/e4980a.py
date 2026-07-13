import pyvisa
import time

class KeysightE4980A:
    """
    Core controller class for the Keysight/Agilent E4980A LCR Meter.
    Encapulates connection setup, configurations, calibration, and data retrieval.
    """
    
    def __init__(self, resource_name=None, timeout=10000):
        """
        Initializes PyVISA resource manager and connects to the instrument.
        
        Parameters:
            resource_name (str, optional): The VISA address (e.g. 'USB0::0x0957::0x0909::MY46500357::0::INSTR').
                                           If None, the first detected USB instrument is used.
            timeout (int): Visa timeout in milliseconds. Default is 10000 ms.
        """
        self.rm = pyvisa.ResourceManager()
        
        if resource_name is None:
            resources = self.rm.list_resources()
            gpib_resources = [r for r in resources if "GPIB" in r]
            if not gpib_resources:
                raise RuntimeError(
                    "No GPIB instruments found. Please ensure the instrument is "
                    "connected and powered on, or specify the VISA address explicitly."
                )
            self.resource_name = gpib_resources[0]
            print(f"Auto-detected GPIB instrument: {self.resource_name}")
        else:
            self.resource_name = resource_name
            
        print(f"Connecting to {self.resource_name}...")
        self.instrument = self.rm.open_resource(self.resource_name)
        
        # Define termination and timeout parameters
        self.instrument.read_termination = '\n'
        self.instrument.write_termination = '\n'
        self.instrument.timeout = timeout
        
        # Verify connection by querying instrument identity
        self.idn = self.query("*IDN?")
        print(f"Connected successfully to: {self.idn}")
        
    def write(self, command, *args):
        """
        Sends a write command to the instrument.
        """
        full_command = command
        if args:
            full_command += " " + ",".join(map(str, args))
        self.instrument.write(full_command)
        
    def query(self, command):
        """
        Sends a query command and returns the response string.
        """
        return self.instrument.query(command).strip()
        
    def query_values(self, command):
        """
        Sends a query command and returns parsed float values.
        """
        return self.instrument.query_ascii_values(command)
        
    def reset(self):
        """
        Resets the instrument to its default factory settings and clears status registers.
        """
        self.write("*RST")
        self.write("*CLS")
        time.sleep(1)
        
    def enable_display(self, enable=True):
        """
        Enables or disables the screen display updates. Disabling display can improve sweep speed.
        """
        state = "ON" if enable else "OFF"
        self.write(f":DISP:ENAB {state}")
        
    def set_display_page(self, page="MEAS"):
        """
        Sets the active display page on the LCR Meter screen.
        Options: 'MEAS' (Measurement), 'LIST' (List sweep), 'CORR' (Correction), etc.
        """
        self.write(f":DISP:PAGE {page}")
        
    def set_measurement_function(self, func_type="CPD"):
        """
        Sets the measurement function parameter type.
        Common options:
            'CPD'  : Parallel capacitance (Cp) and dissipation factor (D)
            'CPQ'  : Parallel capacitance (Cp) and quality factor (Q)
            'CPG'  : Parallel capacitance (Cp) and conductance (G)
            'CPRP' : Parallel capacitance (Cp) and parallel resistance (Rp)
            'CSD'  : Series capacitance (Cs) and dissipation factor (D)
            'CSRS' : Series capacitance (Cs) and series resistance (Rs)
        """
        valid_funcs = ["CPD", "CPQ", "CPG", "CPRP", "CSD", "CSQ", "CSRS", "RX", "ZD", "ZR", "GB", "YBD", "YBD"]
        if func_type not in valid_funcs:
            print(f"Warning: {func_type} may not be a standard measurement type. Setting function...")
        self.write(f":FUNC:IMP:TYPE {func_type}")
        
    def set_aperture_time(self, aperture="MED"):
        """
        Sets the measurement integration speed.
        Options: 'SHOR' (Short), 'MED' (Medium), 'LONG' (Long).
        """
        if aperture not in ["SHOR", "MED", "LONG"]:
            raise ValueError("Aperture must be one of: 'SHOR', 'MED', 'LONG'")
        self.write(f":APER {aperture}")
        
    def set_auto_range(self, enable=True):
        """
        Enables or disables auto impedance range selection.
        """
        state = "ON" if enable else "OFF"
        self.write(f":FUNC:IMP:RANGE:AUTO {state}")
        
    def set_ac_signal(self, frequency=1000000, voltage=0.1):
        """
        Sets the AC stimulus signal frequency (Hz) and voltage amplitude (V).
        """
        self.write(f":FREQ {frequency}")
        self.write(f":VOLT:LEVEL {voltage}")
        
    def set_dc_bias_state(self, enable=True):
        """
        Enables or disables the internal DC bias voltage source.
        """
        state = "ON" if enable else "OFF"
        self.write(f":BIAS:STAT {state}")
        
    def set_dc_bias_voltage(self, voltage=0.0):
        """
        Sets the DC bias voltage (V).
        """
        self.write(f":BIAS:VOLT {voltage}")
        
    def set_trigger_source(self, source="INT"):
        """
        Configures the trigger source.
        Options:
            'INT'  : Internal automatic trigger (continuous measurement)
            'EXT'  : External trigger
            'BUS'  : GPIB/USB bus trigger (controlled via software commands)
            'HOLD' : Manual/Hold triggerf
        """
        if source not in ["INT", "EXT", "BUS", "HOLD"]:
            raise ValueError("Source must be one of: 'INT', 'EXT', 'BUS', 'HOLD'")
        self.write(f":TRIG:SOUR {source}")
        
    def clear_overflow_and_resume(self):
        """
        Clears error/overflow registers and restores continuous measurement 
        without losing calibration data.
        """
        self.write("*CLS")           # Clear error registers & status bytes
        self.write(":TRIG:SOUR INT")  # Switch back to Internal continuous trigger
        
    def configure_cable_correction(self, length=1):
        """
        Sets the cable length parameter for calibration corrections.
        Parameters:
            length (int): Cable length in meters. Options: 0, 1, 2, 4.
        """
        if length not in [0, 1, 2, 4]:
            raise ValueError("Cable length must be 0, 1, 2, or 4 meters.")
        self.write(f":CORR:LENG {length}")
        
    def configure_open_correction(self, enable=True, execute=False):
        """
        Toggles or triggers Open circuit calibration correction.
        """
        if execute:
            print("Executing Open Calibration correction. Please wait...")
            old_timeout = self.instrument.timeout
            self.instrument.timeout = 60000  # 60s timeout for sweep calibration
            try:
                self.write(":CORR:OPEN:EXEC")
                self.query("*OPC?")
            finally:
                self.instrument.timeout = old_timeout
            print("Open correction completed.")
            
        state = "ON" if enable else "OFF"
        self.write(f":CORR:OPEN:STAT {state}")
            
    def configure_short_correction(self, enable=True, execute=False):
        """
        Toggles or triggers Short circuit calibration correction.
        """
        if execute:
            print("Executing Short Calibration correction. Please wait...")
            old_timeout = self.instrument.timeout
            self.instrument.timeout = 60000  # 60s timeout for sweep calibration
            try:
                self.write(":CORR:SHOR:EXEC")
                self.query("*OPC?")
            finally:
                self.instrument.timeout = old_timeout
            print("Short correction completed.")
            
        state = "ON" if enable else "OFF"
        self.write(f":CORR:SHOR:STAT {state}")
            
    def measure_single(self):
        """
        Triggers a single measurement point and reads the output.
        Assumes the trigger source is set to a remote trigger mode (e.g. HOLD or BUS).
        
        Returns:
            list: [param1, param2, status]
                  e.g. for CPD: [Capacitance (F), Dissipation factor (D), Status]
        """
        # Trigger the measurement cycle
        self.write(":TRIG")
        # Synchronize: block until the measurement operation is complete
        self.query("*OPC?")
        # Fetch the completed measurement values
        values = self.query_values("FETC?")
        return values
        
    def close(self):
        """
        Closes the active VISA resource connection.
        """
        if self.instrument:
            self.instrument.close()
        self.rm.close()
        print("Instrument connection closed.")
