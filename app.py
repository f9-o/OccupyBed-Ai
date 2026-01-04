import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. System Config & Ultimate Design
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Enterprise", layout="wide", page_icon="🏥")

# CSS: High-End Corporate Dark Mode + Glowing Icon Animation
st.markdown("""
<style>
    /* Global Reset */
    .stApp { background-color: #050505; color: #E0E0E0; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0A0A0A; border-right: 1px solid #1F1F1F; }
    
    /* --- THE GLOWING ICON (TOP LEFT) --- */
    @keyframes glow {
        from { text-shadow: 0 0 5px #fff, 0 0 10px #238636, 0 0 15px #238636; transform: scale(1); }
        to { text-shadow: 0 0 10px #fff, 0 0 20px #238636, 0 0 30px #238636; transform: scale(1.1); }
    }
    .fixed-icon {
        position: fixed;
        top: 15px;
        left: 20px;
        font-size: 35px;
        z-index: 99999;
        animation: glow 1.5s ease-in-out infinite alternate;
        cursor: default;
    }

    /* AI Command Terminal */
    .ai-board {
        background: #111; border: 1px solid #333; border-left: 5px solid #A371F7;
        border-radius: 6px; padding: 15px; margin-bottom: 20px;
    }
    .ai-title { font-size: 15px; font-weight: 700; color: #A371F7; margin-bottom: 10px; text-transform: uppercase; }
    .ai-msg { font-size: 13px; color: #D1D5DB; margin-bottom: 5px; border-bottom: 1px solid #222; padding-bottom: 5px; }
    .ai-dept { color: #58A6FF; font-weight: 700; }

    /* Department Cards & Visual Matrix */
    .dept-card {
        background-color: #0D0D0D; border: 1px solid #222; border-radius: 8px;
        padding: 15px; margin-bottom: 12px; transition: all 0.3s;
    }
    .dept-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .dept-name { font-size: 14px; font-weight: 700; color: #FFF; }
    
    /* Status Badges */
    .badge { padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; text-transform: uppercase; }
    .badge-green { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #059669; }
    .badge-yellow { background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #B45309; }
    .badge-red { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #B91C1C; }

    /* Visual Bed Grid */
    .bed-grid { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #222; }
    .bed-unit { width: 10px; height: 10px; border-radius: 2px; }
    .b-occ { background-color: #EF4444; box-shadow: 0 0 3px rgba(239, 68, 68, 0.5); } /* Red */
    .b-free { background-color: #1F2937; } /* Gray */
    .b-ready { background-color: #10B981; box-shadow: 0 0 3px rgba(16, 185, 129, 0.5); } /* Green (Ready) */

    /* Stats Grid inside Card */
    .stat-row { display: flex; justify-content: space-between; font-size: 11px; color: #9CA3AF; margin-bottom: 2px; }
    .stat-val { color: #E5E7EB; font-weight: 600; }
    .stat-ready { color: #A371F7; font-weight: 700; }

    /* KPI Top Cards */
    .kpi-box { background: #111; border: 1px solid #333; border-radius: 6px; padding: 15px; text-align: center; }
    .kpi-lbl { font-size: 10px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-num { font-size: 24px; font-weight: 700; color: #FFF; margin: 4px 0; }
    .kpi-sub { font-size: 11px; color: #3B82F6; }

    /* Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0A0A0A !important; border-color: #333 !important; color: white !important; }
    button[kind="primary"] { background: linear-gradient(90deg, #2563EB, #1D4ED8) !important; border: none !important; color: white !important; }
</style>

<div class="fixed-icon">🏥</div>
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
        st.session_state.df = pd.DataFrame(columns=["PIN", "Gender", "Department", "Bed", "Admit_Date", "Exp_Discharge", "Actual_Discharge", "Source"])
        st.session_state.waitlist = [] 
        
        # Populate
        data = []
        for dept, info in DEPARTMENTS.items():
            count = int(info['cap'] * np.random.uniform(0.6, 0.85))
            for i in range(count):
                # Simulated dates
                adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 12))
                
                # Logic: Is patient ready for discharge soon?
                if np.random.random() < 0.25:
                    exp = datetime.now() + timedelta(hours=np.random.randint(1, 24))
                else:
                    exp = adm + timedelta(days=np.random.randint(2, 8))
                
                data.append({
                    "PIN": f"PIN-{np.random.randint(2000, 9999)}",
                    "Gender": "Female" if "Female" in dept else ("Male" if "Male" in dept else np.random.choice(["Male", "Female"])),
                    "Department": dept,
                    "Bed": f"{dept[:3].upper()}-{i+1:03d}",
                    "Admit_Date": adm,
                    "Exp_Discharge": exp,
                    "Actual_Discharge": None,
                    "Source": np.random.choice(["Emergency", "Elective", "Transfer"])
                })
        st.session_state.df = pd.DataFrame(data)

init_system()
df = st.session_state.df

# Type Safety
for col in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------------------------------------------------------
# 3. Sidebar (Search & Navigation)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True) # Space for the fixed icon
    st.markdown("## OccupyBed AI")
    
    st.markdown("### 🔍 Global Search")
    search = st.text_input("Find Patient (PIN)", placeholder="e.g. PIN-2045")
    if search:
        found = df[df['PIN'] == search]
        if not found.empty:
            r = found.iloc[0]
            st.success(f"Loc: {r['Department']}")
            st.caption(f"Bed: {r['Bed']}")
        else:
            st.error("Not Found")

    st.markdown("---")
    menu = st.radio("SYSTEM", ["Dashboard", "Admissions & Flow", "Analytics", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Ver: 10.0 Enterprise")

# ---------------------------------------------------------
# 4. DASHBOARD (The Hub)
# ---------------------------------------------------------
if menu == "Dashboard":
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Hospital Command Center")
    with c2: fc = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=1, format_func=lambda x: f"{x} Hours")

    # --- Calculations ---
    now = datetime.now()
    active = df[df['Actual_Discharge'].isnull()]
    future_limit = now + timedelta(hours=fc)
    
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    occ = len(active)
    avail = total_cap - occ
    
    # Ready to discharge (Active patients whose exp date is <= future limit)
    ready_count = active[active['Exp_Discharge'] <= future_limit].shape[0]
    
    # Net Flow
    last_24 = now - timedelta(hours=24)
    inflow = len(df[df['Admit_Date'] >= last_24])
    outflow = len(df[df['Actual_Discharge'] >= last_24])
    net = inflow - outflow

    # --- 1. AI Action Board (Text Logic) ---
    st.markdown(f"""<div class="ai-board"><div class="ai-title">🤖 AI Operational Recommendations</div>""", unsafe_allow_html=True)
    
    msg_count = 0
    for dept, info in DEPARTMENTS.items():
        d_df = active[active['Department'] == dept]
        d_occ = len(d_df)
        pct = (d_occ / info['cap']) * 100
        d_delayed = d_df[d_df['Exp_Discharge'] < now].shape[0]
        
        if pct >= 85:
            st.markdown(f"""<div class="ai-msg"><span class="ai-dept">{dept}:</span> High occupancy detected ({int(pct)}%). Recommendation: Divert new admissions to {info['overflow']}.</div>""", unsafe_allow_html=True)
            msg_count += 1
        elif d_delayed > 4:
            st.markdown(f"""<div class="ai-msg"><span class="ai-dept">{dept}:</span> High delayed discharge rate detected ({d_delayed} patients). Review pending approvals.</div>""", unsafe_allow_html=True)
            msg_count += 1
        elif pct < 70:
            st.markdown(f"""<div class="ai-msg"><span class="ai-dept">{dept}:</span> Available capacity detected. Elective admissions can proceed safely.</div>""", unsafe_allow_html=True)
            msg_count += 1
            
    if msg_count == 0: st.markdown("""<div class="ai-msg"><span style="color:#10B981">System Status:</span> Operations are stable across all wards.</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. KPI Cards ---
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"""<div class="kpi-box"><div class="kpi-lbl">Occupancy</div><div class="kpi-num" style="color:#60A5FA">{int(occ/total_cap*100)}%</div><div class="kpi-sub">{occ}/{total_cap} Beds</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="kpi-box"><div class="kpi-lbl">Net Flow (24h)</div><div class="kpi-num" style="color:{'#EF4444' if net>0 else '#10B981'}">{net:+d}</div><div class="kpi-sub">In: {inflow} | Out: {outflow}</div></div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="kpi-box"><div class="kpi-lbl">Ready ({fc}h)</div><div class="kpi-num" style="color:#A371F7">{ready_count}</div><div class="kpi-sub">Forecast Free</div></div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="kpi-box"><div class="kpi-lbl">Waitlist</div><div class="kpi-num" style="color:#F59E0B">{len(st.session_state.waitlist)}</div><div class="kpi-sub">Pending</div></div>""", unsafe_allow_html=True)

    # --- 3. File Operations (On Dashboard as requested) ---
    with st.expander("📂 Data Management (Upload / Download)", expanded=False):
        c_up, c_down = st.columns(2)
        with c_up:
            st.download_button("Download Report (CSV)", df.to_csv(index=False).encode('utf-8'), "hospital_data.csv", "text/csv")
        with c_down:
            up_file = st.file_uploader("Upload Data (CSV)", type=['csv'])
            if up_file:
                try:
                    new_df = pd.read_csv(up_file)
                    for c in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']: new_df[c] = pd.to_datetime(new_df[c], errors='coerce')
                    st.session_state.df = new_df
                    st.success("Loaded!")
                    st.rerun()
                except: st.error("Invalid File")

    st.markdown("---")

    # --- 4. Detailed Department Matrix (Visual + Stats) ---
    st.markdown("### 🏥 Department Live Matrix")
    d_cols = st.columns(3)
    d_keys = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(d_keys):
        info = DEPARTMENTS[dept]
        d_df = active[active['Department'] == dept]
        
        # Numbers
        total = info['cap']
        occupied = len(d_df)
        available = total - occupied
        ready_now = d_df[d_df['Exp_Discharge'] <= future_limit].shape[0]
        pct = (occupied / total) * 100
        
        # Color Logic (70% - 85%)
        if pct < 70:
            status = "SAFE"
            badge = "badge-green"
            b_col = "#10B981"
        elif 70 <= pct <= 84:
            status = "WARNING"
            badge = "badge-yellow"
            b_col = "#F59E0B"
        else:
            status = "CRITICAL"
            badge = "badge-red"
            b_col = "#EF4444"
            
        # Grid Generation
        grid_html = '<div class="bed-grid">'
        # Red Boxes (Occupied)
        for _, row in d_df.iterrows():
            cls = "b-ready" if row['Exp_Discharge'] <= future_limit else "b-occ"
            grid_html += f'<div class="bed-unit {cls}" title="PIN: {row["PIN"]}"></div>'
        # Free Boxes
        for _ in range(available):
            grid_html += '<div class="bed-unit b-free" title="Available"></div>'
        grid_html += '</div>'
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card">
                <div class="dept-header">
                    <span class="dept-name">{dept}</span>
                    <span class="badge {badge}">{status}</span>
                </div>
                <div class="stat-row"><span>Total Beds:</span><span class="stat-val">{total}</span></div>
                <div class="stat-row"><span>Occupied:</span><span class="stat-val">{occupied}</span></div>
                <div class="stat-row"><span>Available:</span><span class="stat-val">{available}</span></div>
                <div class="stat-row"><span>Ready ({fc}h):</span><span class="stat-ready">{ready_now}</span></div>
                
                <div style="background:#222; height:4px; border-radius:2px; margin-top:5px;">
                    <div style="width:{min(pct, 100)}%; background:{b_col}; height:100%;"></div>
                </div>
                {grid_html}
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Admissions & Flow
# ---------------------------------------------------------
elif menu == "Admissions & Flow":
    st.title("Patient Flow Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ New Admission", "⏳ Waitlist", "📤 Discharge"])
    
    # TAB 1: ADMIT
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            pin = st.selectbox("Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
            gender = PATIENT_DB.get(pin, "Unknown") if pin != "Select..." else "Unknown"
            if pin != "Select...": st.info(f"Gender Detected: **{gender}**")
            
            # Dept Filter by Gender
            allowed_depts = [d for d, i in DEPARTMENTS.items() if i['gen'] == "Mixed" or i['gen'] == gender]
            dept = st.selectbox("Department", ["Select..."] + allowed_depts)
            
            # Bed Filter (Empty Only)
            bed_opts = ["Select Dept"]
            if dept != "Select...":
                occ_list = df[(df['Department'] == dept) & (df['Actual_Discharge'].isnull())]['Bed'].tolist()
                all_list = [f"{dept[:3].upper()}-{i+1:03d}" for i in range(DEPARTMENTS[dept]['cap'])]
                free_list = [b for b in all_list if b not in occ_list]
                bed_opts = free_list if free_list else ["FULL - Add to Waitlist"]
            bed = st.selectbox("Bed", bed_opts)

        with c2:
            d_admit = st.date_input("Admit Date", datetime.now())
            t_admit = st.time_input("Admit Time", datetime.now().time())
            st.markdown("---")
            d_exp = st.date_input("Expected Discharge Date", datetime.now() + timedelta(days=3))
            t_exp = st.time_input("Expected Time", datetime.now().time())
            src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])

        if st.button("Confirm Admission", type="primary", use_container_width=True):
            if bed == "FULL - Add to Waitlist":
                st.session_state.waitlist.append({"PIN": pin, "Dept": dept, "Source": src})
                st.warning("Added to Waitlist.")
            elif pin != "Select..." and dept != "Select...":
                new_row = {
                    "PIN": pin, "Gender": gender, "Department": dept, "Bed": bed,
                    "Admit_Date": datetime.combine(d_admit, t_admit),
                    "Exp_Discharge": datetime.combine(d_exp, t_exp),
                    "Actual_Discharge": None, "Source": src
                }
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Admitted.")
                time.sleep(0.5)
                st.rerun()

    # TAB 2: WAITLIST
    with tab2:
        if st.session_state.waitlist:
            st.dataframe(pd.DataFrame(st.session_state.waitlist), use_container_width=True)
            if st.button("Clear List"):
                st.session_state.waitlist = []
                st.rerun()
        else: st.info("No patients waiting.")

    # TAB 3: DISCHARGE
    with tab3:
        active = df[df['Actual_Discharge'].isnull()]
        target = st.selectbox("Select Patient to Discharge", ["Select..."] + active['PIN'].tolist())
        
        if target != "Select...":
            row = active[active['PIN'] == target].iloc[0]
            st.warning(f"Processing Discharge: **{row['PIN']}** from **{row['Department']}** ({row['Bed']})")
            
            dc1, dc2 = st.columns(2)
            act_d = dc1.date_input("Actual Discharge Date", datetime.now())
            act_t = dc2.time_input("Actual Discharge Time", datetime.now().time())
            
            if st.button("Finalize Discharge"):
                idx = df[(df['PIN'] == target) & (df['Actual_Discharge'].isnull())].index
                st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(act_d, act_t)
                st.success("Patient Discharged.")
                st.rerun()

