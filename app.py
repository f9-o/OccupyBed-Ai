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
st.set_page_config(page_title="OccupyBed AI | Enterprise", layout="wide", page_icon="🏥")

# Force Dark Theme & Clean UI
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* KPI Cards */
    .kpi-box {
        background: #161B22; border: 1px solid #30363D; border-radius: 6px;
        padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .kpi-title { color: #8B949E; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }
    .kpi-val { color: #F0F6FC; font-size: 32px; font-weight: 700; margin: 5px 0; }
    .kpi-sub { font-size: 11px; color: #58A6FF; }

    /* Department Cards */
    .dept-card {
        background: #0D1117; border: 1px solid #30363D; border-radius: 6px; padding: 15px; margin-bottom: 10px;
    }
    .dept-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .dept-name { font-weight: 700; color: #E6EDF3; font-size: 14px; }
    
    /* Status Tags (No Emojis) */
    .tag { padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; }
    .tag-safe { background: rgba(35, 134, 54, 0.2); color: #3FB950; border: 1px solid #238636; }
    .tag-warn { background: rgba(210, 153, 34, 0.2); color: #D29922; border: 1px solid #9E6A03; }
    .tag-crit { background: rgba(218, 54, 51, 0.2); color: #F85149; border: 1px solid #DA3633; }

    /* Tables & Inputs */
    [data-testid="stDataFrame"] { border: 1px solid #30363D; }
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Logic & Data Initialization
# ---------------------------------------------------------

DEPARTMENTS = {
    "ICU": {"cap": 16, "gen": "Mixed"},
    "Surgical Male": {"cap": 40, "gen": "Male"},
    "Surgical Female": {"cap": 40, "gen": "Female"},
    "Medical Male": {"cap": 50, "gen": "Male"},
    "Medical Female": {"cap": 50, "gen": "Female"},
    "Pediatric": {"cap": 30, "gen": "Mixed"},
    "Obstetrics": {"cap": 24, "gen": "Female"},
}

PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(500)}

def init_system():
    # Force reset if version mismatch or first run
    if 'version' not in st.session_state or st.session_state.version != '4.0':
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", "Admit_Date", 
            "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # Generate Valid Data (Strict Capacity Check)
        new_data = []
        for dept, info in DEPARTMENTS.items():
            # Fill 50-80% of capacity to prevent overflow
            count = int(info['cap'] * np.random.uniform(0.5, 0.8))
            for i in range(count):
                bed_n = i + 1
                adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 10))
                exp = adm + timedelta(days=np.random.randint(2, 7))
                
                new_data.append({
                    "PIN": f"PIN-{np.random.randint(2000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": f"{dept[:3].upper()}-{bed_n:03d}",
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": None, # Active patient
                    "Source": "Emergency"
                })
        
        st.session_state.df = pd.DataFrame(new_data)
        st.session_state.version = '4.0' # Mark version

init_system()
df = st.session_state.df

# ---------------------------------------------------------
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("### OccupyBed AI")
        
    st.markdown("---")
    menu = st.radio("MODULES", ["Overview", "Live Admissions", "Analytics", "Settings"], label_visibility="collapsed")
    
    st.markdown("---")
    # Reset Button for Debugging
    if st.button("HARD RESET DATA", help="Click if numbers look wrong"):
        del st.session_state.version
        st.rerun()

# ---------------------------------------------------------
# 4. Overview Module
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: fc = st.selectbox("Forecast Horizon", [6, 12, 24, 48], index=2, format_func=lambda x: f"{x} Hours")

    # Real Calculations
    active = df[df['Actual_Discharge'].isnull()]
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    curr_occ = len(active)
    avail = total_cap - curr_occ
    
    future = datetime.now() + timedelta(hours=fc)
    # Count patients where Expected Discharge is BEFORE future time
    exp_free = active[active['Exp_Discharge'] <= future].shape[0]

    # KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"""<div class="kpi-box"><div class="kpi-title">Licensed Beds</div><div class="kpi-val" style="color:#58A6FF">{total_cap}</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="kpi-box"><div class="kpi-title">Occupied</div><div class="kpi-val" style="color:#D29922">{curr_occ}</div></div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="kpi-box"><div class="kpi-title">Available</div><div class="kpi-val" style="color:#238636">{avail}</div></div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="kpi-box"><div class="kpi-title">Exp. Free ({fc}h)</div><div class="kpi-val" style="color:#A371F7">{exp_free}</div></div>""", unsafe_allow_html=True)

    # Visual Bed Matrix
    st.markdown("### Department Status Matrix")
    cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, d_name in enumerate(dept_names):
        info = DEPARTMENTS[d_name]
        d_pats = active[active['Department'] == d_name]
        d_count = len(d_pats)
        d_pct = (d_count / info['cap']) * 100
        
        # Forecast for this department
        d_free = d_pats[d_pats['Exp_Discharge'] <= future].shape[0]
        
        # Tags
        color, tag_cls, txt = "#238636", "tag-safe", "STABLE"
        if d_pct > 80: color, tag_cls, txt = "#D29922", "tag-warn", "BUSY"
        if d_pct >= 100: color, tag_cls, txt = "#DA3633", "tag-crit", "FULL"
        
        with cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card" style="border-left: 4px solid {color};">
                <div class="dept-head">
                    <span class="dept-name">{d_name}</span>
                    <span class="tag {tag_cls}">{txt}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#8B949E; margin-bottom:5px;">
                    <span>Occupied: <b style="color:#E6EDF3">{d_count} / {info['cap']}</b></span>
                    <span>Exp Free: <b style="color:#A371F7">{d_free}</b></span>
                </div>
                <div style="background:#21262D; height:6px; border-radius:3px; overflow:hidden;">
                    <div style="width:{min(d_pct, 100)}%; background:{color}; height:100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions (Fixed Date/Time & Table)
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission Center")
    
    # 1. Action Bar
    with st.expander("Data Management (Import/Export)"):
        c1, c2 = st.columns(2)
        c1.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "hospital.csv", "text/csv")
        up = c2.file_uploader("Upload CSV", type=['csv'])
        if up:
            try:
                new_df = pd.read_csv(up)
                for c in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
                    new_df[c] = pd.to_datetime(new_df[c])
                st.session_state.df = new_df
                st.rerun()
            except: st.error("Invalid File")

    st.markdown("---")

    # 2. Admission Form (Corrected with Date/Time)
    st.subheader("Admit New Patient")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        pin = st.selectbox("Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
        gen = "Unknown"
        if pin != "Select...":
            gen = PATIENT_DB.get(pin, "Unknown")
            st.info(f"Detected Gender: **{gen}**")
            
        dept = st.selectbox("Department", ["Select..."] + list(DEPARTMENTS.keys()))
        
        # Logic Check
        if pin != "Select..." and dept != "Select...":
            rule = DEPARTMENTS[dept]['gen']
            if rule != "Mixed" and rule != gen:
                st.error(f"⚠️ Conflict: {dept} is {rule} Only.")
        
        # Bed Filter (Strictly Empty Beds)
        bed_opts = ["Select Dept"]
        if dept != "Select...":
            active_dept = df[(df['Department']==dept) & (df['Actual_Discharge'].isnull())]
            busy = active_dept['Bed'].tolist()
            cap = DEPARTMENTS[dept]['cap']
            all_b = [f"{dept[:3].upper()}-{i:03d}" for i in range(1, cap+1)]
            avail = [b for b in all_b if b not in busy]
            bed_opts = avail if avail else ["No Beds Available"]
            
        bed = st.selectbox("Bed", bed_opts)

    with col_f2:
        # Admission Time
        c_d1, c_t1 = st.columns(2)
        ad_date = c_d1.date_input("Admit Date", datetime.now())
        ad_time = c_t1.time_input("Admit Time", datetime.now().time())
        
        st.markdown("**Expected Discharge Plan**")
        # Discharge Time (The Fix You Asked For)
        c_d2, c_t2 = st.columns(2)
        ex_date = c_d2.date_input("Exp. Date", datetime.now() + timedelta(days=3))
        ex_time = c_t2.time_input("Exp. Time", datetime.now().time())
        
        src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

    if st.button("Confirm Admission", type="primary", use_container_width=True):
        if pin != "Select..." and dept != "Select..." and bed not in ["Select Dept", "No Beds Available"]:
            new_rec = {
                "PIN": pin, "Gender": gen, "Department": dept, "Bed": bed,
                "Admit_Date": datetime.combine(ad_date, ad_time),
                "Exp_Discharge": datetime.combine(ex_date, ex_time),
                "Actual_Discharge": None, "Source": src
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
            st.success(f"Patient {pin} admitted to {bed}")
            time.sleep(0.5)
            st.rerun()
        else:
            st.warning("Please verify all fields.")

    # 3. Active Patient Table (Management)
    st.markdown("### Active Patient Management")
    active_df = df[df['Actual_Discharge'].isnull()]
    
    if not active_df.empty:
        # Quick Discharge
        p_list = active_df.apply(lambda x: f"{x['PIN']} | {x['Bed']}", axis=1).tolist()
        target = st.selectbox("Select Patient to Discharge", ["Select..."] + p_list)
        
        if target != "Select...":
            t_pin, t_bed = target.split(" | ")
            col_act1, col_act2 = st.columns([3, 1])
            with col_act1: st.warning(f"Discharging **{t_pin}** from **{t_bed}**?")
            with col_act2: 
                if st.button("Confirm Discharge"):
                    idx = df[(df['PIN'] == t_pin) & (df['Bed'] == t_bed) & (df['Actual_Discharge'].isnull())].index
                    st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.now()
                    st.success("Discharged.")
                    st.rerun()
        
        # Display Table
        st.dataframe(
            active_df[['PIN', 'Department', 'Bed', 'Admit_Date', 'Exp_Discharge', 'Source']].sort_values('Admit_Date', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No active patients.")

# ---------------------------------------------------------
# 6. Analytics Module
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Operational Analytics")
    
    calc = df.copy()
    now = datetime.now()
    calc['LOS'] = calc.apply(lambda x: ((x['Actual_Discharge'] if pd.notnull(x['Actual_Discharge']) else now) - x['Admit_Date']).total_seconds()/86400, axis=1)
    
    k1, k2, k3, k4 = st.columns(4)
    avg_los = calc['LOS'].mean()
    discharges = len(calc[calc['Actual_Discharge'].notnull()])
    
    k1.metric("Avg LOS", f"{avg_los:.1f} Days")
    k2.metric("Total Admissions", len(calc))
    k3.metric("Discharged", discharges)
    k4.metric("Active", len(calc[calc['Actual_Discharge'].isnull()]))
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("###### Admissions by Source")
        if not calc.empty:
            fig = px.pie(calc, names='Source', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#E6EDF3"})
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.markdown("###### Efficiency Matrix")
        mat = calc.groupby('Department').agg(
            Volume=('PIN', 'count'),
            Active=('Actual_Discharge', lambda x: x.isnull().sum()),
            ALOS=('LOS', 'mean')
        ).reset_index()
        mat['Capacity'] = mat['Department'].apply(lambda x: DEPARTMENTS.get(x, {}).get('cap', 0))
        mat['Occ %'] = (mat['Active']/mat['Capacity']*100).round(1)
        
        st.dataframe(
            mat[['Department', 'Capacity', 'Active', 'Occ %', 'ALOS']].sort_values('Occ %', ascending=False),
            use_container_width=True,
            hide_index=True
        )

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("Settings")
    if st.button("HARD RESET SYSTEM (Clear All Data)", type="primary"):
        del st.session_state.df
        del st.session_state.version
        st.rerun()
