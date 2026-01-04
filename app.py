import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ---------------------------------------------------------
# 1️⃣ إعدادات الصفحة والتصميم (Page Config & Styling)
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI", layout="wide", page_icon="🏥")

# CSS لتخصيص الواجهة وتحسين الألوان (Traffic Light System)
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .stMetric {
        text-align: center;
    }
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    /* مؤشرات الحالة */
    .status-green { color: #28a745; font-weight: bold; }
    .status-yellow { color: #ffc107; font-weight: bold; }
    .status-red { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2️⃣ الثوابت وقاعدة البيانات (Constants & Mock DB)
# ---------------------------------------------------------

# قاعدة بيانات المرضى الداخلية (PIN -> Gender) - لمحاكاة الربط
PATIENT_DB = {
    "PIN-1001": "Male", "PIN-1002": "Female", "PIN-1003": "Male",
    "PIN-1004": "Female", "PIN-1005": "Male", "PIN-1006": "Male",
    "PIN-1007": "Female", "PIN-1008": "Male", "PIN-1009": "Female",
    "PIN-1010": "Male", "PIN-1011": "Female", "PIN-1012": "Male"
}

# هيكل الأقسام والسعة الاستيعابية والجنس المسموح
DEPARTMENTS = {
    "Medical - Male": {"capacity": 50, "gender": "Male"},
    "Medical - Female": {"capacity": 50, "gender": "Female"},
    "Surgical - Male": {"capacity": 40, "gender": "Male"},
    "Surgical - Female": {"capacity": 40, "gender": "Female"},
    "ICU": {"capacity": 20, "gender": "Mixed"},
    "Pediatric": {"capacity": 30, "gender": "Mixed"},
    "Obstetrics & Gynecology": {"capacity": 20, "gender": "Female"},
}

# ---------------------------------------------------------
# 3️⃣ دوال مساعدة (Helper Functions)
# ---------------------------------------------------------

def get_bed_list(dept_name):
    """توليد قائمة أرقام الأسرة للقسم"""
    cap = DEPARTMENTS[dept_name]["capacity"]
    prefix = "".join([w[0] for w in dept_name.split()]) # e.g., Medical Male -> MM
    return [f"{prefix}-{i+1:03d}" for i in range(cap)]

def get_status_color(occupancy_rate):
    """تحديد لون الحالة بناء على نسبة الإشغال"""
    if occupancy_rate < 70:
        return "🟢 Safe", "#28a745" # الأخضر
    elif 70 <= occupancy_rate <= 84:
        return "🟡 Warning", "#ffc107" # الأصفر
    else:
        return "🔴 Critical", "#dc3545" # الأحمر

# ---------------------------------------------------------
# 4️⃣ مولد البيانات الذكي (AI/Pandas Synthetic Data Generator)
# ---------------------------------------------------------
def generate_synthetic_data(num_records=60):
    """
    تقوم هذه الدالة باستخدام Pandas و NumPy لمحاكاة بيانات مستشفى واقعية.
    تستخدم لتعبئة النظام عند البدء أو عند طلب المستخدم.
    """
    depts = list(DEPARTMENTS.keys())
    sources = ["Emergency", "Elective", "Transfer"]
    
    # اختيار عشوائي للأقسام والمصادر بأوزان منطقية
    random_depts = np.random.choice(depts, num_records)
    random_sources = np.random.choice(sources, num_records, p=[0.5, 0.4, 0.1])
    
    data_list = []
    generated_beds = set() # لضمان عدم تكرار السرير لنفس الوقت في المحاكاة

    for i in range(num_records):
        dept = random_depts[i]
        cap = DEPARTMENTS[dept]['capacity']
        
        # محاولة إيجاد سرير فارغ عشوائي
        prefix = "".join([w[0] for w in dept.split()])
        bed_num = f"{prefix}-{np.random.randint(1, cap+1):03d}"
        
        # منع التكرار البسيط في التوليد العشوائي
        if f"{dept}-{bed_num}" in generated_beds:
            continue
        generated_beds.add(f"{dept}-{bed_num}")

        # تواريخ ذكية: دخول خلال الأسبوع الماضي
        days_back = np.random.randint(0, 10)
        adm_date = datetime.now() - timedelta(days=days_back, hours=np.random.randint(1, 23))
        
        # مدة الإقامة المتوقعة
        stay_duration = np.random.randint(2, 14)
        exp_date = adm_date + timedelta(days=stay_duration)
        
        # حالة الخروج: 80% لا يزالون منومين (None)، 20% خرجوا (تاريخ)
        act_date = None
        if np.random.random() < 0.2: 
            # خرج مبكراً أو متأخراً قليلاً
            act_date = exp_date + timedelta(hours=np.random.randint(-24, 48))
        
        data_list.append({
            "PIN": f"PIN-{1000+i}", # PIN افتراضي
            "Department": dept,
            "Bed_Number": bed_num,
            "Admission_Date": adm_date,
            "Admission_Source": random_sources[i],
            "Expected_Discharge": exp_date,
            "Actual_Discharge": act_date
        })
    
    return pd.DataFrame(data_list)

# ---------------------------------------------------------
# 5️⃣ إدارة حالة التطبيق (State Management)
# ---------------------------------------------------------

if 'df' not in st.session_state:
    # عند تشغيل التطبيق لأول مرة، قم بتوليد بيانات محاكاة
    st.session_state.df = generate_synthetic_data(num_records=80)

df = st.session_state.df

# ---------------------------------------------------------
# 6️⃣ القائمة الجانبية (Sidebar)
# ---------------------------------------------------------

with st.sidebar:
    st.title("🏥 OccupyBed AI")
    st.caption("Intelligent Bed Management System")
    
    menu = st.radio("Navigation", 
        ["Overview & AI Actions", "Live Admissions", "KPIs & Analytics", "Data Management"])
    
    st.markdown("---")
    st.info("**Current User:** \nAdmin / Bed Manager")
    st.caption("v1.0 MVP Build")

# ---------------------------------------------------------
# 7️⃣ الصفحة الرئيسية: Overview & AI Actions
# ---------------------------------------------------------
if menu == "Overview & AI Actions":
    st.header("📊 Real-time Overview & AI Insights")

    # --- Forecast Control ---
    col_fc, col_dummy = st.columns([2, 2])
    with col_fc:
        forecast_hours = st.select_slider(
            "🔮 Forecast Window (توقع توفر الأسرة خلال)",
            options=[6, 12, 24, 48, 72],
            value=24
        )

    # --- Calculations ---
    # المرضى المنومين حالياً (الذين لم يخرجوا)
    active_patients = df[df['Actual_Discharge'].isnull()]
    
    total_beds_hospital = sum(d['capacity'] for d in DEPARTMENTS.values())
    occupied_beds_hospital = len(active_patients)
    available_beds_hospital = total_beds_hospital - occupied_beds_hospital
    occupancy_pct = (occupied_beds_hospital / total_beds_hospital) * 100
    
    # حساب الجاهزين للخروج خلال نافذة التنبؤ
    now = datetime.now()
    future_time = now + timedelta(hours=forecast_hours)
    
    # جاهز للخروج: وقته المتوقع خلال الفترة المحددة
    ready_to_discharge = active_patients[
        (active_patients['Expected_Discharge'] <= future_time)
    ].shape[0]

    # --- Top Metrics ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Beds", total_beds_hospital)
    m2.metric("Occupied Beds", occupied_beds_hospital, f"{occupancy_pct:.1f}%")
    m3.metric("Available Now", available_beds_hospital)
    m4.metric(f"Expected Free ({forecast_hours}h)", ready_to_discharge, delta_color="off")

    st.markdown("---")

    # --- AI Section ---
    st.subheader("🤖 AI Suggested Actions")
    
    c_ai_text, c_ai_chart = st.columns([2, 1])
    
    with c_ai_text:
        suggestions = []
        for dept, info in DEPARTMENTS.items():
            dept_pats = active_patients[active_patients['Department'] == dept]
            occ = len(dept_pats)
            cap = info['capacity']
            ratio = (occ / cap) * 100
            
            # AI Logic Rules
            if ratio >= 85:
                suggestions.append(f"🔴 **{dept}** ({ratio:.0f}%): Critical occupancy! Accelerate discharge for stable patients.")
            elif ratio >= 70:
                suggestions.append(f"🟡 **{dept}** ({ratio:.0f}%): High load. Review elective admissions.")
            
            # Delayed Logic
            delayed = dept_pats[dept_pats['Expected_Discharge'] < now].shape[0]
            if delayed > 0:
                suggestions.append(f"⚠️ **{dept}**: {delayed} patients exceeding expected stay. Coordinate with physicians.")

        if not suggestions:
             st.success("✅ AI Analysis: Operations are stable. No critical bottlenecks detected.")
        else:
            for s in suggestions:
                st.write(s)

    with c_ai_chart:
        # Gauge Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = occupancy_pct,
            title = {'text': "Hospital Pressure"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "black"},
                'steps': [
                    {'range': [0, 70], 'color': "#28a745"},
                    {'range': [70, 85], 'color': "#ffc107"},
                    {'range': [85, 100], 'color': "#dc3545"}],
            }
        ))
        fig.update_layout(height=200, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    # --- Department Cards (Grid View) ---
    st.subheader("🏥 Department Live Status")
    dept_names = list(DEPARTMENTS.keys())
    
    # Loop to create grid
    for i in range(0, len(dept_names), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(dept_names):
                dept = dept_names[i+j]
                info = DEPARTMENTS[dept]
                
                # Dept Stats
                d_pats = active_patients[active_patients['Department'] == dept]
                d_occ = len(d_pats)
                d_cap = info['capacity']
                d_rate = (d_occ / d_cap) * 100
                d_avail = d_cap - d_occ
                d_ready = d_pats[d_pats['Expected_Discharge'] <= future_time].shape[0]
                
                status_txt, status_clr = get_status_color(d_rate)
                
                with cols[j]:
                    st.markdown(f"""
                    <div class="metric-card" style="border-top: 5px solid {status_clr};">
                        <h4 style="margin:0;">{dept}</h4>
                        <p style="color:gray; font-size:0.9em;">{info['gender']} Only</p>
                        <hr style="margin:5px 0;">
                        <div style="display:flex; justify-content:space-between;">
                            <span>Occupied: <b>{d_occ}/{d_cap}</b></span>
                            <span style="color:{status_clr}"><b>{status_txt}</b></span>
                        </div>
                        <div style="display:flex; justify-content:space-between;">
                            <span>Available: <b>{d_avail}</b></span>
                            <span>Exp. Free: <b>{d_ready}</b></span>
                        </div>
                        <div style="margin-top:8px; width:100%; background:#ddd; height:6px; border-radius:3px;">
                            <div style="width:{d_rate}%; background:{status_clr}; height:100%; border-radius:3px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 8️⃣ صفحة الإدخال: Live Admissions
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.header("📝 Patient Admission & Discharge")
    
    tab_in, tab_out = st.tabs(["📥 New Admission", "📤 Process Discharge"])
    
    # --- Admission Form ---
    with tab_in:
        with st.form("admit_form"):
            c1, c2 = st.columns(2)
            with c1:
                pin_list = list(PATIENT_DB.keys())
                sel_pin = st.selectbox("Select Patient PIN", ["Choose..."] + pin_list)
                
                # Auto-Detect Gender
                gender_val = "Unknown"
                if sel_pin != "Choose...":
                    gender_val = PATIENT_DB.get(sel_pin, "Unknown")
                    st.info(f"🧬 System Detected Gender: **{gender_val}**")
                
                adm_date = st.date_input("Admission Date", datetime.now())
                adm_time = st.time_input("Time", datetime.now().time())
                
            with c2:
                # Filter Departments by Gender
                valid_depts = []
                for d, info in DEPARTMENTS.items():
                    if info['gender'] == "Mixed" or info['gender'] == gender_val:
                        valid_depts.append(d)
                
                if sel_pin == "Choose...": valid_depts = list(DEPARTMENTS.keys())
                
                sel_dept = st.selectbox("Assign Department", ["Choose..."] + valid_depts)
                
                # Filter Beds (Show only available)
                avail_beds = []
                if sel_dept != "Choose...":
                    all_beds = get_bed_list(sel_dept)
                    busy_beds = df[(df['Department']==sel_dept) & (df['Actual_Discharge'].isnull())]['Bed_Number'].tolist()
                    avail_beds = [b for b in all_beds if b not in busy_beds]
                
                sel_bed = st.selectbox("Assign Bed", avail_beds if sel_dept != "Choose..." else [])
                
                src = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])
                exp_date = st.date_input("Expected Discharge", datetime.now() + timedelta(days=3))
            
            submit = st.form_submit_button("✅ Admit Patient")
            
            if submit:
                if sel_pin != "Choose..." and sel_dept != "Choose..." and sel_bed:
                    new_rec = {
                        "PIN": sel_pin, "Department": sel_dept, "Bed_Number": sel_bed,
                        "Admission_Date": datetime.combine(adm_date, adm_time),
                        "Admission_Source": src,
                        "Expected_Discharge": datetime.combine(exp_date, datetime.now().time()),
                        "Actual_Discharge": None
                    }
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_rec])], ignore_index=True)
                    st.success(f"Admitted {sel_pin} to {sel_dept} ({sel_bed})")
                else:
                    st.error("Please complete all fields.")

    # --- Discharge Form ---
    with tab_out:
        active = df[df['Actual_Discharge'].isnull()]
        if active.empty:
            st.warning("No active patients found.")
        else:
            pat_list = active['Bed_Number'] + " | " + active['PIN'] + " (" + active['Department'] + ")"
            sel_pat = st.selectbox("Select Patient to Discharge", pat_list)
            
            if sel_pat:
                bed_to_free = sel_pat.split(" | ")[0]
                
                cd1, cd2 = st.columns(2)
                with cd1: dis_date = st.date_input("Discharge Date", datetime.now())
                with cd2: dis_time = st.time_input("Discharge Time", datetime.now().time())
                
                if st.button("🚪 Confirm Discharge"):
                    # Update DataFrame
                    idx = df[(df['Bed_Number']==bed_to_free) & (df['Actual_Discharge'].isnull())].index
                    st.session_state.df.at[idx[0], 'Actual_Discharge'] = datetime.combine(dis_date, dis_time)
                    st.success("Patient discharged successfully. Bed is now free.")
                    st.rerun()

# ---------------------------------------------------------
# 9️⃣ صفحة المؤشرات: KPIs & Analytics
# ---------------------------------------------------------
elif menu == "KPIs & Analytics":
    st.header("📈 Operational Analytics")
    
    # A. Hospital KPIs
    st.subheader("🅰 Hospital Level")
    
    # Calculate Net Flow (Last 24h)
    yesterday = datetime.now() - timedelta(hours=24)
    admitted_24h = len(df[df['Admission_Date'] >= yesterday])
    discharged_24h = len(df[(df['Actual_Discharge'] >= yesterday) & (df['Actual_Discharge'].notnull())])
    net = admitted_24h - discharged_24h
    
    # Bed Turnover (Simulated simplistic formula)
    total_discharges = len(df[df['Actual_Discharge'].notnull()])
    turnover_rate = total_discharges / total_beds_hospital if total_beds_hospital > 0 else 0
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Admission Rate (24h)", admitted_24h)
    k2.metric("Discharge Rate (24h)", discharged_24h)
    k3.metric("Net Flow", f"{net:+}", delta_color="inverse")
    k4.metric("Bed Turnover", f"{turnover_rate:.2f}")
    
    st.markdown("---")
    
    # B. Department Drilldown
    st.subheader("🅱 Department Drill-down")
    sel_dept = st.selectbox("Choose Department", list(DEPARTMENTS.keys()))
    
    d_df = df[df['Department'] == sel_dept]
    d_active = d_df[d_df['Actual_Discharge'].isnull()]
    
    # ALOS Calculation
    d_closed = d_df[d_df['Actual_Discharge'].notnull()].copy()
    alos = 0
    if not d_closed.empty:
        d_closed['LOS'] = (d_closed['Actual_Discharge'] - d_closed['Admission_Date']).dt.total_seconds() / 86400
        alos = d_closed['LOS'].mean()
    
    col_d1, col_d2 = st.columns([1, 2])
    
    with col_d1:
        st.metric("Avg Length of Stay (ALOS)", f"{alos:.1f} Days")
        st.metric("Current Patients", len(d_active))
        
        # Delayed patients
        delayed = d_active[d_active['Expected_Discharge'] < datetime.now()].shape[0]
        st.metric("Delayed Discharges", delayed, delta=-delayed, delta_color="inverse")
        
    with col_d2:
        if not d_df.empty:
            fig = px.pie(d_df, names='Admission_Source', title=f"Admissions Source: {sel_dept}", hole=0.4)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for this department.")

# ---------------------------------------------------------
# 🔟 إعدادات البيانات: Data Management
# ---------------------------------------------------------
elif menu == "Data Management":
    st.header("💾 Data Operations")
    
    # 1. AI Simulation
    st.subheader("1. AI Data Simulation (Pandas Generator)")
    st.write("Use this to generate new synthetic scenarios for testing.")
    
    if st.button("🔄 Generate New AI Simulation Data"):
        st.session_state.df = generate_synthetic_data(60)
        st.success("✅ New synthetic data generated successfully using Pandas/NumPy!")
        st.rerun()
        
    st.markdown("---")

    # 2. Export / Import
    col_ex, col_im = st.columns(2)
    
    with col_ex:
        st.subheader("2. Export Data")
        # Convert to CSV friendly format
        df_out = df.copy()
        for c in ['Admission_Date', 'Expected_Discharge', 'Actual_Discharge']:
            df_out[c] = df_out[c].astype(str)
        
        csv = df_out.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "bed_data.csv", "text/csv")
        
    with col_im:
        st.subheader("3. Import Data")
        up_file = st.file_uploader("Upload Excel/CSV", type=['xlsx', 'csv'])
        if up_file:
            try:
                if up_file.name.endswith('.csv'):
                    new_df = pd.read_csv(up_file)
                else:
                    new_df = pd.read_excel(up_file)
                
                # Fix dates
                for c in ['Admission_Date', 'Expected_Discharge', 'Actual_Discharge']:
                    if c in new_df.columns:
                        new_df[c] = pd.to_datetime(new_df[c], errors='coerce')
                
                st.session_state.df = new_df
                st.success("Data imported successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
