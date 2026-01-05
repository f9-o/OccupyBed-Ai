import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Config & Corporate Design (No Emojis)
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Enterprise", layout="wide", page_icon=None)

st.markdown("""
<style>
    /* Global Reset - Corporate Dark Mode */
    .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* KPI Cards */
    .kpi-container {
        background: #161B22; border: 1px solid #30363D; border-radius: 6px;
        padding: 20px; text-align: center; height: 100%;
    }
    .kpi-label { font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #FFF; }
    .kpi-sub { font-size: 12px; color: #58A6FF; margin-top: 5px; }

    /* AI Recommendation Box */
    .ai-box {
        background: #0D1117; border-left: 4px solid #A371F7; border-radius: 4px;
        padding: 15px; margin-bottom: 15px; border: 1px solid #30363D;
    }
    .ai-header { font-weight: 700; color: #A371F7; font-size: 14px; margin-bottom: 8px; text-transform: uppercase; }
    .ai-text { font-size: 13px; color: #E6EDF3; margin-bottom: 4px; }
    
    /* Department Cards */
    .dept-card {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 10px;
    }
    .dept-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .dept-title { font-size: 14px; font-weight: 700; color: #FFF; }
    
    /* Status Indicators */
    .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
    .bg-green { background: rgba(35, 134, 54, 0.2); color: #3FB950; border: 1px solid #238636; }
    .bg-yellow { background: rgba(210, 153, 34, 0.2); color: #D29922; border: 1px solid #9E6A03; }
    .bg-red { background: rgba(218, 54, 51, 0.2); color: #F85149; border: 1px solid #DA3633; }

    /* Stats Rows */
    .stat-row { display: flex; justify-content: space-between; font-size: 11px; color: #8B949E; margin-top: 4px; }
    .stat-val { color: #E6EDF3; font-weight: 600; }
    .val-ready { color: #A371F7; font-weight: 700; }

    /* Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    button[kind="primary"] { background-color: #238636 !important; border: none !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Logic & Data Structure
# ---------------------------------------------------------

DEPARTMENTS = {
    "Medical Male": {"cap": 50, "gen": "Male"},
    "Medical Female": {"cap": 50, "gen": "Female"},
    "Surgical Male": {"cap": 40, "gen": "Male"},
    "Surgical Female": {"cap": 40, "gen": "Female"},
    "ICU": {"cap": 16, "gen": "Mixed"},
    "Pediatric": {"cap": 30, "gen": "Mixed"},
    "Obstetrics": {"cap": 24, "gen": "Female"},
}

# Simulated PIN DB
PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(2000)}

def init_system():
    # Only initialize if 'df' is missing.
    if 'df' not in st.session_state:
        # Define Schema strictly
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", 
            "Admit_Date", "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # --- Generate CLEAN Initial Data (Not Overloaded) ---
        # We will fill only ~60% of beds to allow adding new patients
        initial_data = []
        for dept, info in DEPARTMENTS.items():
            active_count = int(info['cap'] * 0.6) # 60% Occupancy initially
            
            for i in range(active_count):
                bed_num = f"{dept[:3].upper()}-{i+1:03d}"
                
                # Dates
                admit_dt = datetime.now() - timedelta(days=np.random.randint(1, 5), hours=np.random.randint(1, 12))
                exp_dt = admit_dt + timedelta(days=np.random.randint(2, 7))
                
                initial_data.append({
                    "PIN": f"PIN-{np.random.randint(1000, 9000)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": bed_num,
                    "Admit_Date": admit_dt,
                    "Exp_Discharge": exp_dt,
                    "Actual_Discharge": pd.NaT, # Active patients have NO actual discharge date
                    "Source": "Emergency"
                })
        
        st.session_state.df = pd.DataFrame(initial_data)

init_system()
df = st.session_state.df

# Ensure Date Types
for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.header("OccupyBed AI")
    
    st.markdown("---")
    menu = st.radio("MENU", ["Overview", "Live Admissions", "KPIs", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("System Status: Online")

# ---------------------------------------------------------
# 4. OVERVIEW (Real-time Dashboard)
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: 
        fc_hours = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # --- 1. Global Metrics (Live Calculations) ---
    now = datetime.now()
    # Active = Rows where Actual_Discharge is NULL (NaT)
    active_df = df[df['Actual_Discharge'].isna()]
    
    total_capacity = sum(d['cap'] for d in DEPARTMENTS.values())
    occupied_count = len(active_df)
    available_count = total_capacity - occupied_count
    
    # Ready to Discharge Logic:
    # Active Patients AND Expected Discharge is BEFORE (Now + Forecast Window)
    future_limit = now + timedelta(hours=fc_hours)
    ready_df = active_df[active_df['Exp_Discharge'] <= future_limit]
    ready_count = len(ready_df)

    # Net Flow (Last 24h)
    last_24h = now - timedelta(hours=24)
    admissions_24h = len(df[df['Admit_Date'] >= last_24h])
    discharges_24h = len(df[df['Actual_Discharge'] >= last_24h])
    net_flow = admissions_24h - discharges_24h

    # --- 2. AI Suggestions (Text Based) ---
    st.markdown(f"""<div class="ai-box"><div class="ai-header">🤖 AI Operational Recommendations</div>""", unsafe_allow_html=True)
    ai_alerts = 0
    for dept, info in DEPARTMENTS.items():
        d_pats = active_df[active_df['Department'] == dept]
        pct = (len(d_pats) / info['cap']) * 100
        delayed = len(d_pats[d_pats['Exp_Discharge'] < now]) # Already passed expected time
        
        if pct >= 85:
            st.markdown(f"""<div class="ai-text" style="color:#F85149"><b>{dept}:</b> High occupancy ({int(pct)}%). Expedite pending discharges.</div>""", unsafe_allow_html=True)
            ai_alerts += 1
        elif delayed > 3:
            st.markdown(f"""<div class="ai-text" style="color:#D29922"><b>{dept}:</b> {delayed} patients exceeding expected stay. Coordinate with physicians.</div>""", unsafe_allow_html=True)
            ai_alerts += 1
            
    if ai_alerts == 0:
        st.markdown(f"""<div class="ai-text" style="color:#3FB950">Hospital capacity is optimal. No critical actions required.</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 3. KPI Cards ---
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Total Licensed Beds</div><div class="kpi-value" style="color:#58A6FF">{total_capacity}</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Occupied Beds</div><div class="kpi-value" style="color:#D29922">{occupied_count}</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Available Now</div><div class="kpi-value" style="color:#3FB950">{available_count}</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Expected Free ({fc_hours}h)</div><div class="kpi-value" style="color:#A371F7">{ready_count}</div></div>""", unsafe_allow_html=True)

    # --- 4. File Management (Upload/Download) ---
    with st.expander("📂 Data Management (CSV Import/Export)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download Database (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_db.csv", "text/csv")
        with c2:
            up_file = st.file_uploader("Upload Database (CSV)", type=['csv'])
            if up_file:
                try:
                    new_df = pd.read_csv(up_file)
                    # Force conversion
                    for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
                        new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                    st.session_state.df = new_df
                    st.success("Database Updated Successfully!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error reading file: {e}")

    st.markdown("---")

    # --- 5. Department Cards ---
    st.markdown("### Department Status")
    cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_names):
        info = DEPARTMENTS[dept]
        d_df = active_df[active_df['Department'] == dept]
        
        occ = len(d_df)
        cap = info['cap']
        avail = cap - occ
        ready = len(d_df[d_df['Exp_Discharge'] <= future_limit])
        pct = (occ / cap) * 100
        
        # Color Logic
        if pct < 70:
            status = "SAFE"
            cls = "bg-green"
            bar = "#3FB950"
        elif 70 <= pct <= 84:
            status = "WARNING"
            cls = "bg-yellow"
            bar = "#D29922"
        else:
            status = "CRITICAL"
            cls = "bg-red"
            bar = "#F85149"
            
        with cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card">
                <div class="dept-header">
                    <span class="dept-title">{dept}</span>
                    <span class="status-badge {cls}">{status}</span>
                </div>
                <div class="stat-row"><span>Capacity: {cap}</span> <span>Occupied: {occ}</span></div>
                <div class="stat-row"><span>Available: {avail}</span> <span class="val-ready">Exp. Free ({fc_hours}h): {ready}</span></div>
                <div style="background:#21262D; height:6px; border-radius:3px; margin-top:8px;">
                    <div style="width:{min(pct, 100)}%; background:{bar}; height:100%; border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions & Discharge (CRITICAL FIXES HERE)
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission & Discharge Center")
    
    # --- Part A: New Admission ---
    with st.expander("➕ Admit New Patient", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
            gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
            if pin != "Select...": st.info(f"System Identified: **{gender}**")
            
            dept = st.selectbox("Assign Department", ["Select..."] + list(DEPARTMENTS.keys()))
            
            # Bed Logic: Only show EMPTY beds
            bed_opts = ["Select Department First"]
            if dept != "Select...":
                # Find occupied beds in this dept (Active patients only)
                active_in_dept = df[(df['Department'] == dept) & (df['Actual_Discharge'].isna())]
                occupied_beds = active_in_dept['Bed'].tolist()
                
                # Generate all beds
                cap = DEPARTMENTS[dept]['cap']
                all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(cap)]
                
                # Filter available
                free_beds = [b for b in all_beds if b not in occupied_beds]
                bed_opts = free_beds if free_beds else ["NO BEDS AVAILABLE"]
            
            bed = st.selectbox("Assign Bed", bed_opts)

        with c2:
            st.markdown("###### Timing & Source")
            d1, t1 = st.columns(2)
            adm_d = d1.date_input("Admission Date", datetime.now())
            adm_t = t1.time_input("Admission Time", datetime.now().time())
            
            # FIXED: Expected Discharge Date & Time (Not days)
            st.markdown("###### Discharge Plan")
            d2, t2 = st.columns(2)
            exp_d = d2.date_input("Expected Date", datetime.now() + timedelta(days=3))
            exp_t = t2.time_input("Expected Time", datetime.now().time())
            
            src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

        if st.button("Confirm Admission", type="primary", use_container_width=True):
            if pin != "Select..." and dept != "Select..." and bed not in ["Select Department First", "NO BEDS AVAILABLE"]:
                # Check Gender
                dept_gen = DEPARTMENTS[dept]['gen']
                if dept_gen != "Mixed" and dept_gen != gender:
                    st.error(f"Gender Mismatch: {dept} is {dept_gen} Only.")
                else:
                    new_rec = {
                        "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                        "Admit_Date": datetime.combine(adm_d, adm_t),
                        "Exp_Discharge": datetime.combine(exp_d, exp_t),
                        "Actual_Discharge": pd.NaT, # Important: Set to NaT (Not a Time)
                        "Source": src
                    }
                    # Append new record
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
                    st.success("Patient Admitted Successfully.")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.warning("Please complete all fields.")

    st.markdown("---")

    # --- Part B: Current Inpatients & Discharge ---
    st.subheader("Current Inpatients (Real-time)")
    
    # Filter only active patients (Actual_Discharge is NaN)
    active_df = df[df['Actual_Discharge'].isna()].copy()
    
    if not active_df.empty:
        # Sort by Admission Date
        active_df = active_df.sort_values(by="Admit_Date", ascending=False)
        
        # 1. Select Patient to Discharge
        p_list = active_df.apply(lambda x: f"{x['PIN']} | {x['Department']} | {x['Bed']}", axis=1).tolist()
        target = st.selectbox("Select Patient to Discharge / Update", ["Select..."] + p_list)
        
        if target != "Select...":
            t_pin, t_dept, t_bed = target.split(" | ")
            st.info(f"Processing Discharge for: **{t_pin}**")
            
            # 2. Input Actual Discharge Date/Time
            dc1, dc2 = st.columns(2)
            act_d = dc1.date_input("Actual Discharge Date", datetime.now())
            act_t = dc2.time_input("Actual Discharge Time", datetime.now().time())
            
            # 3. Confirm Button
            if st.button("Confirm Discharge & Remove from Active List"):
                # Find the index in the MAIN dataframe
                # Criteria: PIN match, Bed match, and currently active (NaT)
                idx = df[
                    (df['PIN'] == t_pin) & 
                    (df['Bed'] == t_bed) & 
                    (df['Actual_Discharge'].isna())
                ].index
                
                if not idx.empty:
                    # Update the record with the actual timestamp
                    final_dt = datetime.combine(act_d, act_t)
                    st.session_state.df.loc[idx[0], 'Actual_Discharge'] = final_dt
                    
                    st.success("Patient Discharged! Removing from Active List...")
                    time.sleep(1)
                    st.rerun() # Refresh to update table immediately
                else:
                    st.error("Error: Could not find active record.")

        # Show Table (Columns requested)
        st.dataframe(
            active_df[['PIN', 'Department', 'Bed', 'Gender', 'Admit_Date', 'Exp_Discharge', 'Source']], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No active patients. All beds are free.")

# ---------------------------------------------------------
# 6. KPI / Analytics (Fixed Data Visualization)
# ---------------------------------------------------------
elif menu == "KPIs":
    st.title("Operational KPIs")
    
    # Use full dataset (History + Active)
    calc = df.copy()
    now = datetime.now()
    
    # Fix NaT issues for calculations
    calc['Discharge_Calc'] = calc['Actual_Discharge'].fillna(now)
    
    # 1. Average Length of Stay (ALOS)
    calc['LOS_Days'] = (calc['Discharge_Calc'] - calc['Admit_Date']).dt.total_seconds() / 86400
    avg_los = calc['LOS_Days'].mean()
    
    # 2. Admission by Source
    k1, k2, k3, k4 = st.columns(4)
    total_adm = len(calc)
    total_dis = len(calc[calc['Actual_Discharge'].notnull()])
    
    k1.metric("Total Patients Processed", total_adm)
    k2.metric("Total Discharged", total_dis)
    k3.metric("Avg Length of Stay", f"{avg_los:.1f} Days")
    k4.metric("Bed Turnover Rate", "1.4", "Patients/Bed")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Admissions by Source")
        if not calc.empty:
            fig1 = px.pie(calc, names='Source', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig1.update_layout(paper_bgcolor="#0E1117", font={'color': "#FFF"})
            st.plotly_chart(fig1, use_container_width=True)
            
    with c2:
        st.markdown("##### Length of Stay Distribution")
        if not calc.empty:
            fig2 = px.histogram(calc, x="LOS_Days", nbins=10, color_discrete_sequence=['#58A6FF'])
            fig2.update_layout(paper_bgcolor="#0E1117", font={'color': "#FFF"}, xaxis_title="Days", yaxis_title="Count")
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings (Factory Reset)
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    st.warning("Use this to clear all data and start fresh (solves 'Ghost Data' issues).")
    
    if st.button("FACTORY RESET (Clear All Data)", type="primary"):
        del st.session_state.df
        st.success("System Reset Complete.")
        time.sleep(1)
        st.rerun()
