import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Config & Corporate Design
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Enterprise", layout="wide", page_icon="🏥")

# CSS: High-End Dark Theme + Visual Fixes
st.markdown("""
<style>
    /* Global Reset */
    .stApp { background-color: #0B0E11; color: #E6EDF3; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* Glowing Icon Animation */
    @keyframes glow {
        from { text-shadow: 0 0 5px #fff, 0 0 10px #238636; }
        to { text-shadow: 0 0 10px #fff, 0 0 20px #238636; }
    }
    .glow-icon { font-size: 24px; animation: glow 1.5s ease-in-out infinite alternate; }

    /* AI Board Section */
    .ai-container {
        background: #161B22; border: 1px solid #30363D; border-left: 5px solid #A371F7;
        border-radius: 6px; padding: 15px; margin-bottom: 20px;
    }
    .ai-title { font-size: 16px; font-weight: 700; color: #A371F7; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;}
    .ai-item { font-size: 13px; color: #E6EDF3; margin-bottom: 6px; border-bottom: 1px solid #21262D; padding-bottom: 4px; }
    .ai-dept { font-weight: 700; color: #58A6FF; margin-right: 5px; }

    /* Department Cards (Corrected CSS) */
    .dept-box {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 8px;
        padding: 16px; margin-bottom: 10px; transition: transform 0.2s;
    }
    .dept-box:hover { border-color: #58A6FF; }
    .dept-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .dept-title { font-size: 15px; font-weight: 700; color: #FFF; }
    
    /* Stats Grid */
    .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 10px; }
    .stat-item { background: #161B22; padding: 8px; border-radius: 4px; text-align: center; }
    .stat-lbl { font-size: 10px; color: #8B949E; text-transform: uppercase; }
    .stat-val { font-size: 14px; font-weight: 700; color: #E6EDF3; }
    .val-highlight { color: #A371F7; }

    /* Progress Bar Background */
    .prog-bg { background: #21262D; height: 6px; border-radius: 3px; overflow: hidden; width: 100%; margin-top: 8px; }
    
    /* Visual Bed Grid */
    .bed-wrapper { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 10px; padding-top: 8px; border-top: 1px solid #21262D; }
    .bed-dot { width: 10px; height: 10px; border-radius: 2px; }
    
    /* Status Colors */
    .st-safe { color: #3FB950; border: 1px solid #238636; background: rgba(35,134,54,0.1); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .st-warn { color: #D29922; border: 1px solid #9E6A03; background: rgba(210,153,34,0.1); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    .st-crit { color: #F85149; border: 1px solid #DA3633; background: rgba(218,54,51,0.1); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }

    /* Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    button[kind="primary"] { background-color: #238636 !important; border: none !important; color: white !important; font-weight: 600; }
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
        # Schema definition
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", "Admit_Date", 
            "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # Synthetic Data Generation
        data = []
        for dept, info in DEPARTMENTS.items():
            count = int(info['cap'] * np.random.uniform(0.5, 0.85))
            for i in range(count):
                bed_n = f"{dept[:3].upper()}-{i+1:03d}"
                
                # Dates
                adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 10))
                
                # Forecast Logic
                if np.random.random() < 0.2: # Ready soon
                    exp = datetime.now() + timedelta(hours=np.random.randint(2, 24))
                else:
                    exp = adm + timedelta(days=np.random.randint(2, 7))
                
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

# Type Conversion Safety
for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar (Logo & Nav)
# ---------------------------------------------------------
with st.sidebar:
    # Logo Logic: Fallback if file doesn't exist
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("## 🏥 OccupyBed AI")
    
    st.markdown("<div class='glow-icon' style='text-align:center;'>⚡ System Live</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu = st.radio("NAVIGATION", ["Overview", "Live Admissions", "Analytics", "Settings"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("**User:** Admin\n\n**Server:** Jeddah-01")

# ---------------------------------------------------------
# 4. OVERVIEW (Dashboard)
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: 
        fc = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # --- Global Logic ---
    now = datetime.now()
    active = df[df['Actual_Discharge'].isnull()]
    future_limit = now + timedelta(hours=fc)
    
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    curr_occ = len(active)
    curr_avail = total_cap - curr_occ
    
    # Net Flow
    last_24 = now - timedelta(hours=24)
    adm_24 = len(df[df['Admit_Date'] >= last_24])
    dis_24 = len(df[df['Actual_Discharge'] >= last_24])
    net_flow = adm_24 - dis_24
    
    # Forecast Ready
    total_ready = active[active['Exp_Discharge'] <= future_limit].shape[0]

    # --- 1. AI Action Center ---
    st.markdown("""<div class="ai-container"><div class="ai-title">🤖 AI Suggested Actions</div>""", unsafe_allow_html=True)
    ai_triggered = False
    for dept, info in DEPARTMENTS.items():
        d_df = active[active['Department'] == dept]
        occ = len(d_df)
        pct = (occ / info['cap']) * 100
        delayed = d_df[d_df['Exp_Discharge'] < now].shape[0]
        
        if pct >= 85:
            st.markdown(f"""<div class="ai-item"><span class="ai-dept">{dept}:</span> Critical Occupancy ({int(pct)}%). Redirect to {info['overflow']}.</div>""", unsafe_allow_html=True)
            ai_triggered = True
        elif delayed > 3:
            st.markdown(f"""<div class="ai-item"><span class="ai-dept">{dept}:</span> High delayed discharges ({delayed}). Review pending files.</div>""", unsafe_allow_html=True)
            ai_triggered = True
            
    if not ai_triggered:
        st.markdown("""<div class="ai-item">All systems operating within safe parameters.</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. Hospital KPIs ---
    k1, k2, k3, k4 = st.columns(4)
    
    def kpi_box(title, val, sub, col="#FFF"):
        st.markdown(f"""
        <div style="background:#0D1117; padding:15px; border-radius:6px; border:1px solid #30363D; text-align:center;">
            <div style="color:#8B949E; font-size:11px; text-transform:uppercase;">{title}</div>
            <div style="color:{col}; font-size:24px; font-weight:bold; margin:5px 0;">{val}</div>
            <div style="color:#58A6FF; font-size:11px;">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    with k1: kpi_box("Net Flow (24h)", f"{net_flow:+d}", f"In: {adm_24} / Out: {dis_24}", "#DA3633" if net_flow > 0 else "#238636")
    with k2: kpi_box("Occupancy Rate", f"{int(curr_occ/total_cap*100)}%", f"{curr_occ} / {total_cap} Beds", "#D29922")
    with k3: kpi_box(f"Forecast Free ({fc}h)", total_ready, "Projected Vacancy", "#A371F7")
    with k4: kpi_box("Turnover Rate", "1.2", "Patients / Bed / Day", "#238636")

    # --- 3. File Ops ---
    with st.expander("📂 File Data Operations"):
        c_dl, c_up = st.columns(2)
        c_dl.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "hospital_data.csv", "text/csv")
        up_f = c_up.file_uploader("Upload CSV", type=['csv'])
        if up_f:
            try:
                new_df = pd.read_csv(up_f)
                for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']: new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                st.session_state.df = new_df
                st.success("Data Updated!")
                st.rerun()
            except: st.error("Invalid CSV")

    st.markdown("---")

    # --- 4. Department Matrix (Visual) ---
    st.markdown("### Department Status")
    d_cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_names):
        info = DEPARTMENTS[dept]
        d_df = active[active['Department'] == dept]
        
        occ = len(d_df)
        ready = d_df[d_df['Exp_Discharge'] <= future_limit].shape[0]
        pct = (occ / info['cap']) * 100
        avail = info['cap'] - occ
        
        # Logic
        if pct < 70:
            status, s_cls, bar_c = "SAFE", "st-safe", "#238636"
        elif 70 <= pct <= 84:
            status, s_cls, bar_c = "WARNING", "st-warn", "#D29922"
        else:
            status, s_cls, bar_c = "CRITICAL", "st-crit", "#DA3633"
            
        # Bed Grid HTML Generation
        grid_html = '<div class="bed-wrapper">'
        # Occupied
        for _, r in d_df.iterrows():
            # Red if just occupied, Greenish if ready to discharge
            color = "#10B981" if r['Exp_Discharge'] <= future_limit else "#DA3633"
            grid_html += f'<div class="bed-dot" style="background:{color};" title="PIN: {r["PIN"]}"></div>'
        # Free
        for _ in range(avail):
            grid_html += '<div class="bed-dot" style="background:#21262D;" title="Empty"></div>'
        grid_html += '</div>'
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-box">
                <div class="dept-header">
                    <span class="dept-title">{dept}</span>
                    <span class="{s_cls}">{status}</span>
                </div>
                <div class="stat-grid">
                    <div class="stat-item"><div class="stat-lbl">Occupied</div><div class="stat-val">{occ}</div></div>
                    <div class="stat-item"><div class="stat-lbl">Available</div><div class="stat-val">{avail}</div></div>
                    <div class="stat-item"><div class="stat-lbl">Total</div><div class="stat-val">{info['cap']}</div></div>
                    <div class="stat-item"><div class="stat-lbl" style="color:#A371F7">Ready ({fc}h)</div><div class="stat-val val-highlight">{ready}</div></div>
                </div>
                <div class="prog-bg"><div style="width:{min(pct, 100)}%; background:{bar_c}; height:100%"></div></div>
                {grid_html}
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions (The Main Fixes)
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission & Discharge Center")
    
    # --- Tab 1: New Admission ---
    st.subheader("1. New Admission Entry")
    c1, c2 = st.columns(2)
    with c1:
        pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
        gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
        if pin != "Select...": st.info(f"Detected Gender: **{gender}**")
        
        dept = st.selectbox("Assign Department", ["Select..."] + list(DEPARTMENTS.keys()))
        
        # Logic: Filter Occupied Beds
        bed_opts = ["Select Department First"]
        if dept != "Select...":
            # Gender check
            if DEPARTMENTS[dept]['gen'] != "Mixed" and DEPARTMENTS[dept]['gen'] != gender:
                st.error(f"Error: {dept} is {DEPARTMENTS[dept]['gen']} Only.")
            
            occ_beds = df[(df['Department'] == dept) & (df['Actual_Discharge'].isnull())]['Bed'].tolist()
            all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
            free_beds = [b for b in all_beds if b not in occ_beds]
            bed_opts = free_beds if free_beds else ["NO BEDS AVAILABLE"]
            
        bed = st.selectbox("Assign Bed", bed_opts)

    with c2:
        # Date & Time Pickers (Requested Fix)
        d1, t1 = st.columns(2)
        adm_d = d1.date_input("Admission Date", datetime.now())
        adm_t = t1.time_input("Admission Time", datetime.now().time())
        
        st.write("---")
        st.markdown("**Discharge Plan**")
        d2, t2 = st.columns(2)
        exp_d = d2.date_input("Expected Discharge Date", datetime.now() + timedelta(days=3))
        exp_t = t2.time_input("Expected Discharge Time", datetime.now().time())
        
        src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

    if st.button("Confirm Admission", type="primary", use_container_width=True):
        if pin != "Select..." and dept != "Select..." and bed not in ["Select Department First", "NO BEDS AVAILABLE"]:
            new_rec = {
                "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                "Admit_Date": datetime.combine(adm_d, adm_t),
                "Exp_Discharge": datetime.combine(exp_d, exp_t),
                "Actual_Discharge": None, # Active
                "Source": src
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
            st.success(f"Patient {pin} Admitted Successfully.")
            time.sleep(0.5)
            st.rerun()
        else:
            st.warning("Please verify all fields.")

    st.markdown("---")
    
    # --- Tab 2: Manage Active Patients (Discharge) ---
    st.subheader("2. Current Inpatients (Real-time)")
    active_df = df[df['Actual_Discharge'].isnull()].sort_values(by="Admit_Date", ascending=False)
    
    if not active_df.empty:
        # Quick Discharge Selection
        target = st.selectbox("Select Patient to Discharge", ["Select..."] + active_df['PIN'].tolist())
        
        if target != "Select...":
            row = active_df[active_df['PIN'] == target].iloc[0]
            st.info(f"Processing Discharge for: **{row['PIN']}** | **{row['Department']}** | **{row['Bed']}**")
            
            # Actual Discharge Time Input
            dc1, dc2 = st.columns(2)
            act_d = dc1.date_input("Actual Discharge Date", datetime.now())
            act_t = dc2.time_input("Actual Discharge Time", datetime.now().time())
            
            if st.button(f"Confirm Discharge for {target}"):
                # Update Dataframe
                idx = df[(df['PIN'] == target) & (df['Actual_Discharge'].isnull())].index
                st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(act_d, act_t)
                st.success("Patient Discharged & Removed from Active List.")
                time.sleep(0.5)
                st.rerun()
        
        # Show Table
        st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Gender', 'Admit_Date', 'Exp_Discharge']], use_container_width=True)
    else:
        st.info("No active patients in the hospital.")

# ---------------------------------------------------------
# 6. Analytics (KPIs & Heatmaps)
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Operational Analytics")
    
    calc = df.copy()
    now = datetime.now()
    
    # Metrics
    k1, k2, k3, k4 = st.columns(4)
    total_adm = len(calc)
    total_dis = len(calc[calc['Actual_Discharge'].notnull()])
    
    # Bed Turnover
    tot_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    turnover = total_dis / tot_cap
    
    # ALOS (Avg Length of Stay)
    def get_los(r):
        end = r['Actual_Discharge'] if pd.notnull(r['Actual_Discharge']) else now
        return (end - r['Admit_Date']).total_seconds() / 86400
    
    calc['LOS'] = calc.apply(get_los, axis=1)
    
    k1.metric("Total Admissions", total_adm)
    k2.metric("Total Discharges", total_dis)
    k3.metric("Avg LOS", f"{calc['LOS'].mean():.1f} Days")
    k4.metric("Bed Turnover", f"{turnover:.2f}", "Rounds/Bed")
    
    st.markdown("---")
    
    # Graphs
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Net Flow Trend")
        daily_adm = calc.groupby(calc['Admit_Date'].dt.date).size().reset_index(name='In')
        daily_dis = calc[calc['Actual_Discharge'].notnull()].groupby(calc['Actual_Discharge'].dt.date).size().reset_index(name='Out')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=daily_adm['Admit_Date'], y=daily_adm['In'], name='Admission', marker_color='#60A5FA'))
        if not daily_dis.empty:
            fig.add_trace(go.Bar(x=daily_dis['Actual_Discharge'], y=daily_dis['Out'], name='Discharge', marker_color='#34D399'))
        fig.update_layout(paper_bgcolor="#0B0E11", plot_bgcolor="#0B0E11", font={'color':"#AAA"})
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.markdown("##### Occupancy by Department (Active)")
        active_counts = calc[calc['Actual_Discharge'].isnull()]['Department'].value_counts().reset_index()
        active_counts.columns = ['Department', 'Count']
        if not active_counts.empty:
            fig2 = px.bar(active_counts, y='Department', x='Count', orientation='h', color='Count', color_continuous_scale='Bluered')
            fig2.update_layout(paper_bgcolor="#0B0E11", plot_bgcolor="#0B0E11", font={'color':"#AAA"})
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    if st.button("FACTORY RESET (Clear Database)", type="primary"):
        del st.session_state.df
        st.rerun()
