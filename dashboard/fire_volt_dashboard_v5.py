import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os, json
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="FIRE VOLT PROJECT", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background-color:#0f0f0f;}
[data-testid="stSidebar"]{background-color:#111111;border-right:1px solid #e07b00;}
[data-testid="stSidebar"] *{color:#f0f0f0 !important;}
html,body,[class*="css"],p,span,label,div{color:#f0f0f0;}
h1{color:#ff8c00 !important;font-size:2.2rem !important;letter-spacing:2px;}
h2{color:#ff8c00 !important;border-bottom:1px solid #e07b00;padding-bottom:6px;}
h3{color:#ffaa44 !important;}
[data-testid="metric-container"]{background:#252525;border:1px solid #e07b00;border-radius:10px;padding:14px;}
[data-testid="metric-container"] label{color:#ffaa44 !important;font-size:13px !important;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#ffffff !important;font-size:1.8rem !important;}
[data-testid="metric-container"] [data-testid="stMetricDelta"]{color:#ff8c00 !important;}
[data-testid="stTabs"] button{background:#252525 !important;color:#ffaa44 !important;border:1px solid #e07b00 !important;border-radius:8px 8px 0 0 !important;font-weight:500;}
[data-testid="stTabs"] button[aria-selected="true"]{background:#e07b00 !important;color:#ffffff !important;}
input,textarea,select{background-color:#252525 !important;color:#f0f0f0 !important;border:1px solid #e07b00 !important;border-radius:6px !important;}
.stButton>button{background:#e07b00 !important;color:white !important;border:none !important;border-radius:8px !important;font-weight:600 !important;}
.stButton>button:hover{background:#ff8c00 !important;}
[data-testid="stFileUploader"]{background:#252525;border:1px dashed #e07b00;border-radius:10px;padding:10px;}
.stProgress>div>div{background:#e07b00 !important;}
hr{border-color:#e07b00 !important;opacity:0.4;}
::-webkit-scrollbar{width:6px;}
::-webkit-scrollbar-track{background:#0f0f0f;}
::-webkit-scrollbar-thumb{background:#e07b00;border-radius:3px;}
[data-testid="stDataFrame"]{border:1px solid #e07b00;border-radius:8px;}
.stTextArea textarea{background:#252525 !important;color:#f0f0f0 !important;border:1px solid #e07b00 !important;}
.info-card{background:#1e1e1e;border:1px solid #2a2a2a;border-left:4px solid #e07b00;border-radius:10px;padding:16px 20px;margin-bottom:14px;}
.img-frame{border:2px solid #e07b00;border-radius:10px;overflow:hidden;margin-bottom:10px;}
.section-badge{display:inline-block;background:#1a1200;border:1px solid #e07b00;color:#ffaa44;font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;margin-bottom:10px;letter-spacing:.5px;}
</style>
""", unsafe_allow_html=True)

# ── SAVE DIR SETUP ────────────────────────────────────────────────────────────
SAVE_DIR = "fire_volt_data"
os.makedirs(SAVE_DIR, exist_ok=True)

VOLTAGE_FILE  = os.path.join(SAVE_DIR, "voltage_history.csv")
TEMP_FILE     = os.path.join(SAVE_DIR, "temp_history.csv")
ENERGY_FILE   = os.path.join(SAVE_DIR, "energy_history.csv")
SOOT_FILE     = os.path.join(SAVE_DIR, "soot_log.csv")
ABOUT_FILE    = os.path.join(SAVE_DIR, "about.json")
IMG_DIR       = os.path.join(SAVE_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def load_csv(path, default_df):
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except:
            pass
    return default_df

def save_csv(df, path):
    df.to_csv(path, index=False)

def load_about():
    if os.path.exists(ABOUT_FILE):
        try:
            with open(ABOUT_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "project_name": "Fire Volt",
        "abstract": "Fire Volt is an innovative autonomous car that combines three subsystems: car motion via ESP-32 and DC motors, heat-to-electricity conversion using TEG modules and a custom buck converter that steps the TEG output down to 4.5 V for safe battery pack charging, and a filtration system that converts carbon soot into usable ink.",
        "about": "This project was built as part of a group engineering initiative. The car chassis houses a combustion chamber, TEG modules, HEPA filter, and the main circuit board. The goal is to demonstrate sustainable energy recovery and environmental responsibility within a compact vehicle platform.",
        "team": "~OJAS",
        "version": "1.0",
        "date": "2026"
    }

def save_about(data):
    with open(ABOUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_images():
    imgs = []
    if os.path.exists(IMG_DIR):
        for fname in sorted(os.listdir(IMG_DIR)):
            if fname.lower().endswith((".png",".jpg",".jpeg")):
                imgs.append(os.path.join(IMG_DIR, fname))
    return imgs

# ── DEFAULT DATA ──────────────────────────────────────────────────────────────
default_voltage = pd.DataFrame({
    "Time": [f"T{i}" for i in range(1,11)],
    "TEG Output (V)":   [6.2,7.1,8.0,8.8,9.2,10.1,11.0,11.5,12.0,12.4],
    "Buck Output (V)":  [4.5,4.5,4.5,4.5,4.5, 4.5, 4.5, 4.5, 4.5, 4.5],
})
default_temp = pd.DataFrame({
    "Time": [f"T{i}" for i in range(1,11)],
    "Chamber Temp (°C)": [180,210,240,265,285,305,320,335,345,355],
    "Ambient Temp (°C)": [28,29,30,30,31,31,32,32,33,33],
})
default_energy = pd.DataFrame({
    "Session": [f"Run {i}" for i in range(1,7)],
    "Energy Consumed (Wh)":  [12.0,13.5,11.8,14.2,13.0,12.6],
    "Energy Recovered (Wh)": [3.2,4.1,3.8,4.8,4.2,3.9],
})
default_soot = pd.DataFrame(columns=["Time","Soot (g)","Binder","Ink Ready"])

# ── SESSION STATE — load from disk on first run ───────────────────────────────
if "voltage_history" not in st.session_state:
    _vdf = load_csv(VOLTAGE_FILE, default_voltage)
    # ── Migrate old CSVs that still have BC1/BC2 columns ──────────────────
    if "Buck Output (V)" not in _vdf.columns:
        if "BC2 Output (V)" in _vdf.columns:
            _vdf = _vdf.rename(columns={"BC2 Output (V)": "Buck Output (V)"})
            _vdf["Buck Output (V)"] = 4.5          # overwrite boosted values with correct target
        elif "BC1 Output (V)" in _vdf.columns:
            _vdf = _vdf.rename(columns={"BC1 Output (V)": "Buck Output (V)"})
            _vdf["Buck Output (V)"] = 4.5
        else:
            _vdf["Buck Output (V)"] = 4.5          # column missing entirely — add it
        # Drop any leftover BC columns and re-save the migrated file
        _vdf = _vdf.drop(columns=[c for c in _vdf.columns if c.startswith("BC")], errors="ignore")
        save_csv(_vdf, VOLTAGE_FILE)
    st.session_state.voltage_history = _vdf
if "temp_history" not in st.session_state:
    st.session_state.temp_history = load_csv(TEMP_FILE, default_temp)
if "energy_history" not in st.session_state:
    st.session_state.energy_history = load_csv(ENERGY_FILE, default_energy)
if "soot_log" not in st.session_state:
    df_s = load_csv(SOOT_FILE, default_soot)
    st.session_state.soot_log = df_s.to_dict("records") if not df_s.empty else []
if "about" not in st.session_state:
    st.session_state.about = load_about()
if "fan_on" not in st.session_state:
    st.session_state.fan_on = True

# ── PLOTLY THEME ──────────────────────────────────────────────────────────────
PL = dict(
    paper_bgcolor="#141414", plot_bgcolor="#1c1c1c",
    font=dict(color="#f0f0f0", family="Arial"),
    xaxis=dict(gridcolor="#333333", color="#f0f0f0", showline=True, linecolor="#e07b00"),
    yaxis=dict(gridcolor="#333333", color="#f0f0f0", showline=True, linecolor="#e07b00"),
    legend=dict(bgcolor="#252525", bordercolor="#e07b00", borderwidth=1),
    margin=dict(l=40,r=20,t=40,b=40),
)
PINKS = ["#ff8c00","#e07b00","#ffaa44","#ffcc88","#cc6600","#ff9933"]

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Fire Volt")
    st.markdown("**Project Control Panel**")
    st.divider()

    st.markdown("### Upload Data CSV")
    st.caption("Upload once — auto-saved for next time")
    uploaded = st.file_uploader("Drop CSV here", type=["csv"], key="main_csv")
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded)
            cols = df_up.columns.tolist()
            saved_any = False
            if "TEG Output (V)" in cols:
                st.session_state.voltage_history = df_up
                save_csv(df_up, VOLTAGE_FILE)
                saved_any = True
            if "Chamber Temp (°C)" in cols:
                st.session_state.temp_history = df_up
                save_csv(df_up, TEMP_FILE)
                saved_any = True
            if "Energy Consumed (Wh)" in cols:
                st.session_state.energy_history = df_up
                save_csv(df_up, ENERGY_FILE)
                saved_any = True
            if saved_any:
                st.success(f"✅ Saved! {len(df_up)} rows loaded permanently.")
            else:
                st.warning("CSV columns not recognised. Check column names.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # Auto-save status
    files_exist = [os.path.exists(p) for p in [VOLTAGE_FILE, TEMP_FILE, ENERGY_FILE]]
    if all(files_exist):
        st.markdown("### 💾 Auto-save Status")
        st.success("All data saved locally")
        last_mod = datetime.fromtimestamp(os.path.getmtime(VOLTAGE_FILE)).strftime("%d %b %Y, %H:%M")
        st.caption(f"Last saved: {last_mod}")
    else:
        st.markdown("### 💾 Auto-save Status")
        st.info("Using default demo data")

    st.divider()

    st.markdown("### Settings")
    show_raw = st.toggle("Show raw data tables", value=False)

    if st.button("🔄 Reset to demo data"):
        for path in [VOLTAGE_FILE, TEMP_FILE, ENERGY_FILE, SOOT_FILE]:
            if os.path.exists(path):
                os.remove(path)
        st.session_state.voltage_history = default_voltage
        st.session_state.temp_history    = default_temp
        st.session_state.energy_history  = default_energy
        st.session_state.soot_log        = []
        st.success("Reset done!")
        st.rerun()

    st.divider()
    st.caption(f"Fire Volt v{st.session_state.about['version']}")
    st.caption(f"Team: {st.session_state.about['team']}")
    st.caption(f"Opened: {datetime.now().strftime('%H:%M:%S')}")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# ⚡ FIRE VOLT DASHBOARD")
st.markdown("##### Real-time monitoring across all three subsystems")
st.divider()

# ── TOP METRICS ───────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
vdf = st.session_state.voltage_history
tdf = st.session_state.temp_history
edf = st.session_state.energy_history
with c1:
    v  = float(vdf["TEG Output (V)"].iloc[-1])
    vp = float(vdf["TEG Output (V)"].iloc[-2]) if len(vdf)>1 else v
    st.metric("TEG Output", f"{v:.1f} V", f"{v-vp:+.1f} V")
with c2:
    v  = float(vdf["Buck Output (V)"].iloc[-1])
    vp = float(vdf["Buck Output (V)"].iloc[-2]) if len(vdf)>1 else v
    st.metric("Buck Output (4.5 V)", f"{v:.1f} V", f"{v-vp:+.1f} V")
with c3:
    t  = float(tdf["Chamber Temp (°C)"].iloc[-1])
    tp = float(tdf["Chamber Temp (°C)"].iloc[-2]) if len(tdf)>1 else t
    st.metric("Chamber Temp", f"{t:.0f} °C", f"{t-tp:+.0f} °C")
with c4:
    tot_c = edf["Energy Consumed (Wh)"].sum()
    tot_r = edf["Energy Recovered (Wh)"].sum()
    eff   = round((tot_r/tot_c)*100,1) if tot_c>0 else 0
    st.metric("Recovery Eff.", f"{eff}%")
with c5:
    soot_total = sum(r.get("Soot (g)",0) for r in st.session_state.soot_log)
    st.metric("Soot Collected", f"{soot_total:.1f} g")

st.divider()

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4 = st.tabs([
    "🚗  Car Motion",
    "🔥  Heat → Electricity",
    "🌿  Filtration",
    "📊  Overview"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — CAR MOTION
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Car Motion Subsystem")
    st.caption("ESP-32 · Motor Driver (L298N) · 4× DC Motors · Battery Pack")
    st.divider()
    col_l,col_r = st.columns(2)
    with col_l:
        st.subheader("Motor Control")
        motor_spd = st.slider("All motors speed (%)", 0, 100, 75)
        direction = st.selectbox("Direction", ["Forward","Reverse","Turn Left","Turn Right","Stop"])
        pwm_freq  = st.number_input("PWM Frequency (Hz)", min_value=100, max_value=50000, value=1000, step=100)
        st.caption("All 4 DC motors run at the same speed via L298N dual H-bridge.")
        if direction == "Stop":
            st.error("⛔ All motors stopped")
        elif direction in ["Turn Left","Turn Right"]:
            st.warning(f"↩ Turning: {direction}")
        else:
            st.success(f"✅ Moving: {direction}")
    with col_r:
        st.subheader("Battery Status")
        battery_pct = st.slider("Battery charge level (%)", 0, 100, 72)
        st.progress(battery_pct/100)
        bc = "#ff8c00" if battery_pct>50 else ("#ff9900" if battery_pct>20 else "#ff3333")
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=battery_pct,
            title={"text":"Battery Level","font":{"color":"#f0f0f0","size":14}},
            number={"suffix":"%","font":{"color":"#f0f0f0","size":28}},
            gauge={"axis":{"range":[0,100],"tickcolor":"#f0f0f0"},"bar":{"color":bc},
                   "bgcolor":"#252525","bordercolor":"#e07b00",
                   "steps":[{"range":[0,20],"color":"#1e1400"},{"range":[20,50],"color":"#1a1500"},{"range":[50,100],"color":"#202020"}],
                   "threshold":{"line":{"color":"#ff8c00","width":3},"value":20}}
        ))
        fig_g.update_layout(paper_bgcolor="#141414",font=dict(color="#f0f0f0"),height=260,margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_g, use_container_width=True)
        bat_v = st.number_input("Battery voltage (V)", value=7.4, step=0.1)
        bat_i = st.number_input("Current draw (A)",    value=2.3, step=0.1)
        st.metric("Power Consumption", f"{bat_v*bat_i:.2f} W")
    if show_raw:
        st.divider()
        st.dataframe(pd.DataFrame({
            "Motor": ["FL","FR","RL","RR"],
            "Speed (%)": [motor_spd]*4,
            "Direction": [direction]*4,
            "PWM Freq (Hz)": [pwm_freq]*4
        }), use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — HEAT TO ELECTRICITY
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Heat → Electricity Subsystem")
    st.caption("Combustion Chamber · TEG Modules (12–16 series) · Buck Converter (step-down to 4.5 V)")
    st.divider()
    col_a,col_b = st.columns(2)
    with col_a:
        st.subheader("Live Readings")
        n_teg    = st.slider("Number of TEG modules", 8, 16, 14)
        teg_per  = st.slider("Voltage per TEG (V)", 0.3, 1.5, 0.85, step=0.05)
        teg_tot  = round(n_teg*teg_per, 2)
        st.metric("TEG Series Output", f"{teg_tot} V", f"{n_teg} modules × {teg_per}V")
        st.divider()
        st.markdown("**Buck Converter (Step-Down)**")
        TARGET_V = 4.5
        # Buck duty cycle: D = Vout / Vin
        buck_duty_calc = round((TARGET_V / teg_tot) * 100, 1) if teg_tot > 0 else 0
        buck_duty = st.slider("Buck Duty cycle (%)", 0, 95,
                              min(int(buck_duty_calc), 95),
                              help="D = Vout / Vin  →  auto-set for 4.5 V output")
        buck_out  = round(teg_tot * (buck_duty / 100), 2)
        st.metric("Buck Output Voltage", f"{buck_out} V",
                  delta=f"Target 4.5 V | ΔD = {buck_duty}%")
        charging_current = st.number_input("Charging current (A)", 0.1, 5.0, 1.0, step=0.1)
        charging_power   = round(buck_out * charging_current, 2)
        st.metric("Battery Charging Power", f"{charging_power} W")
        if abs(buck_out - TARGET_V) <= 0.1:
            st.success(f"✅ Output {buck_out} V — on target, battery pack charging safely")
        elif buck_out < TARGET_V - 0.5:
            st.warning(f"⚠️ Output {buck_out} V — below 4.5 V, increase TEG count or duty cycle")
        else:
            st.warning(f"⚠️ Output {buck_out} V — above 4.5 V, reduce duty cycle to protect battery")
    with col_b:
        st.subheader("Chamber Temperature")
        chamber_t = st.number_input("Chamber temp (°C)", 0, 600, 310, step=5)
        ambient_t = st.number_input("Ambient temp (°C)", 0, 60,  30,  step=1)
        st.metric("Temperature Differential (ΔT)", f"{chamber_t-ambient_t} °C")
        if st.button("➕ Add reading to history"):
            new_t = len(st.session_state.temp_history)+1
            new_v = len(st.session_state.voltage_history)+1
            st.session_state.temp_history = pd.concat([
                st.session_state.temp_history,
                pd.DataFrame({"Time":[f"T{new_t}"],"Chamber Temp (°C)":[chamber_t],"Ambient Temp (°C)":[ambient_t]})
            ], ignore_index=True)
            st.session_state.voltage_history = pd.concat([
                st.session_state.voltage_history,
                pd.DataFrame({"Time":[f"T{new_v}"],"TEG Output (V)":[teg_tot],"Buck Output (V)":[buck_out]})
            ], ignore_index=True)
            save_csv(st.session_state.temp_history,    TEMP_FILE)
            save_csv(st.session_state.voltage_history, VOLTAGE_FILE)
            st.success("Reading saved permanently!")
            st.rerun()
    st.divider()
    cc,cd = st.columns(2)
    with cc:
        st.subheader("Voltage Over Time")
        fig_v = go.Figure()
        for col,clr in zip(["TEG Output (V)","Buck Output (V)"],PINKS[:2]):
            if col in st.session_state.voltage_history.columns:
                fig_v.add_trace(go.Scatter(
                    x=st.session_state.voltage_history["Time"],
                    y=st.session_state.voltage_history[col],
                    name=col, mode="lines+markers",
                    line=dict(color=clr,width=2), marker=dict(size=5)
                ))
        # Reference line at 4.5 V target
        fig_v.add_hline(y=4.5, line_dash="dash", line_color="#ffcc88",
                        annotation_text="4.5 V target", annotation_position="bottom right")
        fig_v.update_layout(**PL, title="Voltage Readings Over Time", height=300)
        st.plotly_chart(fig_v, use_container_width=True)
    with cd:
        st.subheader("Temperature Over Time")
        fig_t = go.Figure()
        fig_t.add_trace(go.Scatter(
            x=st.session_state.temp_history["Time"],
            y=st.session_state.temp_history["Chamber Temp (°C)"],
            name="Chamber", mode="lines+markers",
            line=dict(color="#ff8c00",width=2), marker=dict(size=5)
        ))
        fig_t.add_trace(go.Scatter(
            x=st.session_state.temp_history["Time"],
            y=st.session_state.temp_history["Ambient Temp (°C)"],
            name="Ambient", mode="lines+markers",
            line=dict(color="#666666",width=1.5,dash="dot"), marker=dict(size=4)
        ))
        fig_t.update_layout(**PL, title="Temperature Over Time (°C)", height=300)
        st.plotly_chart(fig_t, use_container_width=True)
    if show_raw:
        ce,cf = st.columns(2)
        with ce: st.dataframe(st.session_state.voltage_history, use_container_width=True)
        with cf: st.dataframe(st.session_state.temp_history,    use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — FILTRATION
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Filtration Subsystem")
    st.caption("HEPA Filter · Relay · Inbuilt Fan · Filtration Chamber · Ink Output")
    st.divider()
    col_p,col_q = st.columns(2)
    with col_p:
        st.subheader("Fan & Filter Control")
        fan_on     = st.toggle("Fan active (relay)", value=st.session_state.fan_on)
        st.session_state.fan_on = fan_on
        if fan_on: st.success("✅ Fan ON — smoke being drawn into filter")
        else:      st.error("⛔ Fan OFF — filtration paused")
        fan_speed  = st.slider("Fan speed (%)", 0, 100, 80 if fan_on else 0)  # visual only
        run_time   = st.number_input("Filter run time (minutes)", 0, 1000, 45, step=5)
        filter_life= max(0, 100-(run_time*0.4))
        st.metric("Filter Life Remaining", f"{filter_life:.0f}%")
        st.progress(filter_life/100)
        if filter_life < 30: st.warning("⚠️ Filter approaching end of life")
        st.divider()
        st.subheader("Log Soot Collection")
        soot_amt = st.number_input("Soot collected this session (g)", 0.0, 100.0, 0.5, step=0.1)
        binder   = st.selectbox("Binder used", ["Gum arabic + water","Linseed oil","Shellac + alcohol","None yet"])
        if st.button("📝 Log collection"):
            entry = {"Time": datetime.now().strftime("%H:%M:%S"),
                     "Soot (g)": soot_amt, "Binder": binder,
                     "Ink Ready": "Yes" if binder!="None yet" else "No"}
            st.session_state.soot_log.append(entry)
            df_soot_save = pd.DataFrame(st.session_state.soot_log)
            save_csv(df_soot_save, SOOT_FILE)
            st.success(f"Logged {soot_amt}g — saved permanently!")
            st.rerun()
    with col_q:
        st.subheader("Soot & Ink Log")
        if st.session_state.soot_log:
            df_soot = pd.DataFrame(st.session_state.soot_log)
            st.dataframe(df_soot, use_container_width=True)
            total_soot = df_soot["Soot (g)"].sum()
            est_ink    = total_soot*4.5
            cs1,cs2 = st.columns(2)
            cs1.metric("Total Soot",    f"{total_soot:.1f} g")
            cs2.metric("Estimated Ink", f"{est_ink:.1f} ml")
            fig_soot = go.Figure(go.Bar(
                x=df_soot["Time"], y=df_soot["Soot (g)"],
                marker_color=PINKS[0],
                text=df_soot["Soot (g)"].apply(lambda g:f"{g}g"),
                textposition="outside", textfont=dict(color="#f0f0f0")
            ))
            fig_soot.update_layout(**PL, title="Soot Collected Per Session (g)", height=260)
            st.plotly_chart(fig_soot, use_container_width=True)
            st.download_button("⬇️ Download log as CSV",
                               df_soot.to_csv(index=False).encode("utf-8"),
                               "soot_log.csv","text/csv")
        else:
            st.info("No soot logged yet. Use the form on the left to log your first collection.")
        st.divider()
        st.subheader("Air Cleaning Efficiency")
        smoke_in = st.number_input("Smoke intake rate (g/min)", value=0.12, step=0.01)

        HEPA_EFF   = 0.45   # HEPA filter captures 45% of intake
        CARBON_EFF = 0.15   # Activated carbon captures remaining 15%
        TOTAL_EFF  = 0.60   # Combined: 60% total cleaning efficiency

        after_hepa   = smoke_in * (1 - HEPA_EFF)
        after_carbon = after_hepa * (1 - (CARBON_EFF / (1 - HEPA_EFF)))
        captured     = smoke_in * TOTAL_EFF
        released     = smoke_in * (1 - TOTAL_EFF)

        st.info("Combined filter efficiency is fixed at **60%** (HEPA + activated carbon).")
        f1, f2, f3 = st.columns(3)
        f1.metric("HEPA stage", "45%", "of intake captured")
        f2.metric("Carbon stage", "15%", "of intake captured")
        f3.metric("Total efficiency", "60%", "combined")

        st.divider()
        r1, r2 = st.columns(2)
        r1.metric("Particulates captured", f"{captured:.3f} g/min")
        r2.metric("Released to atmosphere", f"{released:.4f} g/min")

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — OVERVIEW  (images · abstract · about · energy · health)
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("Project Overview")
    st.divider()

    # ── ROW 1: PROJECT IMAGES ────────────────────────────────────────────────
    st.markdown('<div class="section-badge">PROJECT IMAGES</div>', unsafe_allow_html=True)

    img_upload = st.file_uploader(
        "Upload project photos (PNG / JPG) — saved permanently",
        type=["png","jpg","jpeg"],
        accept_multiple_files=True,
        key="proj_images"
    )
    if img_upload:
        for up_img in img_upload:
            save_path = os.path.join(IMG_DIR, up_img.name)
            with open(save_path, "wb") as f:
                f.write(up_img.read())
        st.success(f"✅ {len(img_upload)} image(s) saved permanently!")
        st.rerun()

    saved_images = load_images()
    if saved_images:
        n_cols  = min(3, len(saved_images))
        img_cols = st.columns(n_cols)
        for idx, img_path in enumerate(saved_images):
            with img_cols[idx % n_cols]:
                img = Image.open(img_path)
                st.markdown('<div class="img-frame">', unsafe_allow_html=True)
                st.image(img, use_container_width=True,
                         caption=os.path.basename(img_path))
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button(f"🗑 Remove", key=f"del_img_{idx}"):
                    os.remove(img_path)
                    st.rerun()
    else:
        st.info("No project images uploaded yet. Upload photos above — they will be saved permanently.")

    st.divider()

    # ── ROW 2: ABSTRACT ──────────────────────────────────────────────────────
    st.markdown('<div class="section-badge">ABSTRACT</div>', unsafe_allow_html=True)

    with st.expander("✏️ Edit Abstract", expanded=False):
        new_abstract = st.text_area(
            "Write your project abstract here",
            value=st.session_state.about["abstract"],
            height=160, key="abstract_edit"
        )
        if st.button("💾 Save Abstract"):
            st.session_state.about["abstract"] = new_abstract
            save_about(st.session_state.about)
            st.success("Abstract saved permanently!")
            st.rerun()

    st.markdown(f"""
    <div class="info-card">
        <p style="line-height:1.9;font-size:14px;color:#e0e0e0;">
            {st.session_state.about["abstract"]}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── ROW 3: ABOUT ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-badge">ABOUT THE PROJECT</div>', unsafe_allow_html=True)

    with st.expander("✏️ Edit About Section", expanded=False):
        new_about   = st.text_area("About text", value=st.session_state.about["about"],    height=140, key="about_edit")
        new_team    = st.text_input("Team / Author name", value=st.session_state.about["team"],    key="team_edit")
        new_version = st.text_input("Version",            value=st.session_state.about["version"], key="ver_edit")
        new_date    = st.text_input("Year / Date",        value=st.session_state.about["date"],    key="date_edit")
        if st.button("💾 Save About Info"):
            st.session_state.about["about"]   = new_about
            st.session_state.about["team"]    = new_team
            st.session_state.about["version"] = new_version
            st.session_state.about["date"]    = new_date
            save_about(st.session_state.about)
            st.success("About info saved permanently!")
            st.rerun()

    ab = st.session_state.about
    ab_col1, ab_col2 = st.columns([2,1])
    with ab_col1:
        st.markdown(f"""
        <div class="info-card">
            <p style="line-height:1.9;font-size:14px;color:#e0e0e0;">
                {ab["about"]}
            </p>
        </div>
        """, unsafe_allow_html=True)
    with ab_col2:
        st.markdown(f"""
        <div class="info-card" style="height:100%;">
            <p style="color:#ffaa44;font-size:11px;margin-bottom:8px;font-weight:600;letter-spacing:.5px;">PROJECT INFO</p>
            <table style="width:100%;font-size:13px;border-collapse:collapse;">
                <tr><td style="color:#888;padding:5px 0;">Project</td><td style="color:#fff;font-weight:600;">Fire Volt</td></tr>
                <tr><td style="color:#888;padding:5px 0;">Team</td><td style="color:#ff8c00;font-weight:600;">{ab["team"]}</td></tr>
                <tr><td style="color:#888;padding:5px 0;">Version</td><td style="color:#fff;">{ab["version"]}</td></tr>
                <tr><td style="color:#888;padding:5px 0;">Year</td><td style="color:#fff;">{ab["date"]}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── ROW 4: SYSTEM HEALTH ─────────────────────────────────────────────────
    st.markdown('<div class="section-badge">SYSTEM HEALTH</div>', unsafe_allow_html=True)
    h1,h2,h3,h4 = st.columns(4)
    h1.metric("ESP-32",       "Online ✅")
    h2.metric("Motor Driver", "Active ✅")
    h3.metric("TEG Chain",    "Generating ✅")
    h4.metric("HEPA Filter",  "Running ✅" if st.session_state.fan_on else "Idle ⏸")

    st.divider()

    # ── ROW 6: SAVE STATUS ───────────────────────────────────────────────────
    st.markdown('<div class="section-badge">DATA SAVE STATUS</div>', unsafe_allow_html=True)
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("Voltage Data",  "✅ Saved" if os.path.exists(VOLTAGE_FILE) else "⏳ Default")
    s2.metric("Temp Data",     "✅ Saved" if os.path.exists(TEMP_FILE)    else "⏳ Default")
    s3.metric("Energy Data",   "✅ Saved" if os.path.exists(ENERGY_FILE)  else "⏳ Default")
    s4.metric("Soot Log",      "✅ Saved" if os.path.exists(SOOT_FILE)    else "⏳ Default")

