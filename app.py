import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. Page Configuration (Clean & Simple)
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI", layout="wide", page_icon="🏥")

# Minimalist CSS (Clean Dark Mode)
st.markdown("""
<style>
    /* Professional Dark Theme */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #262730; }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] { font-size: 24px; color: #4F8BF9; }
    
    /* Tables */
    [data-testid="stDataFrame"] { border: 1px solid #444; border-radius: 5px; }
    
    /* AI Recommendation Box (Simple) */
    .ai-box {
        padding: 15px; border-radius: 5px; background-color: #1E1E1E;
        border-left: 5px solid #FFBD45; margin-bottom: 20px;
    }
    .ai-text { font-size: 14px; color: #E0E0E0; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Logic & Data
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
            "PIN", "Gender", "Department", "Bed", 
            "Admit_Date", "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # Clean Initial Data (Reasonable Load)
        data = []
        for dept, info in DEPARTMENTS.items():
            count = int(info['cap'] * 0.5) # 50% Load
            for i in range(count):
                bed_n = f"{dept[:3].upper()}-{i+1:03d}"
                adm = datetime.now() - timedelta(days=np.random.randint(1, 5))
                exp = adm + timedelta(days=np.random.randint(2, 7))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(1000, 9000)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": bed_n,
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": pd.NaT,
                    "Source": "Emergency"
                })
        st.session_state.df = pd.DataFrame(data)

init_system()
df = st.session_state.df

# Fix Types
for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar (Simple Navigation)
# ---------------------------------------------------------
with st.sidebar:
    st.header("🏥 OccupyBed AI")
    
    # 1. Search (New Addition)
    st.markdown("### 🔍 Patient Search")
    search_q = st.text_input("Enter PIN", placeholder="e.g. PIN-1050")
    if search_q:
        res = df[(df['PIN'] == search_q) & (df['Actual_Discharge'].isna())]
        if not res.empty:
            r = res.iloc[0]
            st.success(f"Loc: {r['Department']}\nBed: {r['Bed']}")
        else:
            st.warning("Not found or discharged.")

    st.markdown("---")
    menu = st.radio("Go To", ["Overview", "Admissions & Discharge", "Analytics", "Settings"])
    st.markdown("---")

# ---------------------------------------------------------
# 4. Overview (Clean Dashboard)
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Dashboard")
    with c2: 
        fc = st.selectbox("Forecast", [6, 12, 24, 48], format_func=lambda x: f"{x} Hours")

    # Metrics
    now = datetime.now()
    active_df = df[df['Actual_Discharge'].isna()]
    
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    occ = len(active_df)
    avail = total_cap - occ
    ready = len(active_df[active_df['Exp_Discharge'] <= (now + timedelta(hours=fc))])
    
    # Simple Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Beds", total_cap)
    m2.metric("Occupied", occ, f"{int(occ/total_cap*100)}%")
    m3.metric("Available", avail)
    m4.metric(f"Ready ({fc}h)", ready)

    # AI Suggestion (Clean Text Box)
    st.markdown("### 🤖 AI Recommendations")
    alerts = []
    for dept, info in DEPARTMENTS.items():
        d_occ = len(active_df[active_df['Department'] == dept])
        if (d_occ/info['cap']) > 0.85:
            alerts.append(f"🔴 **{dept}** is Critical (>85%). Consider transfers.")
    
    if alerts:
        for a in alerts: st.markdown(f"<div class='ai-box'><span class='ai-text'>{a}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='ai-box'><span class='ai-text'>🟢 Operations are stable. No critical actions needed.</span></div>", unsafe_allow_html=True)

    # Department Status Table (Professional Look)
    st.markdown("### Department Status")
    
    dept_stats = []
    for dept, info in DEPARTMENTS.items():
        d_df = active_df[active_df['Department'] == dept]
        d_occ = len(d_df)
        d_avail = info['cap'] - d_occ
        d_ready = len(d_df[d_df['Exp_Discharge'] <= (now + timedelta(hours=fc))])
        status = "Critical" if (d_occ/info['cap']) > 0.85 else ("Warning" if (d_occ/info['cap']) > 0.7 else "Safe")
        
        dept_stats.append({
            "Department": dept,
            "Capacity": info['cap'],
            "Occupied": d_occ,
            "Available": d_avail,
            "Forecast Free": d_ready,
            "Status": status
        })
    
    st.dataframe(
        pd.DataFrame(dept_stats),
        use_container_width=True,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Operational Status",
                validate="^(Safe|Warning|Critical)$"
            )
        }
    )

# ---------------------------------------------------------
# 5. Admissions & Discharge (Functional Fixes)
# ---------------------------------------------------------
elif menu == "Admissions & Discharge":
    st.title("Admissions & Discharge")
    
    tab1, tab2 = st.tabs(["New Admission", "Discharge Patient"])
    
    # --- Tab 1: Admission ---
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            pin = st.selectbox("Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
            gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
            if pin != "Select...": st.success(f"Gender: {gender}")
            
            dept = st.selectbox("Department", ["Select..."] + list(DEPARTMENTS.keys()))
            
            # Bed Logic
            bed_opts = ["Select Dept"]
            if dept != "Select...":
                occ_beds = df[(df['Department'] == dept) & (df['Actual_Discharge'].isna())]['Bed'].tolist()
                all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
                free_beds = [b for b in all_beds if b not in occ_beds]
                bed_opts = free_beds if free_beds else ["FULL"]
            bed = st.selectbox("Bed", bed_opts)

        with col2:
            # Date/Time Logic (Requested)
            st.markdown("**Admission Time**")
            ad_d = st.date_input("Date", datetime.now())
            ad_t = st.time_input("Time", datetime.now().time())
            
            st.markdown("**Expected Discharge**")
            ex_d = st.date_input("Exp Date", datetime.now() + timedelta(days=3))
            ex_t = st.time_input("Exp Time", datetime.now().time())
            
            src = st.selectbox("Source", ["Emergency", "Elective"])

        if st.button("Confirm Admission", type="primary"):
            if pin != "Select..." and dept != "Select..." and bed not in ["Select Dept", "FULL"]:
                new_row = {
                    "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                    "Admit_Date": datetime.combine(ad_d, ad_t),
                    "Exp_Discharge": datetime.combine(ex_d, ex_t),
                    "Actual_Discharge": pd.NaT,
                    "Source": src
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Saved.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Invalid Input")

    # --- Tab 2: Discharge ---
    with tab2:
        st.subheader("Process Discharge")
        active_df = df[df['Actual_Discharge'].isna()].copy()
        
        if not active_df.empty:
            # Dropdown for active patients
            p_list = active_df.apply(lambda x: f"{x['PIN']} - {x['Department']} - {x['Bed']}", axis=1).tolist()
            target = st.selectbox("Select Patient", ["Select..."] + p_list)
            
            if target != "Select...":
                t_pin = target.split(" - ")[0]
                
                c_d, c_t = st.columns(2)
                act_d = c_d.date_input("Discharge Date", datetime.now())
                act_t = c_t.time_input("Discharge Time", datetime.now().time())
                
                if st.button("Confirm Discharge Action"):
                    # Logic: Find and Update
                    mask = (df['PIN'] == t_pin) & (df['Actual_Discharge'].isna())
                    df.loc[mask, 'Actual_Discharge'] = datetime.combine(act_d, act_t)
                    st.session_state.df = df
                    st.success("Patient Discharged Successfully.")
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.info("No active patients.")

# ---------------------------------------------------------
# 6. Analytics
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Analytics")
    
    calc = df.copy()
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Occupancy Distribution")
        active = calc[calc['Actual_Discharge'].isna()]
        if not active.empty:
            fig = px.pie(active, names='Department', hole=0.5)
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.markdown("##### Admissions by Source")
        if not calc.empty:
            fig2 = px.bar(calc['Source'].value_counts().reset_index(), x='Source', y='count')
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("Settings")
    if st.button("Factory Reset (Clear All Data)"):
        del st.session_state.df
        st.rerun()
