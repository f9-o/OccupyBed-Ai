import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Config & High-End Design
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Enterprise", layout="wide", page_icon="🏥")

st.markdown("""
<style>
    /* Global Settings */
    .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* Glowing Text Effect */
    @keyframes glow {
        from { text-shadow: 0 0 2px #fff, 0 0 5px #238636; }
        to { text-shadow: 0 0 5px #fff, 0 0 10px #238636; }
    }
    .glow-header { font-size: 22px; font-weight: 800; animation: glow 2s infinite alternate; text-align: center; color: #FFF; margin-bottom: 20px; }

    /* KPI Cards (Dashboard Look) */
    .kpi-card {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 8px;
        padding: 20px; text-align: center; height: 100%; position: relative;
    }
    .kpi-title { font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-size: 30px; font-weight: 800; color: #FFF; margin: 5px 0; }
    .kpi-sub { font-size: 12px; font-weight: 600; }
    
    /* Status Colors */
    .c-green { color: #3FB950; } 
    .c-yellow { color: #D29922; } 
    .c-red { color: #F85149; } 
    .c-blue { color: #58A6FF; }

    /* Department Cards */
    .dept-box {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 10px; transition: transform 0.2s;
    }
    .dept-box:hover { border-color: #58A6FF; transform: scale(1.01); }
    .dept-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .dept-name { font-weight: 700; font-size: 14px; color: #FFF; }
    
    /* Status Badge */
    .status-badge { padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; text-transform: uppercase; }
    .bg-green { background: rgba(63, 185, 80, 0.15); color: #3FB950; border: 1px solid #238636; }
    .bg-yellow { background: rgba(210, 153, 34, 0.15); color: #D29922; border: 1px solid #9E6A03; }
    .bg-red { background: rgba(248, 81, 73, 0.15); color: #F85149; border: 1px solid #DA3633; }

    /* Stats Grid inside Card */
    .stat-row { display: flex; justify-content: space-between; font-size: 12px; color: #8B949E; margin-bottom: 4px; }
    .stat-num { font-weight: 700; color: #E6EDF3; }
    .ready-num { font-weight: 700; color: #A371F7; }

    /* AI Box */
    .ai-box { background: #161B22; border-left: 4px solid #A371F7; padding: 15px; border-radius: 0 4px 4px 0; margin-bottom: 20px; }
    .ai-item { font-size: 13px; color: #E6EDF3; margin-bottom: 5px; border-bottom: 1px solid #21262D; padding-bottom: 5px; }

    /* Inputs Override */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    button[kind="primary"] { background: linear-gradient(90deg, #238636, #2EA043) !important; border: none !important; color: white !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Data Logic (Corrected & Simplified)
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

PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(1000)}

def init_system():
    if 'df' not in st.session_state:
        # Define Schema
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", 
            "Admit_Date", "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # --- Generate Logical Data (Not Full) ---
        data = []
        for dept, info in DEPARTMENTS.items():
            # Generate only 40-60% occupancy initially to leave room
            count = int(info['cap'] * np.random.uniform(0.4, 0.6))
            for i in range(count):
                bed_n = f"{dept[:3].upper()}-{i+1:03d}"
                adm = datetime.now() - timedelta(days=np.random.randint(1, 5), hours=np.random.randint(1, 10))
                exp = adm + timedelta(days=np.random.randint(2, 7))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(2000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": bed_n,
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": pd.NaT, # Active
                    "Source": np.random.choice(["Emergency", "Elective"])
                })
        st.session_state.df = pd.DataFrame(data)

init_system()
df = st.session_state.df

# Fix Date Types
for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.markdown("<div class='glow-header'>🏥 OccupyBed AI</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    menu = st.radio("MAIN MENU", ["Overview", "Live Admissions", "Operational Analytics", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    
    # Global Filter (Optional, adds flexibility)
    st.caption("Admin Logged In\nSystem Online 🟢")

# ---------------------------------------------------------
# 4. OVERVIEW (Dashboard)
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: 
        fc = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # --- Calculations (Real Logic) ---
    now = datetime.now()
    active_df = df[df['Actual_Discharge'].isna()] # Only Active Patients
    future_limit = now + timedelta(hours=fc)
    
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    occ_count = len(active_df)
    avail_count = total_cap - occ_count
    ready_count = len(active_df[active_df['Exp_Discharge'] <= future_limit])
    
    # --- AI Action Center ---
    st.markdown(f"""<div class="ai-box"><div style="color:#A371F7; font-weight:bold; margin-bottom:10px;">🤖 AI Suggested Actions</div>""", unsafe_allow_html=True)
    
    ai_msgs = []
    for dept, info in DEPARTMENTS.items():
        d_pats = active_df[active_df['Department'] == dept]
        occ = len(d_pats)
        pct = (occ / info['cap']) * 100
        
        if pct >= 85:
            st.markdown(f"""<div class="ai-item"><span style="color:#F85149"><b>{dept}:</b></span> High occupancy ({int(pct)}%). Consider accelerating discharge for stable patients.</div>""", unsafe_allow_html=True)
            ai_msgs.append(1)
        elif pct < 60:
            st.markdown(f"""<div class="ai-item"><span style="color:#3FB950"><b>{dept}:</b></span> Available capacity. Elective admissions can proceed safely.</div>""", unsafe_allow_html=True)
            ai_msgs.append(1)
            
    if not ai_msgs: st.markdown("""<div class="ai-item">Operations are stable. No critical actions needed.</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- KPI Cards ---
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Total Licensed Beds</div><div class="kpi-value c-blue">{total_cap}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Occupied Beds</div><div class="kpi-value c-yellow">{occ_count}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Available Now</div><div class="kpi-value c-green">{avail_count}</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Expected Free ({fc}h)</div><div class="kpi-value" style="color:#A371F7">{ready_count}</div></div>""", unsafe_allow_html=True)

    # --- Data Operations (Upload/Download) ---
    with st.expander("📂 Data Management (Import / Export CSV)", expanded=False):
        c_dl, c_ul = st.columns(2)
        with c_dl:
            st.download_button("Download Data (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_data.csv", "text/csv")
        with c_ul:
            up_file = st.file_uploader("Upload Data (CSV)", type=['csv'])
            if up_file:
                try:
                    new_df = pd.read_csv(up_file)
                    for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']: 
                        new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                    st.session_state.df = new_df
                    st.success("System Data Updated!")
                    time.sleep(1)
                    st.rerun()
                except: st.error("Error reading file")

    st.markdown("---")

    # --- Department Status Grid ---
    st.markdown("### Department Status")
    d_cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_names):
        info = DEPARTMENTS[dept]
        d_df = active_df[active_df['Department'] == dept]
        
        # Real Numbers
        d_occ = len(d_df)
        d_cap = info['cap']
        d_avail = d_cap - d_occ
        d_ready = len(d_df[d_df['Exp_Discharge'] <= future_limit])
        d_pct = (d_occ / d_cap) * 100
        
        # Color Logic
        if d_pct < 70: status, cls, bar = "SAFE", "bg-green", "#3FB950"
        elif 70 <= d_pct <= 84: status, cls, bar = "WARNING", "bg-yellow", "#D29922"
        else: status, cls, bar = "CRITICAL", "bg-red", "#F85149"
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-box">
                <div class="dept-header">
                    <span class="dept-name">{dept}</span>
                    <span class="status-badge {cls}">{status}</span>
                </div>
                <div class="stat-row"><span>Total Beds:</span> <span class="stat-num">{d_cap}</span></div>
                <div class="stat-row"><span>Occupied:</span> <span class="stat-num">{d_occ}</span></div>
                <div class="stat-row"><span>Available:</span> <span class="stat-num">{d_avail}</span></div>
                <div class="stat-row"><span>Ready ({fc}h):</span> <span class="ready-num">{d_ready}</span></div>
                <div style="background:#21262D; height:5px; border-radius:3px; margin-top:8px;">
                    <div style="width:{min(d_pct, 100)}%; background:{bar}; height:100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions & Discharge (THE FIX)
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission & Discharge Center")
    
    # --- Part A: Admission Form ---
    with st.expander("➕ New Admission Entry", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
            gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
            if pin != "Select...": st.info(f"System Identified: **{gender}**")
            
            dept = st.selectbox("Assign Department", ["Select..."] + list(DEPARTMENTS.keys()))
            
            # Logic: Filter Occupied Beds
            bed_opts = ["Select Dept"]
            if dept != "Select...":
                if DEPARTMENTS[dept]['gen'] != "Mixed" and DEPARTMENTS[dept]['gen'] != gender:
                    st.error(f"Gender Mismatch: {dept} is {DEPARTMENTS[dept]['gen']} Only.")
                
                # Get beds currently in use (Active)
                occ_beds = df[(df['Department'] == dept) & (df['Actual_Discharge'].isna())]['Bed'].tolist()
                all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
                # Available beds
                free_beds = [b for b in all_beds if b not in occ_beds]
                bed_opts = free_beds if free_beds else ["NO BEDS AVAILABLE"]
            
            bed = st.selectbox("Assign Bed", bed_opts)

        with c2:
            # Date & Time Pickers (As requested)
            st.markdown("###### Admission Timing")
            col_d1, col_t1 = st.columns(2)
            adm_d = col_d1.date_input("Date", datetime.now())
            adm_t = col_t1.time_input("Time", datetime.now().time())
            
            st.markdown("###### Expected Discharge")
            col_d2, col_t2 = st.columns(2)
            exp_d = col_d2.date_input("Exp Date", datetime.now() + timedelta(days=3))
            exp_t = col_t2.time_input("Exp Time", datetime.now().time())
            
            src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

        if st.button("Confirm Admission", type="primary", use_container_width=True):
            if pin != "Select..." and dept != "Select..." and bed not in ["Select Dept", "NO BEDS AVAILABLE"]:
                new_rec = {
                    "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                    "Admit_Date": datetime.combine(adm_d, adm_t),
                    "Exp_Discharge": datetime.combine(exp_d, exp_t),
                    "Actual_Discharge": pd.NaT, # Active
                    "Source": src
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
                st.success(f"Patient {pin} Admitted to {bed}.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("Please check inputs.")

    st.markdown("---")

    # --- Part B: Discharge Management (The Fix) ---
    st.subheader("Current Inpatients (Real-time List)")
    active_df = df[df['Actual_Discharge'].isna()].sort_values(by="Admit_Date", ascending=False)
    
    if not active_df.empty:
        # 1. Select Patient to Discharge
        p_list = active_df.apply(lambda x: f"{x['PIN']} | {x['Department']} | {x['Bed']}", axis=1).tolist()
        target = st.selectbox("Select Patient to Discharge", ["Select..."] + p_list)
        
        if target != "Select...":
            t_pin, t_dept, t_bed = target.split(" | ")
            col_dis1, col_dis2 = st.columns(2)
            
            # 2. Input Actual Discharge Time
            with col_dis1:
                act_d = st.date_input("Actual Discharge Date", datetime.now())
            with col_dis2:
                act_t = st.time_input("Actual Discharge Time", datetime.now().time())
            
            # 3. Confirm Button
            if st.button(f"Confirm Discharge for {t_pin}"):
                # Find index in main DF
                idx = df[(df['PIN'] == t_pin) & (df['Actual_Discharge'].isna())].index
                if not idx.empty:
                    st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(act_d, act_t)
                    st.success("Patient Discharged & Removed from Active List.")
                    time.sleep(1)
                    st.rerun()
        
        # Show Active Table
        st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Admit_Date', 'Exp_Discharge', 'Source']], use_container_width=True)
    else:
        st.info("No active patients.")

# ---------------------------------------------------------
# 6. Operational Analytics (KPIs) - Visual Fix
# ---------------------------------------------------------
elif menu == "Operational Analytics":
    st.title("Operational KPIs")
    
    calc = df.copy()
    now = datetime.now()
    
    # 1. Top Metrics
    total_adm = len(calc)
    total_dis = len(calc[calc['Actual_Discharge'].notnull()])
    
    # Bed Turnover
    total_beds = sum(d['cap'] for d in DEPARTMENTS.values())
    turnover = total_dis / total_beds if total_beds > 0 else 0
    
    # ALOS (Average Length of Stay)
    def get_los(r):
        end = r['Actual_Discharge'] if pd.notnull(r['Actual_Discharge']) else now
        return (end - r['Admit_Date']).total_seconds() / 86400
    calc['LOS'] = calc.apply(get_los, axis=1)
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Total Admissions</div><div class="kpi-value">{total_adm}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Total Discharges</div><div class="kpi-value">{total_dis}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Avg LOS</div><div class="kpi-value">{calc['LOS'].mean():.1f} <span style="font-size:12px">Days</span></div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Bed Turnover</div><div class="kpi-value">{turnover:.2f}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # 2. Charts (Visuals like image provided)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("##### Occupancy Distribution")
        # Donut Chart
        active = calc[calc['Actual_Discharge'].isna()]
        if not active.empty:
            dept_counts = active['Department'].value_counts().reset_index()
            dept_counts.columns = ['Department', 'Count']
            fig = px.pie(dept_counts, values='Count', names='Department', hole=0.7, color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_layout(showlegend=False, paper_bgcolor="#0E1117", font={'color': "white"}, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.markdown("##### Length of Stay by Department")
        if not calc.empty:
            fig2 = px.box(calc, x="Department", y="LOS", color="Department", color_discrete_sequence=px.colors.qualitative.Bold)
            fig2.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font={'color': "white"}, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    st.warning("⚠️ **Factory Reset:** Use this to clear all data and start fresh (Fixes 'Ghost Data').")
    if st.button("FACTORY RESET (Clear Database)", type="primary"):
        del st.session_state.df
        st.success("System Reset Complete.")
        time.sleep(1)
        st.rerun()
