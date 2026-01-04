import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Configuration & Enterprise Design
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Command Center", layout="wide", page_icon=None)

# CSS: Professional, Dark, No Emojis, Corporate Look
st.markdown("""
<style>
    /* Global Reset */
    .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* AI Board Section */
    .ai-container {
        background: #161B22; border: 1px solid #30363D; border-left: 4px solid #A371F7;
        border-radius: 4px; padding: 20px; margin-bottom: 20px;
    }
    .ai-title { font-size: 14px; font-weight: 700; color: #A371F7; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px;}
    .ai-item { font-size: 13px; color: #E6EDF3; margin-bottom: 8px; border-bottom: 1px solid #21262D; padding-bottom: 6px; }
    .ai-dept { font-weight: 700; color: #58A6FF; margin-right: 8px; }

    /* Department Cards */
    .dept-card {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 16px; margin-bottom: 12px; transition: transform 0.2s;
    }
    .dept-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .dept-title { font-size: 15px; font-weight: 700; color: #F0F6FC; }
    
    /* Metrics Grid inside Card */
    .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
    .metric-box { text-align: center; background: #161B22; padding: 8px; border-radius: 4px; }
    .m-label { font-size: 10px; color: #8B949E; text-transform: uppercase; }
    .m-val { font-size: 16px; font-weight: 700; color: #E6EDF3; }
    .m-highlight { color: #A371F7; } /* For Forecast */

    /* Status Badges (CSS Only, No Emojis) */
    .status-badge { padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
    .status-green { background: rgba(35, 134, 54, 0.2); color: #3FB950; border: 1px solid #238636; }
    .status-yellow { background: rgba(210, 153, 34, 0.2); color: #D29922; border: 1px solid #9E6A03; }
    .status-red { background: rgba(218, 54, 51, 0.2); color: #F85149; border: 1px solid #DA3633; }

    /* KPI Top Cards */
    .kpi-container { background: #161B22; padding: 20px; border-radius: 6px; border: 1px solid #30363D; text-align: center; }
    .kpi-head { font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-num { font-size: 28px; font-weight: 700; color: #F0F6FC; margin: 5px 0; }
    .kpi-sub { font-size: 11px; color: #58A6FF; }

    /* Inputs & UI overrides */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    [data-testid="stDataFrame"] { border: 1px solid #30363D; }
    button[kind="primary"] { background-color: #238636 !important; border: none !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Data Model & Logic
# ---------------------------------------------------------

DEPARTMENTS = {
    "Medical - Male": {"cap": 50, "gen": "Male", "code": "MED-M"},
    "Medical - Female": {"cap": 50, "gen": "Female", "code": "MED-F"},
    "Surgical - Male": {"cap": 40, "gen": "Male", "code": "SURG-M"},
    "Surgical - Female": {"cap": 40, "gen": "Female", "code": "SURG-F"},
    "ICU": {"cap": 16, "gen": "Mixed", "code": "ICU"},
    "Pediatric": {"cap": 30, "gen": "Mixed", "code": "PED"},
    "Obstetrics & Gynecology": {"cap": 24, "gen": "Female", "code": "OBGYN"},
}

# Simulated Patient DB (PIN -> Gender)
PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(1000)}

def init_system():
    if 'df' not in st.session_state:
        # Create Schema
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", "Admit_Date", 
            "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # Populate with Synthetic Data
        data = []
        for dept, info in DEPARTMENTS.items():
            # Random occupancy between 60% and 90%
            count = int(info['cap'] * np.random.uniform(0.6, 0.9)) 
            for i in range(count):
                bed_n = f"{info['code']}-{i+1:03d}"
                
                # Realistic dates
                adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 10))
                
                # Some are ready for discharge soon, others later
                if np.random.random() < 0.3: # 30% leaving soon
                    exp = datetime.now() + timedelta(hours=np.random.randint(2, 48))
                else:
                    exp = adm + timedelta(days=np.random.randint(3, 8))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(2000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": bed_n,
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": None, # Active
                    "Source": np.random.choice(["Emergency", "Elective", "Transfer"])
                })
        st.session_state.df = pd.DataFrame(data)

init_system()
df = st.session_state.df

# Ensure Datetime Types
df['Admit_Date'] = pd.to_datetime(df['Admit_Date'], errors='coerce')
df['Exp_Discharge'] = pd.to_datetime(df['Exp_Discharge'], errors='coerce')
df['Actual_Discharge'] = pd.to_datetime(df['Actual_Discharge'], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.header("OccupyBed AI")
        
    st.markdown("---")
    menu = st.radio("NAVIGATION", ["Overview", "Live Admissions", "Operational KPIs", "Settings"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("""
    <div style='font-size:12px; color:#8B949E'>
        <b>USER:</b> Administrator<br>
        <b>UNIT:</b> Main Hospital<br>
        <b>STATUS:</b> Online
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. OVERVIEW (Command Center)
# ---------------------------------------------------------
if menu == "Overview":
    # 1. Header & Forecast Window
    c_head, c_fc = st.columns([3, 1])
    with c_head: st.title("Hospital Command Center")
    with c_fc: 
        fc_val = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # --- Calculations ---
    now = datetime.now()
    active = df[df['Actual_Discharge'].isnull()]
    future_limit = now + timedelta(hours=fc_val)
    
    # 2. AI Action Center (Dynamic Text Logic)
    st.markdown(f"""<div class="ai-container"><div class="ai-title">AI Suggested Actions (Real-time)</div>""", unsafe_allow_html=True)
    
    ai_count = 0
    for dept, info in DEPARTMENTS.items():
        d_data = active[active['Department'] == dept]
        occ = len(d_data)
        pct = (occ / info['cap']) * 100
        delayed = d_data[d_data['Exp_Discharge'] < now].shape[0]
        
        # Text Logic
        if pct >= 85:
            st.markdown(f"""<div class="ai-item"><span class="ai-dept">{dept}:</span> High occupancy detected ({int(pct)}%). Consider accelerating discharge for stable patients.</div>""", unsafe_allow_html=True)
            ai_count += 1
        elif delayed > 3:
            st.markdown(f"""<div class="ai-item"><span class="ai-dept">{dept}:</span> High delayed discharge rate ({delayed}). Review pending discharge approvals and coordination.</div>""", unsafe_allow_html=True)
            ai_count += 1
        elif pct < 70:
            st.markdown(f"""<div class="ai-item"><span class="ai-dept">{dept}:</span> Available capacity detected. Elective admissions can proceed safely.</div>""", unsafe_allow_html=True)
            ai_count += 1
            
    if ai_count == 0: st.markdown("""<div class="ai-item">System operating within normal parameters.</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. File Operations (Upload / Download)
    with st.expander("Data Operations (Upload / Download)", expanded=False):
        f1, f2 = st.columns(2)
        with f1:
            st.download_button("Download Current State (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_data.csv", "text/csv")
        with f2:
            up_file = st.file_uploader("Upload Data File (CSV)", type=['csv'])
            if up_file:
                try:
                    new_df = pd.read_csv(up_file)
                    for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
                        new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                    st.session_state.df = new_df
                    st.success("System Updated Successfully")
                    st.rerun()
                except: st.error("Invalid File Format")

    st.markdown("---")

    # 4. Department Grid (The Cards)
    st.markdown("### Department Status Matrix")
    d_cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_names):
        info = DEPARTMENTS[dept]
        d_df = active[active['Department'] == dept]
        
        # Stats
        total = info['cap']
        occupied = len(d_df)
        available = total - occupied
        # Ready to discharge logic based on Forecast Window
        ready = d_df[d_df['Exp_Discharge'] <= future_limit].shape[0]
        
        # Color & Status Logic
        occupancy_pct = (occupied / total) * 100
        
        if occupancy_pct < 70:
            status_txt = "SAFE"
            status_cls = "status-green"
            bar_col = "#238636"
        elif 70 <= occupancy_pct <= 84:
            status_txt = "WARNING"
            status_cls = "status-yellow"
            bar_col = "#D29922"
        else: # >= 85
            status_txt = "CRITICAL"
            status_cls = "status-red"
            bar_col = "#DA3633"
            
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card">
                <div class="dept-header">
                    <span class="dept-title">{dept}</span>
                    <span class="status-badge {status_cls}">{status_txt}</span>
                </div>
                <div class="metric-grid">
                    <div class="metric-box"><div class="m-label">Total Beds</div><div class="m-val">{total}</div></div>
                    <div class="metric-box"><div class="m-label">Occupied</div><div class="m-val">{occupied}</div></div>
                    <div class="metric-box"><div class="m-label">Available</div><div class="m-val">{available}</div></div>
                    <div class="metric-box"><div class="m-label" style="color:#A371F7">Ready ({fc_val}h)</div><div class="m-val m-highlight">{ready}</div></div>
                </div>
                <div style="background:#21262D; height:6px; border-radius:3px; margin-top:8px;">
                    <div style="width:{min(occupancy_pct, 100)}%; background-color:{bar_col}; height:100%; border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission Center")
    
    # Form
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Patient Details")
        # 1. PIN Selection
        pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
        
        # 2. Gender Logic (Auto-detected, Hidden in UI if valid)
        gender = "Unknown"
        if pin != "Select...":
            gender = PATIENT_DB.get(pin, "Unknown")
            st.info(f"System Identified: **{gender}**")
            
        # 3. Department Selection (Filter based on Gender)
        valid_depts = []
        for d, info in DEPARTMENTS.items():
            if info['gen'] == "Mixed" or info['gen'] == gender:
                valid_depts.append(d)
                
        dept_options = ["Select Department"] + valid_depts
        dept = st.selectbox("Assign Department", dept_options if pin != "Select..." else ["Select PIN First"])
        
        # 4. Bed Selection (Only Available Beds)
        bed_opts = ["Select Department First"]
        if dept not in ["Select Department", "Select PIN First"]:
            # Find occupied
            active_beds = df[(df['Department'] == dept) & (df['Actual_Discharge'].isnull())]['Bed'].tolist()
            # Generate all beds for this dept
            code = DEPARTMENTS[dept]['code']
            cap = DEPARTMENTS[dept]['cap']
            all_beds = [f"{code}-{i+1:03d}" for i in range(cap)]
            # Filter
            free_beds = [b for b in all_beds if b not in active_beds]
            bed_opts = free_beds if free_beds else ["NO BEDS AVAILABLE"]
            
        bed = st.selectbox("Assign Bed", bed_opts)

    with c2:
        st.subheader("Admission Timing")
        # 5. Dates (Date & Time Pickers)
        d1, t1 = st.columns(2)
        adm_date = d1.date_input("Admission Date", datetime.now())
        adm_time = t1.time_input("Admission Time", datetime.now().time())
        
        # 6. Source
        src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])
        
        st.write("---")
        st.subheader("Discharge Plan")
        # 7. Exp Discharge
        d2, t2 = st.columns(2)
        exp_date = d2.date_input("Expected Date", datetime.now() + timedelta(days=3))
        exp_time = t2.time_input("Expected Time", datetime.now().time())

    # Submit
    if st.button("Confirm Admission", type="primary", use_container_width=True):
        if pin != "Select..." and dept not in ["Select Department", "Select PIN First"] and bed not in ["Select Department First", "NO BEDS AVAILABLE"]:
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
            st.warning("Please complete all fields correctly.")

    # 8. Active Patients Table
    st.markdown("### 🏥 Current Inpatient List")
    active_df = df[df['Actual_Discharge'].isnull()].sort_values(by="Admit_Date", ascending=False)
    
    # Discharge Action inside Table View
    st.caption("To discharge a patient, select them below:")
    p_list = active_df.apply(lambda x: f"{x['PIN']} | {x['Bed']}", axis=1).tolist()
    dis_target = st.selectbox("Select Patient to Discharge", ["Select..."] + p_list)
    
    if dis_target != "Select...":
        t_pin, t_bed = dis_target.split(" | ")
        col_d1, col_d2 = st.columns(2)
        act_d = col_d1.date_input("Actual Discharge Date", datetime.now())
        act_t = col_d2.time_input("Actual Discharge Time", datetime.now().time())
        
        if st.button("Process Discharge"):
            idx = df[(df['PIN'] == t_pin) & (df['Bed'] == t_bed) & (df['Actual_Discharge'].isnull())].index
            st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(act_d, act_t)
            st.success("Discharged.")
            st.rerun()

    st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Gender', 'Admit_Date', 'Exp_Discharge']], use_container_width=True)

# ---------------------------------------------------------
# 6. Operational KPIs (Analytics)
# ---------------------------------------------------------
elif menu == "Operational KPIs":
    st.title("Operational Performance Indicators")
    
    calc = df.copy()
    now = datetime.now()
    
    # 1. Net Flow (24h)
    last_24 = now - timedelta(hours=24)
    adm_24 = len(calc[calc['Admit_Date'] >= last_24])
    dis_24 = len(calc[(calc['Actual_Discharge'] >= last_24)])
    net_flow = adm_24 - dis_24
    
    # 2. Bed Turnover Rate (Discharges / Total Beds)
    total_beds = sum(d['cap'] for d in DEPARTMENTS.values())
    total_dis = len(calc[calc['Actual_Discharge'].notnull()])
    turnover = total_dis / total_beds if total_beds > 0 else 0
    
    # 3. Admission Rate (Total / Days)
    days_diff = (calc['Admit_Date'].max() - calc['Admit_Date'].min()).days
    days_diff = 1 if days_diff < 1 else days_diff
    adm_rate = len(calc) / days_diff
    
    # KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    
    def kpi(label, val, sub):
        return f"""<div class="kpi-container"><div class="kpi-head">{label}</div><div class="kpi-num">{val}</div><div class="kpi-sub">{sub}</div></div>"""
    
    k1.markdown(kpi("Net Flow (24h)", f"{net_flow:+d}", "Inflow vs Outflow"), unsafe_allow_html=True)
    k2.markdown(kpi("Bed Turnover", f"{turnover:.2f}", "Rounds per Bed"), unsafe_allow_html=True)
    k3.markdown(kpi("Admission Rate", f"{adm_rate:.1f}", "Patients / Day"), unsafe_allow_html=True)
    k4.markdown(kpi("Total Discharges", total_dis, "Cumulative"), unsafe_allow_html=True)

    st.markdown("---")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("##### Net Flow Trends (Admissions vs Discharges)")
        daily_adm = calc.groupby(calc['Admit_Date'].dt.date).size().reset_index(name='Admissions')
        daily_dis = calc[calc['Actual_Discharge'].notnull()].groupby(calc['Actual_Discharge'].dt.date).size().reset_index(name='Discharges')
        
        if not daily_adm.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily_adm['Admit_Date'], y=daily_adm['Admissions'], name='Admissions', marker_color='#58A6FF'))
            if not daily_dis.empty:
                fig.add_trace(go.Bar(x=daily_dis['Actual_Discharge'], y=daily_dis['Discharges'], name='Discharges', marker_color='#238636'))
            
            fig.update_layout(barmode='group', paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font={'color': "#E6EDF3"})
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.markdown("##### Occupancy Heatmap")
        active_counts = calc[calc['Actual_Discharge'].isnull()]['Department'].value_counts().reset_index()
        active_counts.columns = ['Department', 'Count']
        if not active_counts.empty:
            fig2 = px.bar(active_counts, y='Department', x='Count', orientation='h', color='Count', color_continuous_scale='Bluered')
            fig2.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font={'color': "#E6EDF3"})
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    if st.button("FACTORY RESET SYSTEM", type="primary"):
        del st.session_state.df
        st.rerun()
