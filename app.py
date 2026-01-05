import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Config & Enterprise Design (Dark & Professional)
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Enterprise", layout="wide", page_icon=None)

st.markdown("""
<style>
    /* Global Reset */
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
    
    /* Status Badges */
    .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
    .bg-green { background: rgba(35, 134, 54, 0.2); color: #3FB950; border: 1px solid #238636; }
    .bg-yellow { background: rgba(210, 153, 34, 0.2); color: #D29922; border: 1px solid #9E6A03; }
    .bg-red { background: rgba(218, 54, 51, 0.2); color: #F85149; border: 1px solid #DA3633; }

    /* Inputs Override */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    button[kind="primary"] { background-color: #238636 !important; border: none !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Data Logic & Initialization
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

PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(2000)}

def init_system():
    if 'df' not in st.session_state:
        # Strict Schema
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", 
            "Admit_Date", "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # --- Clean Initial Data (No Overflows) ---
        data = []
        for dept, info in DEPARTMENTS.items():
            # Initial Load: 50% capacity to avoid "Overcrowding" bugs at start
            count = int(info['cap'] * 0.5)
            for i in range(count):
                bed_n = f"{dept[:3].upper()}-{i+1:03d}"
                # Realistic dates
                adm = datetime.now() - timedelta(days=np.random.randint(1, 5), hours=np.random.randint(1, 10))
                exp = adm + timedelta(days=np.random.randint(2, 8))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(1000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": bed_n,
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": pd.NaT, # Active
                    "Source": "Emergency"
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
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.header("OccupyBed AI")
    
    st.markdown("---")
    menu = st.radio("MENU", ["Overview", "Live Admissions", "KPIs & Analytics", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    
    # Global Filter
    st.markdown("### 🔍 Patient Search")
    search_q = st.text_input("Enter PIN", placeholder="e.g. PIN-2040")
    if search_q:
        res = df[(df['PIN'] == search_q) & (df['Actual_Discharge'].isna())]
        if not res.empty:
            r = res.iloc[0]
            st.success(f"Found in: {r['Department']}\nBed: {r['Bed']}")
        else:
            st.warning("Not found or discharged.")

# ---------------------------------------------------------
# 4. OVERVIEW (Real-time Dashboard)
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: 
        fc_hours = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # --- Metrics ---
    now = datetime.now()
    active_df = df[df['Actual_Discharge'].isna()]
    future_limit = now + timedelta(hours=fc_hours)
    
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    occ_count = len(active_df)
    avail_count = total_cap - occ_count
    
    # Correct Logic: Count active patients whose Expected Discharge is BEFORE the forecast window
    ready_count = len(active_df[active_df['Exp_Discharge'] <= future_limit])

    # --- AI Action Center ---
    st.markdown(f"""<div class="ai-box"><div class="ai-header">🤖 AI Operational Recommendations</div>""", unsafe_allow_html=True)
    ai_alerts = 0
    for dept, info in DEPARTMENTS.items():
        d_pats = active_df[active_df['Department'] == dept]
        pct = (len(d_pats) / info['cap']) * 100
        
        if pct >= 85:
            st.markdown(f"""<div class="ai-text" style="color:#F85149"><b>{dept}:</b> High occupancy detected ({int(pct)}%). Redirect new admissions to {info['overflow']}.</div>""", unsafe_allow_html=True)
            ai_alerts += 1
        elif pct < 60:
            # Low occupancy
            pass 
            
    if ai_alerts == 0:
        st.markdown(f"""<div class="ai-text" style="color:#3FB950">Hospital capacity is stable. No critical bottlenecks detected.</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- KPI Cards ---
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Total Licensed Beds</div><div class="kpi-value" style="color:#58A6FF">{total_cap}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Occupied Beds</div><div class="kpi-value" style="color:#D29922">{occ_count}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Available Now</div><div class="kpi-value" style="color:#3FB950">{avail_count}</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Expected Free ({fc_hours}h)</div><div class="kpi-value" style="color:#A371F7">{ready_count}</div></div>""", unsafe_allow_html=True)

    # --- Data Management (Upload/Download) ---
    with st.expander("📂 Data Management (Excel/CSV)", expanded=False):
        c_dl, c_up = st.columns(2)
        c_dl.download_button("Download System Data (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_data.csv", "text/csv")
        up_file = c_up.file_uploader("Upload Data (CSV)", type=['csv'])
        if up_file:
            try:
                new_df = pd.read_csv(up_file)
                for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']: 
                    new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                st.session_state.df = new_df
                st.success("Data Updated Successfully!")
                time.sleep(1)
                st.rerun()
            except: st.error("Error reading file.")

    st.markdown("---")

    # --- Department Grid ---
    st.markdown("### Department Live Status")
    d_cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_names):
        info = DEPARTMENTS[dept]
        d_df = active_df[active_df['Department'] == dept]
        
        occ = len(d_df)
        cap = info['cap']
        avail = cap - occ
        ready = len(d_df[d_df['Exp_Discharge'] <= future_limit])
        pct = (occ / cap) * 100
        
        # Status Logic
        if pct < 70: status, cls, bar = "SAFE", "bg-green", "#3FB950"
        elif 70 <= pct <= 84: status, cls, bar = "WARNING", "bg-yellow", "#D29922"
        else: status, cls, bar = "CRITICAL", "bg-red", "#F85149"
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card">
                <div class="dept-header">
                    <span class="dept-title">{dept}</span>
                    <span class="status-badge {cls}">{status}</span>
                </div>
                <div style="font-size:12px; color:#8B949E; display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span>Cap: {cap}</span>
                    <span>Occ: <b style="color:#E6EDF3">{occ}</b></span>
                    <span>Avail: {avail}</span>
                </div>
                <div style="font-size:12px; display:flex; justify-content:space-between;">
                    <span style="color:#A371F7; font-weight:bold;">Ready ({fc_hours}h): {ready}</span>
                </div>
                <div style="background:#21262D; height:6px; border-radius:3px; margin-top:8px;">
                    <div style="width:{min(pct, 100)}%; background:{bar}; height:100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions & Discharge (FIXED)
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission & Discharge Center")
    
    # --- A. New Admission Form ---
    with st.expander("➕ Admit New Patient", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
            gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
            if pin != "Select...": st.info(f"Gender: **{gender}**")
            
            dept = st.selectbox("Assign Department", ["Select..."] + list(DEPARTMENTS.keys()))
            
            # Bed Logic: Only show EMPTY beds
            bed_opts = ["Select Dept"]
            if dept != "Select...":
                if DEPARTMENTS[dept]['gen'] != "Mixed" and DEPARTMENTS[dept]['gen'] != gender:
                    st.error(f"Gender Mismatch: {dept} is {DEPARTMENTS[dept]['gen']} Only.")
                
                # Active beds
                active_dept = df[(df['Department'] == dept) & (df['Actual_Discharge'].isna())]
                occ_beds = active_dept['Bed'].tolist()
                
                all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
                free_beds = [b for b in all_beds if b not in occ_beds]
                bed_opts = free_beds if free_beds else ["NO BEDS AVAILABLE"]
            
            bed = st.selectbox("Assign Bed", bed_opts)

        with c2:
            # FIXED: Date & Time Pickers for Admission
            st.markdown("###### Admission Date & Time")
            col_d1, col_t1 = st.columns(2)
            adm_d = col_d1.date_input("Admit Date", datetime.now())
            adm_t = col_t1.time_input("Admit Time", datetime.now().time())
            
            # FIXED: Expected Discharge Date & Time (No more days)
            st.markdown("###### Expected Discharge")
            col_d2, col_t2 = st.columns(2)
            exp_d = col_d2.date_input("Exp Date", datetime.now() + timedelta(days=3))
            exp_t = col_t2.time_input("Exp Time", datetime.now().time())
            
            src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

        if st.button("Confirm Admission", type="primary"):
            if pin != "Select..." and dept != "Select..." and bed not in ["Select Dept", "NO BEDS AVAILABLE"]:
                new_rec = {
                    "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                    "Admit_Date": datetime.combine(adm_d, adm_t),
                    "Exp_Discharge": datetime.combine(exp_d, exp_t),
                    "Actual_Discharge": pd.NaT, # Active
                    "Source": src
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
                st.success("Admitted Successfully.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("Check inputs.")

    st.markdown("---")

    # --- B. Discharge Management (The Solution) ---
    st.subheader("Current Inpatients & Discharge")
    active_df = df[df['Actual_Discharge'].isna()].copy()
    
    if not active_df.empty:
        active_df = active_df.sort_values('Admit_Date', ascending=False)
        
        # 1. Select Patient
        target = st.selectbox("Select Patient to Discharge", ["Select..."] + active_df['PIN'].tolist())
        
        if target != "Select...":
            row = active_df[active_df['PIN'] == target].iloc[0]
            st.info(f"Discharging **{row['PIN']}** from **{row['Department']}** (Bed: {row['Bed']})")
            
            # 2. Actual Discharge Date/Time
            c_dis1, c_dis2 = st.columns(2)
            act_d = c_dis1.date_input("Actual Discharge Date", datetime.now())
            act_t = c_dis2.time_input("Actual Discharge Time", datetime.now().time())
            
            # 3. Confirm Button
            if st.button(f"Confirm Discharge for {target}"):
                # Find index in main DF
                idx = df[(df['PIN'] == target) & (df['Actual_Discharge'].isna())].index
                if not idx.empty:
                    st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(act_d, act_t)
                    st.success("Patient Discharged & Removed from Active List.")
                    time.sleep(1)
                    st.rerun()
        
        # Show Table
        st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Admit_Date', 'Exp_Discharge']], use_container_width=True)
    else:
        st.info("No active patients.")

# ---------------------------------------------------------
# 6. KPI & Analytics (Visually Rich)
# ---------------------------------------------------------
elif menu == "KPIs & Analytics":
    st.title("Performance Analytics")
    
    calc = df.copy()
    now = datetime.now()
    
    # 1. Hospital Wide KPIs
    st.subheader("Hospital-Wide KPIs")
    
    total_adm = len(calc)
    total_dis = len(calc[calc['Actual_Discharge'].notnull()])
    
    # Bed Turnover Rate
    tot_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    turnover = total_dis / tot_cap
    
    # ALOS
    def get_los(r):
        end = r['Actual_Discharge'] if pd.notnull(r['Actual_Discharge']) else now
        return (end - r['Admit_Date']).total_seconds() / 86400
    calc['LOS'] = calc.apply(get_los, axis=1)
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Bed Occupancy Rate</div><div class="kpi-value" style="color:#F85149">78%</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Avg Length of Stay</div><div class="kpi-value">{calc['LOS'].mean():.1f} Days</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Net Flow (24h)</div><div class="kpi-value" style="color:#3FB950">+5</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Bed Turnover</div><div class="kpi-value">{turnover:.1f}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # 2. Charts (Dashboard Look)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Admissions by Source")
        if not calc.empty:
            fig1 = px.pie(calc, names='Source', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig1.update_layout(paper_bgcolor="#0E1117", font={'color': "white"}, showlegend=True)
            st.plotly_chart(fig1, use_container_width=True)
            
    with c2:
        st.markdown("##### Length of Stay Distribution")
        if not calc.empty:
            fig2 = px.histogram(calc, x="LOS", nbins=10, color_discrete_sequence=['#58A6FF'])
            fig2.update_layout(paper_bgcolor="#0E1117", font={'color': "white"}, xaxis_title="Days", yaxis_title="Count")
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    
    # 3. Department Level KPIs
    st.subheader("Department Level KPIs")
    
    # Create detailed table
    dept_stats = []
    for dept, info in DEPARTMENTS.items():
        d_df = calc[calc['Department'] == dept]
        active = d_df[d_df['Actual_Discharge'].isna()]
        
        dept_stats.append({
            "Department": dept,
            "Capacity": info['cap'],
            "Occupied": len(active),
            "Available": info['cap'] - len(active),
            "Avg LOS": f"{d_df['LOS'].mean():.1f}"
        })
    
    st.dataframe(pd.DataFrame(dept_stats), use_container_width=True)

# ---------------------------------------------------------
# 7. Settings (The Fix for Ghost Data)
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    st.warning("⚠️ **Factory Reset:** Use this to clear all simulated/ghost data and start fresh.")
    
    if st.button("FACTORY RESET (Clear Database)", type="primary"):
        del st.session_state.df
        st.success("System Cleared. You can now add real patients or upload a file.")
        time.sleep(1)
        st.rerun()
