import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Config & Design
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Command Center", layout="wide", page_icon="🏥")

st.markdown("""
<style>
    /* Global Settings */
    .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* KPI Cards */
    .kpi-card {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 6px;
        padding: 20px; text-align: center; height: 100%; transition: all 0.3s;
    }
    .kpi-card:hover { border-color: #58A6FF; transform: scale(1.02); }
    .kpi-label { font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .kpi-val { font-size: 32px; font-weight: 700; color: #FFF; margin: 0; }
    
    /* AI Board */
    .ai-container {
        background-color: #161B22; border: 1px solid #30363D; border-left: 5px solid #A371F7;
        border-radius: 6px; padding: 15px; height: 100%;
    }
    .ai-header { font-weight: 700; color: #A371F7; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }
    .ai-item { font-size: 13px; color: #E6EDF3; margin-bottom: 6px; border-bottom: 1px solid #21262D; padding-bottom: 4px; }

    /* Department Cards */
    .dept-card {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px;
    }
    .dept-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .dept-title { font-size: 14px; font-weight: 700; color: #FFF; }
    
    /* Status Badges */
    .badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
    .bg-green { background: rgba(35, 134, 54, 0.2); color: #3FB950; border: 1px solid #238636; }
    .bg-yellow { background: rgba(210, 153, 34, 0.2); color: #D29922; border: 1px solid #9E6A03; }
    .bg-red { background: rgba(218, 54, 51, 0.2); color: #F85149; border: 1px solid #DA3633; }

    /* Animation Pulse for Live Mode */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
    }
    .live-indicator {
        display: inline-block; width: 10px; height: 10px; background: red; border-radius: 50%;
        animation: pulse 2s infinite; margin-right: 5px;
    }

    /* Inputs & Buttons */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    button[kind="primary"] { background-color: #238636 !important; border: none !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Logic & Data
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
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", 
            "Admit_Date", "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # --- GENERATE SAFE INITIAL DATA ---
        data = []
        for dept, info in DEPARTMENTS.items():
            # Safety Logic: Occupancy between 40% and 70% (Never Full)
            safe_count = int(info['cap'] * np.random.uniform(0.4, 0.6))
            
            for i in range(safe_count):
                bed_n = f"{dept[:3].upper()}-{i+1:03d}"
                adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 10))
                if np.random.random() < 0.3:
                    exp = datetime.now() + timedelta(hours=np.random.randint(2, 24))
                else:
                    exp = adm + timedelta(days=np.random.randint(3, 8))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(2000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": bed_n,
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": pd.NaT, # Active
                    "Source": np.random.choice(["Emergency", "Elective", "Transfer"])
                })
        st.session_state.df = pd.DataFrame(data)

init_system()
df = st.session_state.df

# Fix Date Types
for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------------------------------------------------------
# 3. AUTOMATED SIMULATION ENGINE (The 7s Update)
# ---------------------------------------------------------
def run_simulation_step():
    """Simulates hospital activity: Discharges or Admits a patient."""
    action = np.random.choice(['admit', 'discharge'], p=[0.55, 0.45]) # Slight bias to admission
    
    if action == 'discharge':
        # Find an active patient to discharge
        active_indices = df[df['Actual_Discharge'].isna()].index
        if not active_indices.empty:
            target_idx = np.random.choice(active_indices)
            # Discharge them now
            st.session_state.df.at[target_idx, 'Actual_Discharge'] = datetime.now()
            st.toast(f"🔄 SYSTEM UPDATE: Patient {df.at[target_idx, 'PIN']} Discharged.", icon="📤")
            
    elif action == 'admit':
        # Find a department with space
        for dept in np.random.permutation(list(DEPARTMENTS.keys())):
            info = DEPARTMENTS[dept]
            active_in_dept = df[(df['Department'] == dept) & (df['Actual_Discharge'].isna())]
            if len(active_in_dept) < info['cap']:
                # Admit here
                new_pin = f"PIN-{np.random.randint(3000, 9999)}"
                bed_num = f"{dept[:3].upper()}-{len(active_in_dept)+1:03d}"
                new_row = {
                    "PIN": new_pin,
                    "Gender": "Female" if "Female" in dept else "Male", 
                    "Department": dept,
                    "Bed": bed_num,
                    "Admit_Date": datetime.now(),
                    "Exp_Discharge": datetime.now() + timedelta(days=3),
                    "Actual_Discharge": pd.NaT,
                    "Source": "Emergency"
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.toast(f"🚨 LIVE: New Admission to {dept} ({new_pin})", icon="➕")
                break

# ---------------------------------------------------------
# 4. Sidebar & Simulation Control
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.header("OccupyBed AI")
    
    # --- PATIENT SEARCH (NEW ADDITION) ---
    st.markdown("### 🔍 Patient Search")
    search_q = st.text_input("Enter PIN", placeholder="e.g. PIN-2005")
    if search_q:
        res = df[df['PIN'] == search_q]
        if not res.empty:
            # Check latest status (most recent entry for this PIN)
            latest = res.iloc[-1]
            status = "Active 🟢" if pd.isna(latest['Actual_Discharge']) else "Discharged 🔴"
            st.success(f"**Found:** {latest['Department']}")
            st.info(f"**Bed:** {latest['Bed']}")
            st.caption(f"**Status:** {status}")
        else:
            st.warning("Patient not found.")

    st.markdown("---")
    
    # --- SIMULATION TOGGLE ---
    st.markdown("### ⚡ Simulation Mode")
    sim_mode = st.toggle("Active Live Simulation", value=False, help="Updates data every 7 seconds")
    
    if sim_mode:
        st.markdown(f"<div style='color:#F85149; font-weight:bold;'><span class='live-indicator'></span>LIVE FEED ACTIVE</div>", unsafe_allow_html=True)
        st.caption("Auto-refreshing every 7s...")
    
    st.markdown("---")
    menu = st.radio("NAVIGATION", ["Overview", "Live Admissions", "Operational Analytics", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("System Online | MVP v1.0")

# ---------------------------------------------------------
# 5. OVERVIEW
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: 
        fc_hours = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # Metrics
    now = datetime.now()
    active_df = df[df['Actual_Discharge'].isna()]
    future_limit = now + timedelta(hours=fc_hours)
    
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    occ_count = len(active_df)
    avail_count = total_cap - occ_count
    ready_count = len(active_df[active_df['Exp_Discharge'] <= future_limit])

    # KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Total Licensed Beds</div><div class="kpi-val" style="color:#58A6FF">{total_cap}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Occupied Beds</div><div class="kpi-val" style="color:#D29922">{occ_count}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Available Now</div><div class="kpi-val" style="color:#3FB950">{avail_count}</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Expected Free ({fc_hours}h)</div><div class="kpi-val" style="color:#A371F7">{ready_count}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gauge & AI
    g_col, ai_col = st.columns([1, 2])
    with g_col:
        occ_rate = (occ_count / total_cap) * 100 if total_cap > 0 else 0
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = occ_rate,
            title = {'text': "Hospital Pressure"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "#58A6FF"},
                'steps': [
                    {'range': [0, 70], 'color': "#161B22"},
                    {'range': [70, 85], 'color': "#451a03"},
                    {'range': [85, 100], 'color': "#450a0a"}],
            }
        ))
        fig.update_layout(height=250, margin=dict(l=10,r=10,t=0,b=0), paper_bgcolor="#0E1117", font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)

    with ai_col:
        st.markdown(f"""<div class="ai-container"><div class="ai-header">🤖 AI Operational Recommendations</div>""", unsafe_allow_html=True)
        ai_triggered = False
        for dept, info in DEPARTMENTS.items():
            d_pats = active_df[active_df['Department'] == dept]
            pct = (len(d_pats) / info['cap']) * 100
            
            if pct >= 85:
                st.markdown(f"""<div class="ai-item"><span style="color:#F85149"><b>{dept}:</b></span> Critical load ({int(pct)}%). Redirect new admissions to {info['overflow']}.</div>""", unsafe_allow_html=True)
                ai_triggered = True
            elif pct >= 70:
                st.markdown(f"""<div class="ai-item"><span style="color:#D29922"><b>{dept}:</b></span> High Load ({int(pct)}%). Prepare discharge lounge.</div>""", unsafe_allow_html=True)
                ai_triggered = True
                
        if not ai_triggered:
            st.markdown("""<div class="ai-item" style="color:#3FB950">Operations are stable. No critical bottlenecks.</div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Department Grid
    st.markdown("### Department Live Status")
    d_cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_names):
        info = DEPARTMENTS[dept]
        d_df = active_df[active_df['Department'] == dept]
        
        occ = len(d_df)
        avail = info['cap'] - occ
        ready = len(d_df[d_df['Exp_Discharge'] <= future_limit])
        pct = (occ / info['cap']) * 100
        
        if pct < 70: status, cls, bar = "SAFE", "bg-green", "#3FB950"
        elif 70 <= pct <= 84: status, cls, bar = "WARNING", "bg-yellow", "#D29922"
        else: status, cls, bar = "CRITICAL", "bg-red", "#F85149"
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card">
                <div class="dept-header">
                    <span class="dept-title">{dept}</span>
                    <span class="badge {cls}">{status}</span>
                </div>
                <div style="font-size:12px; color:#8B949E; display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span>Cap: {info['cap']}</span>
                    <span>Occ: <b style="color:#E6EDF3">{occ}</b></span>
                    <span>Avail: {avail}</span>
                </div>
                <div style="font-size:12px; display:flex; justify-content:space-between;">
                    <span style="color:#A371F7; font-weight:bold;">Ready ({fc_hours}h): {ready}</span>
                </div>
                <div style="background:#21262D; height:5px; border-radius:3px; margin-top:8px;">
                    <div style="width:{min(pct, 100)}%; background:{bar}; height:100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission & Discharge Center")
    
    # Data Ops
    with st.expander("📂 Data Operations (Import / Export)", expanded=False):
        c_dl, c_ul = st.columns(2)
        with c_dl:
            st.download_button("Download Data (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_db.csv", "text/csv")
        with c_ul:
            up_file = st.file_uploader("Upload Data (CSV)", type=['csv'])
            if up_file:
                try:
                    new_df = pd.read_csv(up_file)
                    for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']: 
                        new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                    st.session_state.df = new_df
                    st.success("Data Imported.")
                    st.rerun()
                except: st.error("Invalid File")

    # Admission Form
    st.subheader("1. New Admission")
    c1, c2 = st.columns(2)
    with c1:
        pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
        gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
        if pin != "Select...": st.info(f"Gender: **{gender}**")
        
        dept = st.selectbox("Assign Department", ["Select..."] + list(DEPARTMENTS.keys()))
        
        bed_opts = ["Select Dept"]
        if dept != "Select...":
            occ_beds = df[(df['Department'] == dept) & (df['Actual_Discharge'].isna())]['Bed'].tolist()
            all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
            free_beds = [b for b in all_beds if b not in occ_beds]
            bed_opts = free_beds if free_beds else ["NO BEDS AVAILABLE"]
        bed = st.selectbox("Assign Bed", bed_opts)

    with c2:
        d1, t1 = st.columns(2)
        adm_d = d1.date_input("Date", datetime.now())
        adm_t = t1.time_input("Time", datetime.now().time())
        d2, t2 = st.columns(2)
        exp_d = d2.date_input("Exp Date", datetime.now() + timedelta(days=3))
        exp_t = t2.time_input("Exp Time", datetime.now().time())
        src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

    if st.button("Confirm Admission", type="primary"):
        if pin != "Select..." and dept != "Select..." and bed not in ["Select Dept", "NO BEDS AVAILABLE"]:
            new_rec = {
                "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                "Admit_Date": datetime.combine(adm_d, adm_t),
                "Exp_Discharge": datetime.combine(exp_d, exp_t),
                "Actual_Discharge": pd.NaT,
                "Source": src
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
            st.success("Admitted.")
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")

    # Discharge
    st.subheader("2. Discharge Management")
    active_df = df[df['Actual_Discharge'].isna()].sort_values(by="Admit_Date", ascending=False)
    
    if not active_df.empty:
        target = st.selectbox("Select Patient to Discharge", ["Select..."] + active_df['PIN'].tolist())
        if target != "Select...":
            c_dis1, c_dis2 = st.columns(2)
            act_d = c_dis1.date_input("Discharge Date", datetime.now())
            act_t = c_dis2.time_input("Discharge Time", datetime.now().time())
            
            if st.button("Confirm Discharge"):
                idx = df[(df['PIN'] == target) & (df['Actual_Discharge'].isna())].index
                st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(act_d, act_t)
                st.success("Discharged.")
                st.rerun()
        
        st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Admit_Date', 'Exp_Discharge']], use_container_width=True)
    else:
        st.info("No active patients.")

# ---------------------------------------------------------
# 6. Analytics
# ---------------------------------------------------------
elif menu == "Operational Analytics":
    st.title("Performance Analytics")
    calc = df.copy()
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("##### Active Occupancy")
        active_mask = calc['Actual_Discharge'].isna()
        if not calc[active_mask].empty:
            dept_counts = calc[active_mask]['Department'].value_counts().reset_index()
            dept_counts.columns = ['Department', 'Count']
            fig = px.pie(dept_counts, values='Count', names='Department', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False, paper_bgcolor="#0E1117", font={'color': "white"}, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.markdown("##### Admissions Trend")
        daily_adm = calc.groupby(calc['Admit_Date'].dt.date).size().reset_index(name='In')
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=daily_adm['Admit_Date'], y=daily_adm['In'], name='Admissions', marker_color='#58A6FF'))
        fig2.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#0E1117", font={'color': "white"})
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    if st.button("FACTORY RESET (Clean Database)", type="primary"):
        del st.session_state.df
        st.success("System Cleared.")
        st.rerun()

# ---------------------------------------------------------
# 8. SIMULATION LOOP (THE MAGIC)
# ---------------------------------------------------------
if sim_mode:
    # Run a simulation step
    run_simulation_step()
    # Wait 7 seconds
    time.sleep(7)
    # Rerun the app to update UI
    st.rerun()
