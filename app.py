import os
import csv
import subprocess
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid

# Page Configuration
st.set_page_config(
    page_title="2D Phototransistor C-V Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF4B4B, #FF8F8F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #7d8590;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "dark_results" not in st.session_state:
    st.session_state.dark_results = None
if "light_results" not in st.session_state:
    st.session_state.light_results = None
if "open_calibrated" not in st.session_state:
    st.session_state.open_calibrated = False
if "short_calibrated" not in st.session_state:
    st.session_state.short_calibrated = False
if "idn" not in st.session_state:
    st.session_state.idn = None

# Resource detection helper (delayed import to prevent page-load errors)
def detect_resources():
    try:
        import pyvisa
        rm = pyvisa.ResourceManager()
        return list(rm.list_resources())
    except Exception as e:
        return [f"Error listing resources: {e}"]

# Subprocess command runner with live terminal logging
def run_cli_command(args):
    cmd = ["python", "-m", "keysight_control.run_measurement"] + args
    log_placeholder = st.empty()
    log_content = ""
    
    # Run CLI command as a separate process and stream output to UI
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    while True:
        line = process.stdout.readline()
        if not line:
            break
        log_content += line
        log_placeholder.code(log_content)
        
    process.wait()
    return process.returncode, log_content

# 2D Carrier concentration calculation
def calculate_2d_carrier_concentration(sweep_results, channel_area_cm2):
    q = 1.602e-19
    sorted_pts = sorted(sweep_results, key=lambda x: x['bias_voltage'])
    voltages = np.array([pt['bias_voltage'] for pt in sorted_pts])
    capacitances = np.array([pt['param1'] for pt in sorted_pts]) # Cp (F)
    
    C_A = capacitances / channel_area_cm2
    min_idx = np.argmin(C_A)
    C_A_min = C_A[min_idx]
    
    C_channel = C_A - C_A_min
    C_channel = np.maximum(C_channel, 0)
    
    integrated_area = cumulative_trapezoid(C_channel, voltages, initial=0)
    integrated_area_shifted = integrated_area - integrated_area[min_idx]
    
    N_2D = integrated_area_shifted / q
    N_2D = np.where(voltages < voltages[min_idx], 0.0, N_2D)
    return voltages, capacitances, N_2D

# ----------------- SIDEBAR -----------------
st.sidebar.image("https://img.icons8.com/nolan/96/physics.png", width=60)
st.sidebar.markdown("### 🛠️ Hardware Setup")

# Manual text input for VISA address
selected_resource = st.sidebar.text_input(
    "VISA Address", 
    value="USB0::0x0957::0x0909::MY46500357::0::INSTR",
    help="Default example USB address. Set to your E4980A address."
)

# USB Port scanner (only runs when clicked)
if st.sidebar.button("🔍 Scan for USB Instruments"):
    with st.spinner("Scanning USB ports..."):
        resources = detect_resources()
        usb_resources = [r for r in resources if "USB" in r]
        if usb_resources:
            st.sidebar.success("Detected USB Address(es):")
            for r in usb_resources:
                st.sidebar.code(r)
        else:
            st.sidebar.warning("No USB instruments found. Ensure your E4980A is powered on.")

# Sidebar Test Connection
if st.sidebar.button("🔌 Test Connection"):
    with st.spinner("Connecting to hardware..."):
        ret, log = run_cli_command(["--visa", selected_resource, "--mode", "test_conn"])
        if ret == 0:
            for line in log.splitlines():
                if "SUCCESS: Connected to" in line:
                    st.session_state.idn = line.replace("SUCCESS: Connected to", "").strip()
            st.sidebar.success("Connection Successful!")
        else:
            st.sidebar.error("Connection Failed. Verify connection logs in main panel.")

# Sidebar Geometry Settings
st.sidebar.markdown("### 📐 Transistor Geometry")
w_um = st.sidebar.number_input("Channel Width W (µm)", min_value=0.1, max_value=10000.0, value=10.0, step=1.0)
l_um = st.sidebar.number_input("Channel Length L (µm)", min_value=0.1, max_value=10000.0, value=10.0, step=1.0)
channel_area_cm2 = (w_um * 1e-4) * (l_um * 1e-4)
st.sidebar.info(f"Calculated Area: {channel_area_cm2:.4e} cm²")

# Sidebar Sweep parameters
st.sidebar.markdown("### 📈 Sweep Settings")
v_start = st.sidebar.number_input("Start Gate Voltage (V)", value=-10.0, step=1.0)
v_stop = st.sidebar.number_input("Stop Gate Voltage (V)", value=10.0, step=1.0)
num_pts = st.sidebar.slider("Number of Points", min_value=5, max_value=201, value=41, step=2)
step_delay = st.sidebar.slider("Step Settle Delay (s)", min_value=0.01, max_value=2.00, value=0.20, step=0.05)

# Sidebar AC Stimulus Parameters
st.sidebar.markdown("### ⚡ AC Stimulus")
ac_freq = st.sidebar.number_input("AC Frequency (Hz)", min_value=20.0, max_value=2e6, value=1e6, step=100000.0)
ac_volt = st.sidebar.number_input("AC Amplitude (V)", min_value=0.005, max_value=2.000, value=0.030, step=0.010)
aperture = st.sidebar.selectbox("Aperture Speed", ["SHOR", "MED", "LONG"], index=1)

# ----------------- MAIN PANEL -----------------
st.markdown('<div class="main-title">2D Material Phototransistor C-V Sweeper</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Perform High-Frequency Capacitance-Voltage measurements and extract photogenerated sheet carrier concentration profiles.</div>', unsafe_allow_html=True)

# Connection & Calibration Status Card
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("**Instrument Status**")
    if st.session_state.idn:
        st.success(f"Connected: {st.session_state.idn.split(',')[1] if ',' in st.session_state.idn else st.session_state.idn}")
    else:
        st.warning("Not Connected")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("**Open Calibration**")
    if st.session_state.open_calibrated:
        st.success("Active (Calibrated)")
    else:
        st.info("Stored/Off")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("**Short Calibration**")
    if st.session_state.short_calibrated:
        st.success("Active (Calibrated)")
    else:
        st.info("Stored/Off")
    st.markdown('</div>', unsafe_allow_html=True)

# Step-by-Step Execution Tabs
tab_cal, tab_meas, tab_results = st.tabs(["🔒 Calibration", "🛰️ Measurement", "📊 Results & Export"])

# ---- TAB 1: CALIBRATION ----
with tab_cal:
    st.subheader("Instrument Corrections (Open/Short calibration)")
    st.markdown("""
    Because 2D monolayer materials have microscopic overlap areas, the channel capacitance is extremely small (typically < 30 pF).
    It is **highly recommended** to run Open and Short corrections to remove fixture and cabling parasitic impedances.
    """)
    
    cal_col1, cal_col2 = st.columns(2)
    
    with cal_col1:
        st.markdown("### Step 1: Open Calibration")
        st.info("👉 Action: Lift the probes completely off the device and pads (Open Circuit).")
        if st.button("🚀 Run Open Correction"):
            with st.spinner("Executing Open calibration sweep..."):
                ret, log = run_cli_command(["--visa", selected_resource, "--mode", "open_cal"])
                if ret == 0:
                    st.session_state.open_calibrated = True
                    st.success("Open calibration completed successfully!")
                else:
                    st.error("Open calibration failed. Check connection/logs.")
                    
    with cal_col2:
        st.markdown("### Step 2: Short Calibration")
        st.info("👉 Action: Place both probes down onto the same pad or short all electrodes (Short Circuit).")
        if st.button("🚀 Run Short Correction"):
            with st.spinner("Executing Short calibration sweep..."):
                ret, log = run_cli_command(["--visa", selected_resource, "--mode", "short_cal"])
                if ret == 0:
                    st.session_state.short_calibrated = True
                    st.success("Short calibration completed successfully!")
                else:
                    st.error("Short calibration failed. Check connection/logs.")

# ---- TAB 2: MEASUREMENT ----
with tab_meas:
    st.subheader("C-V Sweep Controls")
    
    meas_col1, meas_col2 = st.columns(2)
    
    with meas_col1:
        st.markdown("### 1. Measure Dark State")
        st.markdown("Action: Cover the probe station shield completely to block ambient light.")
        if st.button("🌑 Start Dark C-V Sweep", type="secondary"):
            with st.spinner("Measuring Dark C-V curve..."):
                output_file = "dark_temp.csv"
                ret, log = run_cli_command([
                    "--visa", selected_resource,
                    "--mode", "dark_sweep",
                    "--v-start", str(v_start),
                    "--v-stop", str(v_stop),
                    "--num-pts", str(num_pts),
                    "--step-delay", str(step_delay),
                    "--ac-freq", str(ac_freq),
                    "--ac-volt", str(ac_volt),
                    "--aperture", aperture,
                    "--output", output_file
                ])
                if ret == 0 and os.path.exists(output_file):
                    df_temp = pd.read_csv(output_file)
                    st.session_state.dark_results = df_temp.to_dict('records')
                    st.success("Dark measurement complete!")
                else:
                    st.error("Dark sweep failed. Check connection/logs.")
                    
        # State display
        if st.session_state.dark_results:
            st.success("Data Captured (Dark State)")
        else:
            st.info("No Dark Data captured yet.")
            
    with meas_col2:
        st.markdown("### 2. Measure Illuminated State")
        st.markdown("Action: Turn on the light source and illuminate the phototransistor channel.")
        if st.button("☀️ Start Light C-V Sweep", type="primary"):
            with st.spinner("Measuring Light C-V curve..."):
                output_file = "light_temp.csv"
                ret, log = run_cli_command([
                    "--visa", selected_resource,
                    "--mode", "light_sweep",
                    "--v-start", str(v_start),
                    "--v-stop", str(v_stop),
                    "--num-pts", str(num_pts),
                    "--step-delay", str(step_delay),
                    "--ac-freq", str(ac_freq),
                    "--ac-volt", str(ac_volt),
                    "--aperture", aperture,
                    "--output", output_file
                ])
                if ret == 0 and os.path.exists(output_file):
                    df_temp = pd.read_csv(output_file)
                    st.session_state.light_results = df_temp.to_dict('records')
                    st.success("Light measurement complete!")
                else:
                    st.error("Light sweep failed. Check connection/logs.")
                    
        # State display
        if st.session_state.light_results:
            st.success("Data Captured (Illuminated State)")
        else:
            st.info("No Illuminated Data captured yet.")

# ---- TAB 3: RESULTS & EXPORT ----
with tab_results:
    st.subheader("Data Analysis & Plots")
    
    if st.session_state.dark_results and st.session_state.light_results:
        # Perform calculations
        v_dark, c_dark, n_dark = calculate_2d_carrier_concentration(st.session_state.dark_results, channel_area_cm2)
        v_light, c_light, n_light = calculate_2d_carrier_concentration(st.session_state.light_results, channel_area_cm2)
        
        n_photo = n_light - n_dark
        
        # Build pandas DataFrame for visualization and download
        df = pd.DataFrame({
            "Voltage (V)": v_dark,
            "C_dark (pF)": c_dark * 1e12,
            "C_light (pF)": c_light * 1e12,
            "N_dark (cm^-2)": n_dark,
            "N_light (cm^-2)": n_light,
            "N_photo (cm^-2)": n_photo
        })
        
        # Ploting Panel
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
        
        # Subplot 1: C-V curves
        ax1.plot(v_dark, df["C_dark (pF)"], 'ko-', label='Dark', linewidth=2, markersize=4)
        ax1.plot(v_light, df["C_light (pF)"], 'ro-', label='Illuminated', linewidth=2, markersize=4)
        ax1.set_xlabel('Gate Bias Voltage $V_g$ (V)', fontsize=11)
        ax1.set_ylabel('Gate Capacitance $C_p$ (pF)', fontsize=11)
        ax1.set_title('Capacitance-Voltage (C-V) Curves', fontsize=12, fontweight='bold')
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend(fontsize=10)
        
        # Subplot 2: Carrier concentration
        ax2.plot(v_dark, df["N_dark (cm^-2)"], 'k--', label='$N_{dark}$ (Dark Carriers)', linewidth=1.8)
        ax2.plot(v_light, df["N_light (cm^-2)"], 'r--', label='$N_{light}$ (Illuminated Carriers)', linewidth=1.8)
        ax2.plot(v_dark, df["N_photo (cm^-2)"], 'b-', label='$N_{photo}$ (Net Photocarriers)', linewidth=2.2)
        ax2.set_xlabel('Gate Bias Voltage $V_g$ (V)', fontsize=11)
        ax2.set_ylabel('2D Sheet Carrier Density $N_{2D}$ ($cm^{-2}$)', fontsize=11)
        ax2.set_title('Carrier Concentration Profile', fontsize=12, fontweight='bold')
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.legend(fontsize=10)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # CSV Export Options
        csv_data = df.to_csv(index=False).encode('utf-8')
        
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            st.download_button(
                label="📥 Download Data CSV File",
                data=csv_data,
                file_name="2d_phototransistor_cv_results.csv",
                mime="text/csv"
            )
            
        with col_down2:
            plot_filename = "2d_phototransistor_plots.png"
            fig.savefig(plot_filename, dpi=300)
            with open(plot_filename, "rb") as file:
                st.download_button(
                    label="🖼️ Download High-Res Plot Image",
                    data=file,
                    file_name="2d_phototransistor_plots.png",
                    mime="image/png"
                )
        
        # Show interactive data preview
        st.markdown("### 📋 Data Table Preview")
        st.dataframe(df.style.format({
            "Voltage (V)": "{:.2f}",
            "C_dark (pF)": "{:.4f}",
            "C_light (pF)": "{:.4f}",
            "N_dark (cm^-2)": "{:.4e}",
            "N_light (cm^-2)": "{:.4e}",
            "N_photo (cm^-2)": "{:.4e}"
        }), height=300)
        
    else:
        st.info("⚠️ Please record both Dark and Illuminated C-V sweeps in the 'Measurement' tab to view results and calculate carrier concentration profiles.")
