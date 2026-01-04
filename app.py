import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Config & Enterprise Styling
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Command Center", layout="wide", page_icon="🏥")

# Forced Dark Theme & Advanced CSS (No Emojis)
st.markdown("""
<style>
    /* Global Settings */
    .stApp { background-color: #090C10; color: #E6EDF3; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* AI Recommendation Board */
    .ai-container {
        background: #161B22; border: 1px solid #30363D; border-left: 5px solid #A371F7;
        border-radius: 6px; padding: 15px; margin-bottom: 20px;
    }
    .ai-header { font-weight: bold; color: #A371F7; font-size: 16px; margin-bottom: 10px; }
    .ai-item { font-size: 13px; color: #E6EDF3; margin-bottom: 5px; border-bottom: 1px solid #21262D; padding-bottom: 3px; }
    .ai-dept { font-weight: bold; color: #58A6FF; }

    /* Department Cards (Strict Layout) */
    .dept-card {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px;
    }
    .dept-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .dept-title { font-size: 15px; font-weight: 700; color: #E6EDF3; }
    .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    
    /* Status Colors */
    .bg-green { background: #238636; color: white; }
    .bg-yellow { background: #D29922; color: white; }
    .bg-red { background: #DA3633; color: white; }
    
    .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px; color: #8B949E; }
    .stat-val { color: #E6EDF3; font-weight: 600; }
    .ready-val { color: #A371F7; font-weight: 700; }

    /* Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Logic & Data Model
# ---------------------------------------------------------

DEPARTMENTS = {
    "Medical Male": {"cap": 50, "gen": "Male", "overflow": "Surgical Male"},
    "Medical Female": {"cap": 50, "gen": "Female", "overflow": "Surgical Female"},
    "Surgical Male": {"cap": 40, "gen": "Male", "overflow": "Medical Male"},
    "Surgical Female": {"cap": 40, "gen": "Female", "overflow": "Medical Female"},
    "ICU": {"cap": 16, "gen": "Mixed", "overflow": "HDU"},
    "Pediatric": {"cap": 30, "gen": "Mixed", "overflow": "None"},
    "Obstetrics": {"cap": 24, "gen": "Female", "overflow": "Gynae"},
}

# Simulated Patient Database (PIN -> Gender)
PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(1000)}

def init_system():
    if 'df' not in st.session_state:
        # Create Data Structure matching requirements
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", "Admit_Date", 
            "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # Populate with Initial Data
        data = []
        for dept, info in DEPARTMENTS.items():
            count = int(info['cap'] * np.random.uniform(0.6, 0.9)) # 60-90% occupancy
            for i in range(count):
                bed_n = i + 1
                adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 10))
                
                # Logic to create some ready for discharge
                if np.random.random() < 0.2:
                    exp = datetime.now() + timedelta(hours=np.random.randint(1, 24))
                else:
                    exp = adm + timedelta(days=np.random.randint(2, 7))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(2000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": f"{dept[:3].upper()}-{bed_n:03d}",
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": None, # Active
                    "Source": np.random.choice(["Emergency", "Elective", "Transfer"])
                })
        st.session_state.df = pd.DataFrame(data)

init_system()
df = st.session_state.df

# ---------------------------------------------------------
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.header("OccupyBed AI")
        
    st.markdown("---")
    menu = st.radio("MAIN MENU", ["Overview (Command Center)", "Live Admissions", "Operational KPIs", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    st.caption(f"System Online\nServer: JED-HOSP-01")

# ---------------------------------------------------------
# 4. Overview (Command Center) - Highly Customized
# ---------------------------------------------------------
if menu == "Overview (Command Center)":
    # Header & Forecast Window
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Overview")
    with c2: 
        # Forecast Window (User Selects hours)
        fc_hours = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # --- 1. Global Calculations ---
    now = datetime.now()
    active = df[df['Actual_Discharge'].isnull()]
    future_limit = now + timedelta(hours=fc_hours)
    
    # Net Flow (Last 24h)
    last_24 = now - timedelta(hours=24)
    adm_24 = len(df[df['Admit_Date'] >= last_24])
    dis_24 = len(df[(df['Actual_Discharge'] >= last_24)])
    net_flow = adm_24 - dis_24
    
    # Total Forecast
    total_ready = active[active['Exp_Discharge'] <= future_limit].shape[0]

    # --- 2. AI Suggested Actions (Top Section) ---
    st.markdown(f"""
    <div class="ai-container">
        <div class="ai-header">🤖 AI Suggested Actions (Live Analysis)</div>
    """, unsafe_allow_html=True)
    
    # Generate Logic-based Sentences
    ai_alerts = []
    for dept, info in DEPARTMENTS.items():
        d_df = active[active['Department'] == dept]
        occ = len(d_df)
        cap = info['cap']
        pct = (occ/cap)*100
        delayed = d_df[d_df['Exp_Discharge'] < now].shape[0]
        
        if pct > 85:
            st.markdown(f"""<div class="ai-item"><span class="ai-dept">{dept}:</span> High occupancy detected ({int(pct)}%). Consider diverting to {info['overflow']}.</div>""", unsafe_allow_html=True)
        elif delayed > 3:
            st.markdown(f"""<div class="ai-item"><span class="ai-dept">{dept}:</span> High delayed discharge rate ({delayed} patients). Review pending approvals.</div>""", unsafe_allow_html=True)
        elif pct < 70:
            st.markdown(f"""<div class="ai-item"><span class="ai-dept">{dept}:</span> Available capacity detected. Elective admissions can proceed safely.</div>""", unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 3. Hospital Level KPIs ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Net Flow (24h)", f"{net_flow:+d}", "Adm vs Disc")
    k2.metric("Total Forecast Free", total_ready, f"Next {fc_hours}h")
    k3.metric("Current Inpatients", len(active))
    k4.metric("Bed Turnover Rate", "1.2", "Daily Avg")

    # --- 4. File Upload/Download (Placed here as requested) ---
    with st.expander("📂 File Operations (Upload / Download)", expanded=False):
        f1, f2 = st.columns(2)
        with f1:
            st.download_button("Download Current Report (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_data.csv", "text/csv")
        with f2:
            up_file = st.file_uploader("Upload External Data (CSV)", type=['csv'])
            if up_file:
                try:
                    new_df = pd.read_csv(up_file)
                    for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
                        new_df[col] = pd.to_datetime(new_df[col])
                    st.session_state.df = new_df
                    st.success("File Loaded Successfully")
                    st.rerun()
                except: st.error("Invalid CSV Format")

    st.markdown("---")

    # --- 5. Department Grid (The Core Request) ---
    st.markdown("### Department Status & Forecast")
    
    d_cols = st.columns(3)
    dept_list = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_list):
        info = DEPARTMENTS[dept]
        d_data = active[active['Department'] == dept]
        
        # Stats
        occ = len(d_data)
        cap = info['cap']
        avail = cap - occ
        # Ready to discharge based on user selected window
        ready = d_data[d_data['Exp_Discharge'] <= future_limit].shape[0]
        pct = (occ / cap) * 100
        
        # Color Logic (70% - 85%)
        if pct < 70:
            status = "SAFE"
            color_cls = "bg-green"
            bar_color = "#238636"
        elif 70 <= pct <= 84:
            status = "WARNING"
            color_cls = "bg-yellow"
            bar_color = "#D29922"
        else: # > 85%
            status = "CRITICAL"
            color_cls = "bg-red"
            bar_color = "#DA3633"
            
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card">
                <div class="dept-title-row">
                    <span class="dept-title">{dept}</span>
                    <span class="status-badge {color_cls}">{status}</span>
                </div>
                <div class="stat-grid">
                    <span>Total Beds:</span> <span class="stat-val">{cap}</span>
                    <span>Occupied:</span> <span class="stat-val">{occ}</span>
                    <span>Available:</span> <span class="stat-val">{avail}</span>
                    <span>Ready ({fc_hours}h):</span> <span class="ready-val">{ready}</span>
                </div>
                <div style="background:#21262D; height:6px; border-radius:3px; margin-top:10px;">
                    <div style="width:{min(pct, 100)}%; background-color:{bar_color}; height:100%; border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions (Strict Input Logic)
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission Center")
    
    # Form Layout
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Patient Details")
        # PIN Selection
        pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
        
        # Auto-Gender (No Input)
        gender = "Unknown"
        if pin != "Select...":
            gender = PATIENT_DB.get(pin, "Unknown")
            st.info(f"System Identified: **{gender}**")
            
        # Department
        dept = st.selectbox("Assign Department", ["Select..."] + list(DEPARTMENTS.keys()))
        
        # Logic: Filter Beds (Occupied beds must NOT appear)
        bed_options = ["Select Department First"]
        if dept != "Select...":
            # Gender Check
            rule = DEPARTMENTS[dept]['gen']
            if rule != "Mixed" and rule != gender:
                st.error(f"⛔ Conflict: {dept} is {rule} Only.")
            
            # Bed Filter
            active_beds = df[(df['Department'] == dept) & (df['Actual_Discharge'].isnull())]['Bed'].tolist()
            all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
            free_beds = [b for b in all_beds if b not in active_beds]
            bed_options = free_beds if free_beds else ["NO BEDS AVAILABLE"]
            
        bed = st.selectbox("Assign Bed", bed_options)

    with c2:
        st.subheader("Admission Timing")
        # Admission Date/Time
        c_d1, c_t1 = st.columns(2)
        adm_date = c_d1.date_input("Admit Date", datetime.now())
        adm_time = c_t1.time_input("Admit Time", datetime.now().time())
        
        # Source
        src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])
        
        st.write("---")
        st.subheader("Discharge Plan")
        # Expected Discharge Date/Time
        c_d2, c_t2 = st.columns(2)
        exp_date = c_d2.date_input("Expected Date", datetime.now() + timedelta(days=3))
        exp_time = c_t2.time_input("Expected Time", datetime.now().time())

    # Submit Button
    if st.button("Confirm Admission", type="primary", use_container_width=True):
        if pin != "Select..." and dept != "Select..." and bed not in ["Select Department First", "NO BEDS AVAILABLE"]:
            new_rec = {
                "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                "Admit_Date": datetime.combine(adm_date, adm_time),
                "Exp_Discharge": datetime.combine(exp_date, exp_time),
                "Actual_Discharge": None,
                "Source": src
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
            st.success("Patient Admitted Successfully")
            time.sleep(0.5)
            st.rerun()
        else:
            st.warning("Please check all fields.")

    # Table (Requested to be at the bottom)
    st.markdown("### 🏥 Current Inpatient List")
    active_df = df[df['Actual_Discharge'].isnull()].sort_values(by="Admit_Date", ascending=False)
    st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Gender', 'Admit_Date', 'Exp_Discharge']], use_container_width=True)

# ---------------------------------------------------------
# 6. Operational KPIs (The Missing Stats)
# ---------------------------------------------------------
elif menu == "Operational KPIs":
    st.title("Operational Performance Indicators")
    
    # Calculations
    calc = df.copy()
    now = datetime.now()
    
    # 1. Admission Rate (Daily Average)
    days_range = (calc['Admit_Date'].max() - calc['Admit_Date'].min()).days + 1
    if days_range < 1: days_range = 1
    adm_rate = len(calc) / days_range
    
    # 2. Discharge Rate
    discharges = calc[calc['Actual_Discharge'].notnull()]
    disc_rate = len(discharges) / days_range
    
    # 3. Bed Turnover (Discharges / Total Beds)
    total_beds = sum(d['cap'] for d in DEPARTMENTS.values())
    turnover = len(discharges) / total_beds
    
    # 4. Ready to Discharge %
    active = calc[calc['Actual_Discharge'].isnull()]
    ready_count = active[active['Exp_Discharge'] < now].shape[0]
    ready_pct = (ready_count / len(active) * 100) if len(active) > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Admission Rate", f"{adm_rate:.1f}", "Patients/Day")
    k2.metric("Discharge Rate", f"{disc_rate:.1f}", "Patients/Day")
    k3.metric("Bed Turnover", f"{turnover:.2f}", "Rounds/Bed")
    k4.metric("Delayed Discharges", f"{ready_pct:.1f}%", f"{ready_count} Patients")
    
    st.markdown("---")
    
    # Charts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Net Flow Analysis (Adm vs Disc)")
        daily_adm = calc.groupby(calc['Admit_Date'].dt.date).size().reset_index(name='Admissions')
        daily_disc = discharges.groupby(discharges['Actual_Discharge'].dt.date).size().reset_index(name='Discharges')
        
        if not daily_adm.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily_adm['Admit_Date'], y=daily_adm['Admissions'], name='Inflow', marker_color='#58A6FF'))
            if not daily_disc.empty:
                fig.add_trace(go.Bar(x=daily_disc['Actual_Discharge'], y=daily_disc['Discharges'], name='Outflow', marker_color='#238636'))
            fig.update_layout(barmode='group', paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font={'color': "#E6EDF3"})
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.markdown("##### Bottleneck Analysis (Occupancy Heatmap)")
        # Simple bar chart for occupancy
        dept_occ = active['Department'].value_counts().reset_index()
        dept_occ.columns = ['Department', 'Count']
        dept_occ['Capacity'] = dept_occ['Department'].apply(lambda x: DEPARTMENTS[x]['cap'])
        dept_occ['%'] = (dept_occ['Count'] / dept_occ['Capacity']) * 100
        
        fig2 = px.bar(dept_occ, x='Department', y='%', color='%', color_continuous_scale=['green', 'yellow', 'red'])
        fig2.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font={'color': "#E6EDF3"})
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("Settings")
    if st.button("Factory Reset (Clear Data)", type="primary"):
        del st.session_state.df
        st.rerun()