# ---------------------------------------------------------
# 6. Operational KPIs
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Operational KPIs")
    
    calc = df.copy()
    
    # 1. Admission Rate
    range_days = (calc['Admit_Date'].max() - calc['Admit_Date'].min()).days
    range_days = 1 if range_days < 1 else range_days
    adm_rate = len(calc) / range_days
    
    # 2. Discharge Rate
    discharges = calc[calc['Actual_Discharge'].notnull()]
    disc_rate = len(discharges) / range_days
    
    # 3. Turnover
    tot_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    turnover = len(discharges) / tot_cap
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Admission Rate", f"{adm_rate:.1f}", "Pat/Day")
    k2.metric("Discharge Rate", f"{disc_rate:.1f}", "Pat/Day")
    k3.metric("Bed Turnover", f"{turnover:.2f}", "Rounds/Bed")
    k4.metric("Avg LOS", f"{(calc['Exp_Discharge'] - calc['Admit_Date']).dt.days.mean():.1f}", "Days")
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Net Flow Analysis")
        daily_adm = calc.groupby(calc['Admit_Date'].dt.date).size().reset_index(name='In')
        daily_dis = discharges.groupby(discharges['Actual_Discharge'].dt.date).size().reset_index(name='Out')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=daily_adm['Admit_Date'], y=daily_adm['In'], name='Admissions', marker_color='#60A5FA'))
        if not daily_dis.empty:
            fig.add_trace(go.Bar(x=daily_dis['Actual_Discharge'], y=daily_dis['Out'], name='Discharges', marker_color='#34D399'))
        fig.update_layout(paper_bgcolor="#0A0A0A", plot_bgcolor="#0A0A0A", font={'color':"#AAA"})
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.markdown("##### Occupancy Heatmap")
        active_counts = df[df['Actual_Discharge'].isnull()]['Department'].value_counts().reset_index()
        active_counts.columns = ['Dept', 'Count']
        if not active_counts.empty:
            fig2 = px.bar(active_counts, y='Dept', x='Count', orientation='h', color='Count', color_continuous_scale='Bluered')
            fig2.update_layout(paper_bgcolor="#0A0A0A", plot_bgcolor="#0A0A0A", font={'color':"#AAA"})
            st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. Settings
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("Settings")
    if st.button("FACTORY RESET (Clear Data)", type="primary"):
        del st.session_state.df
        del st.session_state.waitlist
        st.rerun()
