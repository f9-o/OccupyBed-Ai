import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Config & Design (Classic V4 Style - Professional)
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI", layout="wide", page_icon=None)

st.markdown("""
<style>
    /* Dark Corporate Theme */
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #333; }
    
    /* KPI Cards - Clean & Simple */
    .kpi-card {
        background: #1B1F24; border: 1px solid #30363D; border-radius: 6px;
        padding: 20px; text-align: center; margin-bottom: 10px;
    }
    .kpi-num { font-size: 32px; font-weight: bold; color: #FFF; margin: 5px 0; }
    .kpi-lbl { font-size: 12px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Department Cards */
    .dept-box {
        background: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px;
    }
    .dept-title { font-weight: 700; font-size: 15px; color: #E6EDF3; display: flex; justify-content: space-between; }
    .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    
    /* Status Colors */
    .st-safe { background: #064e3b; color: #34d399; }
    .st-warn { background: #451a03; color: #fbbf24; }
    .st-crit { background: #450a0a; color: #f87171; }

    /* Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    button[kind="primary"] { background-color: #238636 !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Data & Logic (Cleaned Up)
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

PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(1000)}

def init_system():
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", "Admit_Date", 
            "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # Generate CLEAN Initial Data (No Overflows)
        data = []
        for dept, info in DEPARTMENTS.items():
            # Fill only 50-70% to allow space
            count = int(info['cap'] * np.random.uniform(0.5, 0.7))
            for i in range(count):
                bed_n = f"{dept[:3].upper()}-{i+1:03d}"
                adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 10))
                exp = adm + timedelta(days=np.random.randint(2, 7))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(1000, 9000)}",
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

# Type Safety
for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.header("OccupyBed AI")
    
    st.markdown("---")
    menu = st.radio("MENU", ["Overview", "Live Admissions", "Analytics", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("System Status: **Online**")

# ---------------------------------------------------------
# 4. Overview (Dashboard)
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Real-time Overview")
    with c2: fc = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # Metrics
    now = datetime.now()
    active = df[df['Actual_Discharge'].isna()]
    
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    occ = len(active)
    avail = total_cap - occ
    
    # Calculate Expected Free based on Window
    future = now + timedelta(hours=fc)
    exp_free = active[active['Exp_Discharge'] <= future].shape[0]

    # KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"""<div class="kpi-card"><div class="kpi-lbl">Total Beds</div><div class="kpi-num" style="color:#3b82f6">{total_cap}</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="kpi-card"><div class="kpi-lbl">Occupied</div><div class="kpi-num" style="color:#eab308">{occ}</div></div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="kpi-card"><div class="kpi-lbl">Available</div><div class="kpi-num" style="color:#22c55e">{avail}</div></div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="kpi-card"><div class="kpi-lbl">Exp. Free ({fc}h)</div><div class="kpi-num" style="color:#a855f7">{exp_free}</div></div>""", unsafe_allow_html=True)

    # File Ops (Requested Placement)
    with st.expander("📂 Data Management"):
        c_dl, c_up = st.columns(2)
        c_dl.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv")
        up_f = c_up.file_uploader("Upload CSV", type=['csv'])
        if up_f:
            try:
                new_df = pd.read_csv(up_f)
                for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']: new_df[col] = pd.to_datetime(new_df[col])
                st.session_state.df = new_df
                st.rerun()
            except: st.error("Error")

    # Department Grid
    st.markdown("### Department Status")
    d_cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_names):
        info = DEPARTMENTS[dept]
        d_df = active[active['Department'] == dept]
        d_occ = len(d_df)
        d_pct = (d_occ / info['cap']) * 100
        d_ready = d_df[d_df['Exp_Discharge'] <= future].shape[0]
        
        # Color Logic
        if d_pct < 70: status, cls = "SAFE", "st-safe"
        elif 70 <= d_pct <= 84: status, cls = "WARNING", "st-warn"
        else: status, cls = "CRITICAL", "st-crit"
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-box">
                <div class="dept-title">
                    <span>{dept}</span>
                    <span class="status-badge {cls}">{status}</span>
                </div>
                <div style="font-size:12px; color:#8B949E; margin-top:10px; display:flex; justify-content:space-between;">
                    <span>Cap: {info['cap']}</span>
                    <span>Occ: <b style="color:white">{d_occ}</b></span>
                    <span>Free: {info['cap']-d_occ}</span>
                </div>
                <div style="font-size:12px; color:#a855f7; margin-top:5px; font-weight:bold;">
                    Exp. Free ({fc}h): {d_ready}
                </div>
                <div style="background:#21262D; height:5px; margin-top:8px; border-radius:3px;">
                    <div style="width:{min(d_pct,100)}%; height:100%; background:{'#22c55e' if d_pct<70 else '#eab308' if d_pct<85 else '#ef4444'};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions (Fixed Dates & Discharge)
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Admission & Discharge Center")
    
    # --- Part 1: Admission Form ---
    with st.expander("➕ Admit New Patient", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
            gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
            if pin != "Select...": st.info(f"Gender: **{gender}**")
            
            dept = st.selectbox("Assign Department", ["Select..."] + list(DEPARTMENTS.keys()))
            
            # Filter Beds
            bed_opts = ["Select Dept"]
            if dept != "Select...":
                if DEPARTMENTS[dept]['gen'] != "Mixed" and DEPARTMENTS[dept]['gen'] != gender:
                    st.error(f"Gender Mismatch! {dept} is {DEPARTMENTS[dept]['gen']} Only.")
                
                occ_beds = df[(df['Department'] == dept) & (df['Actual_Discharge'].isna())]['Bed'].tolist()
                all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
                free_beds = [b for b in all_beds if b not in occ_beds]
                bed_opts = free_beds if free_beds else ["NO BEDS"]
            bed = st.selectbox("Assign Bed", bed_opts)

        with c2:
            # FIXED: Date & Time Pickers
            st.markdown("###### Admission Time")
            d1, t1 = st.columns(2)
            adm_d = d1.date_input("Date", datetime.now())
            adm_t = t1.time_input("Time", datetime.now().time())
            
            st.markdown("###### Expected Discharge")
            d2, t2 = st.columns(2)
            exp_d = d2.date_input("Exp Date", datetime.now() + timedelta(days=3))
            exp_t = t2.time_input("Exp Time", datetime.now().time())
            
            src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

        if st.button("Confirm Admission", type="primary", use_container_width=True):
            if pin != "Select..." and dept != "Select..." and bed not in ["Select Dept", "NO BEDS"]:
                new_rec = {
                    "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                    "Admit_Date": datetime.combine(adm_d, adm_t),
                    "Exp_Discharge": datetime.combine(exp_d, exp_t),
                    "Actual_Discharge": pd.NaT,
                    "Source": src
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
                st.success("Admitted Successfully.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("Please check fields.")

    st.markdown("---")

    # --- Part 2: Discharge / Active List ---
    st.subheader("Current Inpatients (Manage & Discharge)")
    active_df = df[df['Actual_Discharge'].isna()].sort_values(by="Admit_Date", ascending=False)
    
    if not active_df.empty:
        # Discharge UI
        target = st.selectbox("Select Patient to Discharge", ["Select..."] + active_df['PIN'].tolist())
        
        if target != "Select...":
            row = active_df[active_df['PIN'] == target].iloc[0]
            st.warning(f"Discharging: **{row['PIN']}** from **{row['Bed']}**")
            
            # Actual Discharge Time
            dc1, dc2 = st.columns(2)
            act_d = dc1.date_input("Actual Discharge Date", datetime.now())
            act_t = dc2.time_input("Actual Discharge Time", datetime.now().time())
            
            if st.button("Confirm Discharge"):
                idx = df[(df['PIN'] == target) & (df['Actual_Discharge'].isna())].index
                st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(act_d, act_t)
                st.success("Patient Discharged.")
                time.sleep(0.5)
                st.rerun()
                
        st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Admit_Date', 'Exp_Discharge']], use_container_width=True)
    else:
        st.info("No active patients.")

# ---------------------------------------------------------
# 6. Analytics
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Operational Analytics")
    
    calc = df.copy()
    now = datetime.now()
    
    # 1. Admission by Source
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("###### Admissions by Source")
        if not calc.empty:
            fig = px.pie(calc, names='Source', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(paper_bgcolor="#0E1117", font={'color': "white"})
            st.plotly_chart(fig, use_container_width=True)
            
    # 2. LOS
    with c2:
        st.markdown("###### Length of Stay Analysis")
        # Calculate LOS for discharged only
        discharged = calc[calc['Actual_Discharge'].notnull()].copy()
        if not discharged.empty:
            discharged['LOS'] = (discharged['Actual_Discharge'] - discharged['Admit_Date']).dt.total_seconds() / 86400
            fig2 = px.box(discharged, x="Department", y="LOS", color="Department")
            fig2.update_layout(paper_bgcolor="#0E1117", font={'color': "white"}, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No discharge data yet.")

    # 3. Efficiency Table
    st.markdown("###### Department Efficiency")
    mat = calc.groupby('Department').size().reset_index(name='Total_Admissions')
    mat['Capacity'] = mat['Department'].apply(lambda x: DEPARTMENTS[x]['cap'])
    st.dataframe(mat, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("Settings")
    if st.button("Factory Reset (Clear All Data)", type="primary"):
        del st.session_state.df
        st.success("System Cleared.")
        time.sleep(1)
        st.rerun()
