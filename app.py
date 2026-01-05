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
    /* Global Corporate Dark Theme */
    .stApp { background-color: #0E1117; color: #E6EDF3; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    /* Glowing Logo Effect */
    @keyframes glow {
        from { text-shadow: 0 0 5px #fff, 0 0 10px #238636; }
        to { text-shadow: 0 0 10px #fff, 0 0 20px #238636; }
    }
    .glow-header { font-size: 20px; font-weight: bold; animation: glow 2s infinite alternate; text-align: center; margin-bottom: 20px; }

    /* KPI Cards */
    .kpi-container {
        background: #161B22; border: 1px solid #30363D; border-radius: 8px;
        padding: 20px; text-align: center; transition: transform 0.2s;
    }
    .kpi-container:hover { border-color: #58A6FF; transform: translateY(-2px); }
    .kpi-label { font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #FFF; margin: 8px 0; }
    
    /* Department Cards */
    .dept-card {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px; border-left: 4px solid #30363D;
    }
    .dept-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .dept-title { font-size: 15px; font-weight: 700; color: #FFF; }
    
    /* Status Badges */
    .badge { padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
    .b-safe { background: rgba(35, 134, 54, 0.2); color: #3FB950; border: 1px solid #238636; }
    .b-warn { background: rgba(210, 153, 34, 0.2); color: #D29922; border: 1px solid #9E6A03; }
    .b-crit { background: rgba(218, 54, 51, 0.2); color: #F85149; border: 1px solid #DA3633; }

    /* AI Box */
    .ai-rec-box {
        background: #161B22; border: 1px solid #30363D; border-left: 5px solid #A371F7;
        border-radius: 6px; padding: 15px; margin-bottom: 20px;
    }
    .ai-title { color: #A371F7; font-weight: bold; font-size: 14px; margin-bottom: 8px; }
    
    /* Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    button[kind="primary"] { background: linear-gradient(90deg, #238636, #2EA043) !important; border: none !important; color: white !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Logic & Data Initialization
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
        
        # Initial Data Seeding (Clean & Logical)
        data = []
        for dept, info in DEPARTMENTS.items():
            # Fill ~50-70% capacity
            count = int(info['cap'] * np.random.uniform(0.5, 0.7))
            for i in range(count):
                bed_n = f"{dept[:3].upper()}-{i+1:03d}"
                # Realistic dates
                adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 10))
                exp = adm + timedelta(days=np.random.randint(2, 8))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(1000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": bed_n,
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": pd.NaT, # Active status
                    "Source": np.random.choice(["Emergency", "Elective", "Transfer"])
                })
        st.session_state.df = pd.DataFrame(data)

init_system()
df = st.session_state.df

# Type Enforcement
for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar (Enhanced with Search)
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<div class='glow-header'>🏥 OccupyBed AI</div>", unsafe_allow_html=True)
    
    # --- NEW: Patient Search ---
    st.markdown("### 🔍 Find Patient")
    search_query = st.text_input("Enter PIN (e.g. PIN-2040)")
    if search_query:
        result = df[(df['PIN'] == search_query) & (df['Actual_Discharge'].isna())]
        if not result.empty:
            r = result.iloc[0]
            st.success(f"Found in: **{r['Department']}**")
            st.caption(f"Bed: {r['Bed']} | Admitted: {r['Admit_Date'].strftime('%d-%m %H:%M')}")
        else:
            st.error("Patient not found or discharged.")
    
    st.markdown("---")
    menu = st.radio("NAVIGATION", ["Overview", "Live Admissions", "Analytics", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    st.caption(f"Server: JED-HOSP-01\nStatus: Online 🟢")

# ---------------------------------------------------------
# 4. OVERVIEW (Dashboard)
# ---------------------------------------------------------
if menu == "Overview":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: 
        fc_hours = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")

    # --- Calculations ---
    now = datetime.now()
    active_df = df[df['Actual_Discharge'].isna()]
    future_limit = now + timedelta(hours=fc_hours)
    
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    occ_count = len(active_df)
    avail_count = total_cap - occ_count
    ready_count = len(active_df[active_df['Exp_Discharge'] <= future_limit])

    # Net Flow
    last_24 = now - timedelta(hours=24)
    in_24 = len(df[df['Admit_Date'] >= last_24])
    out_24 = len(df[df['Actual_Discharge'] >= last_24])
    net = in_24 - out_24

    # --- AI Insights ---
    st.markdown(f"""<div class="ai-rec-box"><div class="ai-title">🤖 AI Operational Insights</div>""", unsafe_allow_html=True)
    msgs = []
    for dept, info in DEPARTMENTS.items():
        d_pats = active_df[active_df['Department'] == dept]
        pct = (len(d_pats)/info['cap'])*100
        
        if pct >= 85:
            st.markdown(f"""<div style="font-size:13px; color:#E6EDF3; margin-bottom:4px;">🚨 <b>{dept}:</b> Critical load ({int(pct)}%). Divert to {info['overflow']}.</div>""", unsafe_allow_html=True)
            msgs.append(1)
        elif len(d_pats[d_pats['Exp_Discharge'] < now]) > 3:
            st.markdown(f"""<div style="font-size:13px; color:#E6EDF3; margin-bottom:4px;">⚠️ <b>{dept}:</b> Delayed discharges detected. Check barriers.</div>""", unsafe_allow_html=True)
            msgs.append(1)
            
    if not msgs: st.markdown("""<div style="font-size:13px; color:#3FB950;">System operating optimally. No critical bottlenecks.</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- KPIs ---
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"""<div class="kpi-container"><div class="kpi-label">Occupancy</div><div class="kpi-value" style="color:#D29922">{occ_count}</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="kpi-container"><div class="kpi-label">Available Beds</div><div class="kpi-value" style="color:#3FB950">{avail_count}</div></div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="kpi-container"><div class="kpi-label">Ready ({fc_hours}h)</div><div class="kpi-value" style="color:#A371F7">{ready_count}</div></div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="kpi-container"><div class="kpi-label">Net Flow (24h)</div><div class="kpi-value" style="color:{'#F85149' if net>0 else '#3FB950'}">{net:+d}</div></div>""", unsafe_allow_html=True)

    # --- File Ops ---
    with st.expander("📂 File Data Management", expanded=False):
        c_dl, c_ul = st.columns(2)
        c_dl.download_button("Download Database (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_db.csv", "text/csv")
        ul_file = c_ul.file_uploader("Upload CSV", type=['csv'])
        if ul_file:
            try:
                new_df = pd.read_csv(ul_file)
                for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']: new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
                st.session_state.df = new_df
                st.rerun()
            except: st.error("Error loading file")

    st.markdown("---")

    # --- Department Grid ---
    st.markdown("### Department Status Matrix")
    d_cols = st.columns(3)
    for i, (dept, info) in enumerate(DEPARTMENTS.items()):
        d_df = active_df[active_df['Department'] == dept]
        occ = len(d_df)
        pct = (occ / info['cap']) * 100
        ready = len(d_df[d_df['Exp_Discharge'] <= future_limit])
        
        if pct < 70: status, cls, col = "SAFE", "b-safe", "#238636"
        elif 70 <= pct <= 84: status, cls, col = "WARNING", "b-warn", "#D29922"
        else: status, cls, col = "CRITICAL", "b-crit", "#F85149"
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card" style="border-left-color: {col};">
                <div class="dept-header">
                    <span class="dept-title">{dept}</span>
                    <span class="badge {cls}">{status}</span>
                </div>
                <div style="font-size:12px; color:#8B949E; display:flex; justify-content:space-between;">
                    <span>Occupied: <b style="color:#E6EDF3">{occ} / {info['cap']}</b></span>
                    <span>Ready ({fc_hours}h): <b style="color:#A371F7">{ready}</b></span>
                </div>
                <div style="background:#21262D; height:5px; border-radius:3px; margin-top:8px;">
                    <div style="width:{min(pct,100)}%; background:{col}; height:100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Live Admissions (Smart Logic)
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Admissions & Discharge Center")
    
    # A. New Admission
    with st.expander("➕ New Admission Entry", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
            gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
            if pin != "Select...": st.info(f"System Check: **{gender}**")
            
            dept = st.selectbox("Department", ["Select..."] + list(DEPARTMENTS.keys()))
            
            # Bed Logic: Only show empty beds
            bed_opts = ["Select Dept"]
            if dept != "Select...":
                if DEPARTMENTS[dept]['gen'] != "Mixed" and DEPARTMENTS[dept]['gen'] != gender:
                    st.error(f"Gender Mismatch: {dept} is {DEPARTMENTS[dept]['gen']} Only.")
                
                occ_beds = df[(df['Department'] == dept) & (df['Actual_Discharge'].isna())]['Bed'].tolist()
                all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
                free = [b for b in all_beds if b not in occ_beds]
                bed_opts = free if free else ["NO BEDS"]
            bed = st.selectbox("Bed", bed_opts)

        with c2:
            st.markdown("###### Timeline Setup")
            d1, t1 = st.columns(2)
            ad_d = d1.date_input("Admit Date", datetime.now())
            ad_t = t1.time_input("Admit Time", datetime.now().time())
            
            st.markdown("###### Discharge Plan")
            d2, t2 = st.columns(2)
            ex_d = d2.date_input("Expected Date", datetime.now() + timedelta(days=3))
            ex_t = t2.time_input("Expected Time", datetime.now().time())
            
            src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

        if st.button("Confirm Admission", type="primary", use_container_width=True):
            if pin != "Select..." and dept != "Select..." and bed not in ["Select Dept", "NO BEDS"]:
                new_rec = {
                    "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                    "Admit_Date": datetime.combine(ad_d, ad_t),
                    "Exp_Discharge": datetime.combine(ex_d, ex_t),
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

    # B. Discharge Management
    st.subheader("Current Inpatients (Real-time List)")
    active_df = df[df['Actual_Discharge'].isna()].copy()
    
    if not active_df.empty:
        # Calculate Current LOS for display
        active_df['Current_LOS'] = (datetime.now() - active_df['Admit_Date']).dt.total_seconds() / 86400
        active_df['Current_LOS'] = active_df['Current_LOS'].apply(lambda x: f"{x:.1f} days")
        
        # Sort
        active_df = active_df.sort_values('Admit_Date', ascending=False)
        
        # Discharge UI
        target = st.selectbox("Select Patient to Discharge", ["Select..."] + active_df['PIN'].tolist())
        
        if target != "Select...":
            row = active_df[active_df['PIN'] == target].iloc[0]
            st.info(f"Processing Discharge: **{row['PIN']}** | **{row['Department']}** | **{row['Bed']}**")
            
            c_d, c_t = st.columns(2)
            act_d = c_d.date_input("Actual Discharge Date", datetime.now())
            act_t = c_t.time_input("Actual Discharge Time", datetime.now().time())
            
            if st.button("Confirm Discharge"):
                idx = df[(df['PIN'] == target) & (df['Actual_Discharge'].isna())].index
                st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(act_d, act_t)
                st.success("Patient Discharged.")
                time.sleep(0.5)
                st.rerun()
                
        # Display Table with LOS
        st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Gender', 'Admit_Date', 'Exp_Discharge', 'Current_LOS']], use_container_width=True)
    else:
        st.info("No active patients.")

# ---------------------------------------------------------
# 6. Analytics
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Operational KPIs")
    
    calc = df.copy()
    now = datetime.now()
    
    # 1. Total Metrics
    total_adm = len(calc)
    total_dis = len(calc[calc['Actual_Discharge'].notnull()])
    
    # 2. ALOS
    def calc_los(r):
        end = r['Actual_Discharge'] if pd.notnull(r['Actual_Discharge']) else now
        return (end - r['Admit_Date']).total_seconds() / 86400
    calc['LOS'] = calc.apply(calc_los, axis=1)
    
    # 3. Turnover
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    turnover = total_dis / total_cap
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Admissions", total_adm)
    m2.metric("Total Discharges", total_dis)
    m3.metric("Avg LOS", f"{calc['LOS'].mean():.1f} Days")
    m4.metric("Bed Turnover", f"{turnover:.2f}", "Turns/Bed")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Admissions by Source")
        if not calc.empty:
            fig = px.pie(calc, names='Source', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(paper_bgcolor="#0E1117", font={'color': "white"})
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.markdown("##### Occupancy by Department")
        active = calc[calc['Actual_Discharge'].isna()]
        if not active.empty:
            cnt = active['Department'].value_counts().reset_index()
            cnt.columns = ['Department', 'Count']
            fig2 = px.bar(cnt, y='Department', x='Count', orientation='h', color='Count', color_continuous_scale='Bluered')
            fig2.update_layout(paper_bgcolor="#0E1117", font={'color': "white"})
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    if st.button("FACTORY RESET (Clear Database)", type="primary"):
        del st.session_state.df
        st.success("System Reset.")
        time.sleep(1)
        st.rerun()
