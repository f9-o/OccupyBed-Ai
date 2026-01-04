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
    
    /* AI Board Section */
    .ai-board {
        background: linear-gradient(145deg, #161B22, #0D1117);
        border: 1px solid #30363D; border-left: 5px solid #A371F7;
        border-radius: 8px; padding: 20px; margin-bottom: 20px;
    }
    .ai-title { font-size: 16px; font-weight: bold; color: #A371F7; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
    .ai-msg { font-size: 14px; color: #E6EDF3; margin-bottom: 5px; }
    .ai-tag { font-size: 11px; background: #1F2428; padding: 2px 8px; border-radius: 4px; color: #8B949E; border: 1px solid #30363D; }

    /* KPI Matrix */
    .kpi-container {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; text-align: center; height: 100%;
        transition: all 0.3s;
    }
    .kpi-container:hover { border-color: #58A6FF; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
    .kpi-label { color: #8B949E; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .kpi-val { color: #F0F6FC; font-size: 28px; font-weight: 700; margin: 0; }
    .kpi-delta { font-size: 12px; font-weight: 600; margin-top: 5px; }
    
    /* Department Cards with Indicators */
    .dept-card-pro {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px; position: relative;
    }
    .dept-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .dept-name { font-size: 14px; font-weight: 700; color: #E6EDF3; }
    .indicator-dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; }
    
    /* Visual Bed Matrix */
    .bed-grid { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 8px; }
    .bed-box { width: 10px; height: 10px; border-radius: 2px; }
    .b-free { background: #238636; opacity: 0.3; }
    .b-occ { background: #DA3633; box-shadow: 0 0 3px #DA3633; }
    .b-delay { background: #D29922; box-shadow: 0 0 3px #D29922; } /* New: Delayed Discharge */

    /* Custom Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    [data-testid="stMetricValue"] { color: #E6EDF3 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Logic & Data Model
# ---------------------------------------------------------

DEPARTMENTS = {
    "ICU": {"cap": 16, "gen": "Mixed", "type": "Critical"},
    "Surgical Male": {"cap": 40, "gen": "Male", "type": "Acute"},
    "Surgical Female": {"cap": 40, "gen": "Female", "type": "Acute"},
    "Medical Male": {"cap": 50, "gen": "Male", "type": "General"},
    "Medical Female": {"cap": 50, "gen": "Female", "type": "General"},
    "Pediatric": {"cap": 30, "gen": "Mixed", "type": "General"},
    "Obstetrics": {"cap": 24, "gen": "Female", "type": "Acute"},
}

PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(1000)}

def init_system():
    if 'version' not in st.session_state or st.session_state.version != '5.0':
        # Create Data Structure
        st.session_state.df = pd.DataFrame(columns=[
            "PIN", "Gender", "Department", "Bed", "Admit_Date", 
            "Exp_Discharge", "Actual_Discharge", "Source"
        ])
        
        # Populate with Realistic Scenarios (Bottlenecks & Delays)
        new_data = []
        for dept, info in DEPARTMENTS.items():
            # Random occupancy level (ICU tends to be fuller)
            occupancy_factor = 0.9 if info['type'] == 'Critical' else np.random.uniform(0.6, 0.85)
            count = int(info['cap'] * occupancy_factor)
            
            for i in range(count):
                bed_n = i + 1
                adm = datetime.now() - timedelta(days=np.random.randint(0, 10), hours=np.random.randint(1, 12))
                
                # Create some delayed discharges (Bed Blockers)
                is_delayed = np.random.random() < 0.15 # 15% are delayed
                if is_delayed:
                    exp = datetime.now() - timedelta(hours=np.random.randint(2, 24)) # Should have left already
                else:
                    exp = adm + timedelta(days=np.random.randint(2, 8))
                
                new_data.append({
                    "PIN": f"PIN-{np.random.randint(2000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": f"{dept[:3].upper()}-{bed_n:03d}",
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": None, 
                    "Source": np.random.choice(["Emergency", "Transfer", "Elective"], p=[0.7, 0.1, 0.2])
                })
        
        st.session_state.df = pd.DataFrame(new_data)
        st.session_state.version = '5.0'

init_system()
df = st.session_state.df

# ---------------------------------------------------------
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("## OccupyBed AI")
        st.caption("Enterprise Edition v5.0")
        
    st.markdown("---")
    menu = st.radio("MODULES", ["Command Center", "Admissions", "Analytics", "Settings"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:12px; color:#8B949E;">
    LAST UPDATE<br>
    <b style="color:#E6EDF3">{datetime.now().strftime('%H:%M:%S')}</b>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. Command Center (The Main Dashboard)
# ---------------------------------------------------------
if menu == "Command Center":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: fc = st.selectbox("Forecast Horizon", [6, 12, 24, 48], index=1, format_func=lambda x: f"{x} Hours")

    # --- Calculations ---
    now = datetime.now()
    active = df[df['Actual_Discharge'].isnull()]
    
    # 1. Net Flow (Last 24h)
    last_24h = now - timedelta(hours=24)
    adm_24h = len(df[(df['Admit_Date'] >= last_24h)])
    # For simulation, assume some discharges happened
    dis_24h = int(adm_24h * 0.9) # Mock logic for MVP flow
    net_flow = adm_24h - dis_24h
    
    # 2. Delayed Discharges (Bed Blockers)
    delayed = active[active['Exp_Discharge'] < now]
    delayed_count = len(delayed)
    
    # 3. General Stats
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    curr_occ = len(active)
    occ_rate = (curr_occ / total_cap) * 100
    
    # --- AI AI General Board (The Brain) ---
    st.markdown("---")
    
    # AI Logic Generation
    ai_status = "STABLE"
    ai_color = "#238636"
    ai_rec = "Standard operating procedures in effect."
    ai_risk = "None detected."
    
    if occ_rate > 90:
        ai_status = "CRITICAL"
        ai_color = "#DA3633"
        ai_rec = "ACTIVATE SURGE PROTOCOL. Cancel elective surgeries. Expedite discharges in Medical Wards."
        ai_risk = "ED Overcrowding imminent."
    elif occ_rate > 80:
        ai_status = "HIGH LOAD"
        ai_color = "#D29922"
        ai_rec = "Prioritize morning discharges. Review ICU transfer list."
        ai_risk = "Surgical beds at capacity."
    elif delayed_count > 10:
        ai_status = "BOTTLENECK"
        ai_color = "#D29922"
        ai_rec = f"Focus on discharging {delayed_count} delayed patients to clear capacity."
        
    st.markdown(f"""
    <div class="ai-board" style="border-left-color: {ai_color};">
        <div class="ai-title">
            <span>🤖 AI SITUATION REPORT</span>
            <span style="background:{ai_color}; color:white; padding:2px 8px; border-radius:4px; font-size:12px;">{ai_status}</span>
        </div>
        <div class="ai-msg"><strong>Recommendation:</strong> {ai_rec}</div>
        <div class="ai-msg"><strong>Impending Risk:</strong> {ai_risk}</div>
        <div style="margin-top:10px; display:flex; gap:10px;">
            <span class="ai-tag">Delay Count: {delayed_count}</span>
            <span class="ai-tag">Forecast Free ({fc}h): {active[active['Exp_Discharge'] <= (now + timedelta(hours=fc))].shape[0]} Beds</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Hospital Level KPIs ---
    k1, k2, k3, k4, k5 = st.columns(5)
    
    def kpi_card(label, value, delta, color="#E6EDF3"):
        return f"""
        <div class="kpi-container">
            <div class="kpi-label">{label}</div>
            <div class="kpi-val" style="color:{color}">{value}</div>
            <div class="kpi-delta">{delta}</div>
        </div>
        """
    
    flow_color = "#DA3633" if net_flow > 0 else "#238636"
    
    k1.markdown(kpi_card("Occupancy Rate", f"{occ_rate:.1f}%", f"{curr_occ}/{total_cap} Beds", "#58A6FF"), unsafe_allow_html=True)
    k2.markdown(kpi_card("Net Flow (24h)", f"{net_flow:+d}", "Adm vs Disc", flow_color), unsafe_allow_html=True)
    k3.markdown(kpi_card("Delayed Discharges", delayed_count, "Bed Blockers", "#D29922"), unsafe_allow_html=True)
    k4.markdown(kpi_card(f"Forecast ({fc}h)", active[active['Exp_Discharge'] <= (now + timedelta(hours=fc))].shape[0], "Expected Free", "#A371F7"), unsafe_allow_html=True)
    k5.markdown(kpi_card("Turnover Rate", "1.2", "Pat/Bed/Day", "#238636"), unsafe_allow_html=True)

    # --- Department Matrix (Visual + Indicators) ---
    st.markdown("### 🏥 Wards Live Status")
    
    # Legend
    st.markdown("""
    <div style="display:flex; gap:15px; font-size:11px; color:#8B949E; margin-bottom:10px;">
        <span><span style="display:inline-block;width:10px;height:10px;background:#DA3633;margin-right:5px;"></span>Occupied</span>
        <span><span style="display:inline-block;width:10px;height:10px;background:#D29922;margin-right:5px;"></span>Delayed/Overdue</span>
        <span><span style="display:inline-block;width:10px;height:10px;background:#238636;opacity:0.3;margin-right:5px;"></span>Available</span>
    </div>
    """, unsafe_allow_html=True)
    
    d_cols = st.columns(3)
    d_keys = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(d_keys):
        info = DEPARTMENTS[dept]
        d_pats = active[active['Department'] == dept]
        d_count = len(d_pats)
        d_pct = (d_count / info['cap']) * 100
        
        # Calculate Delays in this dept
        d_delays = d_pats[d_pats['Exp_Discharge'] < now].shape[0]
        
        # Color Logic
        border_col = "#238636"
        status_txt = "SAFE"
        if d_pct > 85: border_col, status_txt = "#D29922", "WARNING"
        if d_pct > 95: border_col, status_txt = "#DA3633", "CRITICAL"
        
        # Bed Grid Generation
        grid_html = '<div class="bed-grid">'
        # 1. Delayed (Yellow/Orange)
        for _ in range(d_delays): grid_html += '<div class="bed-box b-delay" title="Delayed Discharge"></div>'
        # 2. Normal Occupied (Red)
        for _ in range(d_count - d_delays): grid_html += '<div class="bed-box b-occ" title="Occupied"></div>'
        # 3. Free (Green)
        for _ in range(info['cap'] - d_count): grid_html += '<div class="bed-box b-free" title="Available"></div>'
        grid_html += '</div>'
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card-pro" style="border-left: 4px solid {border_col};">
                <div class="dept-top">
                    <span class="dept-name">{dept}</span>
                    <span style="color:{border_col}; font-weight:bold; font-size:11px;">{status_txt}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px; color:#8B949E;">
                    <span>Occ: <b style="color:white">{d_count}</b>/{info['cap']}</span>
                    <span>Gender: {info['gen']}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px; color:#D29922; margin-top:2px;">
                    <span>Late Stay: <b>{d_delays}</b></span>
                </div>
                {grid_html}
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Admissions Module
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Admissions Center")
    
    # Import/Export
    with st.expander("Data Controls"):
        c1, c2 = st.columns(2)
        c1.download_button("Export CSV", df.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv")
        up = c2.file_uploader("Import CSV", type=['csv'])
        if up:
            try:
                new_df = pd.read_csv(up)
                for c in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']: new_df[c] = pd.to_datetime(new_df[c])
                st.session_state.df = new_df
                st.rerun()
            except: st.error("Import Error")

    st.markdown("---")
    st.subheader("New Patient Entry")
    
    c1, c2 = st.columns(2)
    with c1:
        pin = st.selectbox("PIN", ["Select..."] + list(PATIENT_DB.keys()))
        gen = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
        if pin != "Select...": st.info(f"Gender: {gen}")
        
        dept = st.selectbox("Ward", ["Select..."] + list(DEPARTMENTS.keys()))
        
        # Strict Bed Filter
        bed_opts = ["Select Ward"]
        if dept != "Select...":
            occ_beds = df[(df['Department']==dept) & (df['Actual_Discharge'].isnull())]['Bed'].tolist()
            all_beds = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
            free = [b for b in all_beds if b not in occ_beds]
            bed_opts = free if free else ["Full"]
        
        bed = st.selectbox("Bed", bed_opts)

    with c2:
        now = datetime.now()
        adm_d = st.date_input("Admit Date", now)
        adm_t = st.time_input("Time", now.time())
        
        st.markdown("**Discharge Plan**")
        ex_d = st.date_input("Target Date", now + timedelta(days=3))
        ex_t = st.time_input("Target Time", now.time())
        src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

    if st.button("Admit Patient", type="primary", use_container_width=True):
        if pin != "Select..." and dept != "Select..." and bed not in ["Select Ward", "Full"]:
            # Check Gender
            rule = DEPARTMENTS[dept]['gen']
            if rule != "Mixed" and rule != gen:
                st.error(f"Gender Mismatch: {dept} is {rule} only.")
            else:
                new = {
                    "PIN": pin, "Gender": gen, "Department": dept, "Bed": bed,
                    "Admit_Date": datetime.combine(adm_d, adm_t),
                    "Exp_Discharge": datetime.combine(ex_d, ex_t),
                    "Actual_Discharge": None, "Source": src
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new])], ignore_index=True)
                st.success("Admitted.")
                time.sleep(0.5)
                st.rerun()
        else:
            st.warning("Invalid Data")

    # Active Table
    st.markdown("### Active Inpatients")
    active_df = df[df['Actual_Discharge'].isnull()]
    
    if not active_df.empty:
        # Quick Discharge
        sel = st.selectbox("Quick Discharge", ["Select..."] + active_df['PIN'].tolist())
        if sel != "Select...":
            if st.button(f"Discharge {sel}"):
                idx = df[(df['PIN']==sel) & (df['Actual_Discharge'].isnull())].index
                st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.now()
                st.success("Discharged")
                st.rerun()
        
        st.dataframe(active_df[['PIN', 'Department', 'Bed', 'Admit_Date', 'Exp_Discharge']], use_container_width=True)

# ---------------------------------------------------------
# 6. Analytics (Operational KPIs)
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Operational KPIs")
    
    calc = df.copy()
    now = datetime.now()
    
    # Metrics
    total_adm = len(calc)
    total_dis = len(calc[calc['Actual_Discharge'].notnull()])
    
    # Bed Turnover Rate (Discharges / Total Beds)
    tot_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    turnover = (total_dis / tot_cap) if tot_cap > 0 else 0
    
    # Ready for Discharge (Exp date passed)
    active = calc[calc['Actual_Discharge'].isnull()]
    ready = active[active['Exp_Discharge'] < now].shape[0]
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Admission Rate", f"{total_adm}", "Total")
    k2.metric("Discharge Rate", f"{total_dis}", "Total")
    k3.metric("Bed Turnover", f"{turnover:.2f}", "Rounds/Bed")
    k4.metric("Overdue Patients", f"{ready}", "Delayed", delta_color="inverse")
    
    st.markdown("---")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("##### Admissions Flow")
        daily = calc.groupby(calc['Admit_Date'].dt.date).size().reset_index(name='Count')
        fig = px.area(daily, x='Admit_Date', y='Count', line_shape='spline')
        fig.update_layout(paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font={'color':'#C9D1D9'})
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.markdown("##### Efficiency Matrix")
        eff = calc.groupby('Department').size().reset_index(name='Volume')
        eff['Cap'] = eff['Department'].apply(lambda x: DEPARTMENTS[x]['cap'])
        eff['Util%'] = (eff['Volume']/eff['Cap']*100).astype(int) # Mock metric
        st.dataframe(eff.sort_values('Volume', ascending=False), hide_index=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    if st.button("FACTORY RESET SYSTEM", type="primary"):
        del st.session_state.df
        del st.session_state.version
        st.rerun()
