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

# Forced Dark Theme & Advanced CSS
st.markdown("""
<style>
    /* Global Settings */
    .stApp { background-color: #090C10; color: #E6EDF3; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* AI Board */
    .ai-container {
        background: #161B22; border: 1px solid #30363D; border-left: 5px solid #A371F7;
        border-radius: 6px; padding: 15px; margin-bottom: 20px;
    }
    .ai-header { font-weight: bold; color: #A371F7; font-size: 16px; margin-bottom: 8px; }
    .ai-msg { font-size: 13px; color: #E6EDF3; margin-bottom: 4px; padding-bottom: 4px; border-bottom: 1px solid #21262D; }
    
    /* KPI Cards */
    .kpi-card {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; text-align: center; margin-bottom: 10px;
    }
    .kpi-label { color: #8B949E; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-val { color: #F0F6FC; font-size: 28px; font-weight: 700; }
    .kpi-delta { font-size: 11px; font-weight: 600; }
    
    /* Department Cards */
    .dept-card {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px;
    }
    .dept-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    
    /* Colors */
    .c-green { color: #238636; } .bg-green { background: #238636; color: white; }
    .c-yellow { color: #D29922; } .bg-yellow { background: #D29922; color: white; }
    .c-red { color: #DA3633; } .bg-red { background: #DA3633; color: white; }
    
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

PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(1000)}

def init_system():
    if 'df' not in st.session_state:
        # Create Data Structure
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", "Admit_Date", 
            "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # Populate with Robust Initial Data
        data = []
        for dept, info in DEPARTMENTS.items():
            count = int(info['cap'] * np.random.uniform(0.5, 0.85)) 
            for i in range(count):
                bed_n = i + 1
                adm = datetime.now() - timedelta(days=np.random.randint(0, 10), hours=np.random.randint(1, 10))
                
                # Create mixed status (Active & Discharged)
                if np.random.random() < 0.15: # 15% discharged
                    exp = adm + timedelta(days=np.random.randint(1, 5))
                    act = exp + timedelta(hours=np.random.randint(0, 4))
                else: # Active
                    exp = adm + timedelta(days=np.random.randint(2, 8))
                    act = None
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(2000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": f"{dept[:3].upper()}-{bed_n:03d}",
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": act,
                    "Source": np.random.choice(["Emergency", "Elective", "Transfer"])
                })
        st.session_state.df = pd.DataFrame(data)

init_system()
df = st.session_state.df

# Fix Date Types (CRITICAL FIX FOR THE ERROR)
df['Admit_Date'] = pd.to_datetime(df['Admit_Date'], errors='coerce')
df['Exp_Discharge'] = pd.to_datetime(df['Exp_Discharge'], errors='coerce')
df['Actual_Discharge'] = pd.to_datetime(df['Actual_Discharge'], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar (With Filter)
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.header("OccupyBed AI")
        
    st.markdown("---")
    menu = st.radio("MAIN MENU", ["Overview", "Live Admissions", "Analytics", "Settings"], label_visibility="collapsed")
    
    st.markdown("---")
    # New Feature: Global Filter
    st.markdown("### 🔍 View Filter")
    selected_dept_filter = st.selectbox("Filter by Ward", ["All Wards"] + list(DEPARTMENTS.keys()))
    
    st.markdown("---")
    st.caption(f"Server: JED-HOSP-01\nVer: 7.1 (Stable)")

# Filter Data Logic
if selected_dept_filter != "All Wards":
    filtered_df = df[df['Department'] == selected_dept_filter]
    filtered_depts = {selected_dept_filter: DEPARTMENTS[selected_dept_filter]}
else:
    filtered_df = df
    filtered_depts = DEPARTMENTS

# ---------------------------------------------------------
# 4. Overview (Command Center)
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: 
        fc_hours = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # --- 1. Global Calculations ---
    now = datetime.now()
    active = filtered_df[filtered_df['Actual_Discharge'].isnull()]
    future_limit = now + timedelta(hours=fc_hours)
    
    # Capacity
    total_cap = sum(d['cap'] for d in filtered_depts.values())
    curr_occ = len(active)
    curr_avail = total_cap - curr_occ
    
    # Net Flow (24h)
    last_24 = now - timedelta(hours=24)
    adm_24 = len(filtered_df[filtered_df['Admit_Date'] >= last_24])
    dis_24 = len(filtered_df[(filtered_df['Actual_Discharge'] >= last_24)])
    net_flow = adm_24 - dis_24
    
    # Ready to Discharge (Forecast)
    total_ready = active[active['Exp_Discharge'] <= future_limit].shape[0]

    # --- 2. AI Action Center ---
    st.markdown(f"""<div class="ai-container"><div class="ai-header">🤖 AI Intelligence Report</div>""", unsafe_allow_html=True)
    
    ai_msg_count = 0
    for dept, info in filtered_depts.items():
        d_df = active[active['Department'] == dept]
        pct = (len(d_df)/info['cap'])*100
        delayed = d_df[d_df['Exp_Discharge'] < now].shape[0]
        
        if pct > 85:
            st.markdown(f"""<div class="ai-msg"><span style="color:#DA3633; font-weight:bold;">{dept}:</span> High occupancy ({int(pct)}%). Redirect new admissions to {info['overflow']}.</div>""", unsafe_allow_html=True)
            ai_msg_count += 1
        elif delayed > 3:
            st.markdown(f"""<div class="ai-msg"><span style="color:#D29922; font-weight:bold;">{dept}:</span> {delayed} patients overdue for discharge. Expedite social work review.</div>""", unsafe_allow_html=True)
            ai_msg_count += 1
            
    if ai_msg_count == 0:
        st.markdown(f"""<div class="ai-msg"><span style="color:#238636; font-weight:bold;">System:</span> Operations are running smoothly within safe capacity limits.</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 3. Enterprise KPIs ---
    k1, k2, k3, k4 = st.columns(4)
    
    def metric_card(label, value, sub, color):
        return f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-val" style="color:{color}">{value}</div>
            <div class="kpi-delta">{sub}</div>
        </div>
        """
    
    flow_col = "#DA3633" if net_flow > 0 else "#238636"
    
    k1.markdown(metric_card("Net Flow (24h)", f"{net_flow:+d}", f"In: {adm_24} | Out: {dis_24}", flow_col), unsafe_allow_html=True)
    k2.markdown(metric_card(f"Forecast Free ({fc_hours}h)", total_ready, "Projected Vacancy", "#A371F7"), unsafe_allow_html=True)
    k3.markdown(metric_card("Occupancy", curr_occ, f"{int(curr_occ/total_cap*100)}% Utilization", "#D29922"), unsafe_allow_html=True)
    k4.markdown(metric_card("Available Beds", curr_avail, "Ready for Admission", "#238636"), unsafe_allow_html=True)

    # --- 4. File Management ---
    with st.expander("📂 File Operations (Upload / Download)", expanded=False):
        f1, f2 = st.columns(2)
        with f1:
            st.download_button("Download Report (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_data.csv", "text/csv")
        with f2:
            up_file = st.file_uploader("Upload Data (CSV)", type=['csv'])
            if up_file:
                try:
                    new_df = pd.read_csv(up_file)
                    for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
                        new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                    st.session_state.df = new_df
                    st.success("Data Loaded Successfully")
                    st.rerun()
                except: st.error("Error parsing file.")

    st.markdown("---")

    # --- 5. Department Grid ---
    st.markdown("### Department Status")
    d_cols = st.columns(3)
    dept_names = list(filtered_depts.keys())
    
    for i, dept in enumerate(dept_names):
        info = filtered_depts[dept]
        d_data = active[active['Department'] == dept]
        
        occ = len(d_data)
        ready = d_data[d_data['Exp_Discharge'] <= future_limit].shape[0]
        pct = (occ / info['cap']) * 100
        
        # Logic
        if pct < 70:
            status, cls, b_col = "SAFE", "bg-green", "#238636"
        elif 70 <= pct <= 84:
            status, cls, b_col = "WARNING", "bg-yellow", "#D29922"
        else:
            status, cls, b_col = "CRITICAL", "bg-red", "#DA3633"
            
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card">
                <div class="dept-title-row">
                    <span class="dept-title">{dept}</span>
                    <span class="status-badge {cls}">{status}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#8B949E; margin-bottom:5px;">
                    <span>Cap: {info['cap']}</span>
                    <span>Occ: <b style="color:#E6EDF3">{occ}</b></span>
                    <span>Ready: <b style="color:#A371F7">{ready}</b></span>
                </div>
                <div style="background:#21262D; height:6px; border-radius:3px;">
                    <div style="width:{min(pct, 100)}%; background-color:{b_col}; height:100%; border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission Center")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Patient Info")
        pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
        gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
        if pin != "Select...": st.info(f"System Identified: **{gender}**")
        
        dept = st.selectbox("Department", ["Select..."] + list(DEPARTMENTS.keys()))
        
        # Bed Filter
        bed_opts = ["Select Department First"]
        if dept != "Select...":
            # Gender Rule
            if DEPARTMENTS[dept]['gen'] != "Mixed" and DEPARTMENTS[dept]['gen'] != gender:
                st.error(f"Compliance Alert: {dept} is {DEPARTMENTS[dept]['gen']} Only.")
            
            busy = df[(df['Department'] == dept) & (df['Actual_Discharge'].isnull())]['Bed'].tolist()
            all_b = [f"{dept[:3].upper()}-{i:03d}" for i in range(1, DEPARTMENTS[dept]['cap']+1)]
            avail = [b for b in all_b if b not in busy]
            bed_opts = avail if avail else ["NO BEDS AVAILABLE"]
            
        bed = st.selectbox("Bed Assignment", bed_opts)

    with c2:
        st.subheader("Timing")
        d1, t1 = st.columns(2)
        adm_date = d1.date_input("Admit Date", datetime.now())
        adm_time = t1.time_input("Admit Time", datetime.now().time())
        
        st.markdown("**Discharge Plan**")
        d2, t2 = st.columns(2)
        ex_date = d2.date_input("Exp. Date", datetime.now() + timedelta(days=3))
        ex_time = t2.time_input("Exp. Time", datetime.now().time())
        
        src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

    if st.button("Confirm Admission", type="primary", use_container_width=True):
        if pin != "Select..." and dept != "Select..." and bed not in ["Select Department First", "NO BEDS AVAILABLE"]:
            new_rec = {
                "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                "Admit_Date": datetime.combine(adm_date, adm_time),
                "Exp_Discharge": datetime.combine(ex_date, ex_time),
                "Actual_Discharge": None, "Source": src
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
            st.success("Admitted Successfully")
            time.sleep(0.5)
            st.rerun()
        else:
            st.warning("Please complete all fields.")

    st.markdown("### 🏥 Current Inpatients")
    active_df = df[df['Actual_Discharge'].isnull()].sort_values(by="Admit_Date", ascending=False)
    st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Admit_Date', 'Exp_Discharge']], use_container_width=True)

# ---------------------------------------------------------
# 6. Operational KPIs (Fixed the Error Here)
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Operational Analytics")
    
    # DATA PREP (CRITICAL FIX)
    calc = df.copy()
    now = datetime.now()
    # Ensure datetime format again to be safe
    calc['Admit_Date'] = pd.to_datetime(calc['Admit_Date'], errors='coerce')
    calc['Actual_Discharge'] = pd.to_datetime(calc['Actual_Discharge'], errors='coerce')
    
    # LOS Calc
    def get_los(row):
        end = row['Actual_Discharge'] if pd.notnull(row['Actual_Discharge']) else now
        return (end - row['Admit_Date']).total_seconds() / 86400
    calc['LOS'] = calc.apply(get_los, axis=1)

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Admissions", len(calc))
    m2.metric("Total Discharges", len(calc[calc['Actual_Discharge'].notnull()]))
    m3.metric("Avg LOS", f"{calc['LOS'].mean():.1f} Days")
    
    # Bed Turnover
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    turnover = len(calc[calc['Actual_Discharge'].notnull()]) / total_cap
    m4.metric("Bed Turnover", f"{turnover:.2f}", "Rounds/Bed")

    st.markdown("---")

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("##### Net Flow Analysis (Adm vs Disc)")
        # Grouping with Dropna to avoid errors
        daily_adm = calc.groupby(calc['Admit_Date'].dt.date).size().reset_index(name='Admissions')
        
        # Safe grouping for discharges
        discharged_only = calc[calc['Actual_Discharge'].notnull()].copy()
        if not discharged_only.empty:
            daily_disc = discharged_only.groupby(discharged_only['Actual_Discharge'].dt.date).size().reset_index(name='Discharges')
            # Merge
            trend = pd.merge(daily_adm, daily_disc, left_on='Admit_Date', right_on='Actual_Discharge', how='outer').fillna(0)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend['Admit_Date'], y=trend['Admissions'], name='Admissions', marker_color='#58A6FF'))
            fig.add_trace(go.Bar(x=trend['Admit_Date'], y=trend['Discharges'], name='Discharges', marker_color='#238636'))
            fig.update_layout(barmode='group', paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font={'color': "#E6EDF3"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No discharge data available for trend chart.")

    with c2:
        st.markdown("##### Occupancy Heatmap")
        # Creating a simple heatmap of occupancy by department
        dept_counts = calc[calc['Actual_Discharge'].isnull()]['Department'].value_counts().reset_index()
        dept_counts.columns = ['Department', 'Count']
        
        if not dept_counts.empty:
            fig2 = px.bar(dept_counts, x='Count', y='Department', orientation='h', color='Count', color_continuous_scale='Bluered')
            fig2.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font={'color': "#E6EDF3"})
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    if st.button("FACTORY RESET (Clear Database)", type="primary"):
        del st.session_state.df
        st.rerun()
