import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import os
import time

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتصميم الاحترافي (بدون إيموجي)
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI", layout="wide", page_icon=None)

# CSS: Dark Mode Professional - تنظيف الواجهة من الإيموجي وتنسيق الجداول
st.markdown("""
<style>
    /* خلفية داكنة */
    .stApp { background-color: #0e1117; }
    
    /* القائمة الجانبية */
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #333; }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; font-family: sans-serif; }

    /* كروت الأرقام العلوية */
    .kpi-card {
        background: #1f2937;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        color: white;
        margin-bottom: 10px;
    }
    .kpi-num { font-size: 36px; font-weight: bold; margin: 10px 0; }
    .kpi-label { font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af; }
    
    /* كروت الأقسام التفصيلية */
    .dept-box {
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .dept-title { font-size: 16px; font-weight: bold; color: white; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .dept-stats { display: flex; justify-content: space-between; font-size: 12px; color: #d1d5db; margin-bottom: 5px; }
    .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; }
    
    /* ألوان الحالة */
    .bg-safe { background-color: #065f46; color: #6ee7b7; } /* Green */
    .bg-warn { background-color: #78350f; color: #fcd34d; } /* Orange */
    .bg-crit { background-color: #7f1d1d; color: #fca5a5; } /* Red */

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. هيكلة البيانات (Data Structure)
# ---------------------------------------------------------
# تعريف الأقسام بسعة سريرية واقعية (مجموعهم هو السعة الكلية)
DEPARTMENTS = {
    "ICU": {"cap": 16, "gen": "Mixed"},
    "Surgical Male": {"cap": 40, "gen": "Male"},
    "Surgical Female": {"cap": 40, "gen": "Female"},
    "Medical Male": {"cap": 50, "gen": "Male"},
    "Medical Female": {"cap": 50, "gen": "Female"},
    "Pediatric": {"cap": 30, "gen": "Mixed"},
    "Obstetrics": {"cap": 24, "gen": "Female"},
}

# قاعدة بيانات المرضى (محاكاة) للتحقق من الجنس
PATIENT_DB = {f"PIN-{1000+i}": ("Male" if i % 2 == 0 else "Female") for i in range(200)}

def init_state():
    if 'df' not in st.session_state:
        # توليد بيانات أولية عشوائية لملء النظام عند التشغيل الأول
        data = []
        for i in range(120): # نبدأ بـ 120 مريض
            dept = np.random.choice(list(DEPARTMENTS.keys()))
            cap = DEPARTMENTS[dept]['cap']
            bed_num = np.random.randint(1, cap + 1)
            
            adm = datetime.now() - timedelta(days=np.random.randint(0, 10))
            exp = adm + timedelta(days=np.random.randint(2, 10))
            
            # 15% فقط تم خروجهم، الباقي منومين
            act = exp if np.random.random() < 0.15 else None
            
            gender = DEPARTMENTS[dept]['gen']
            if gender == "Mixed": gender = np.random.choice(["Male", "Female"])
            
            data.append({
                "PIN": f"PIN-{2000+i}", 
                "Gender": gender,
                "Department": dept, 
                "Bed": f"{dept[:3]}-{bed_num}",
                "Admit_Date": adm, 
                "Exp_Discharge": exp, 
                "Actual_Discharge": act,
                "Source": "Emergency"
            })
        st.session_state.df = pd.DataFrame(data)

init_state()
df = st.session_state.df

# ---------------------------------------------------------
# 3. القائمة الجانبية (Sidebar)
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("## OccupyBed AI")
        
    st.markdown("---")
    menu = st.radio("MAIN MENU", ["Overview", "Live Admissions", "Analytics", "Settings"], label_visibility="collapsed")
    
    st.markdown("---")
    st.info(f"**Admin Logged In**\nSystem Online")

# ---------------------------------------------------------
# 4. الصفحة الرئيسية (Overview)
# ---------------------------------------------------------
if menu == "Overview":
    # --- Top Header ---
    c1, c2 = st.columns([3, 1])
    with c1: st.title("Real-time Overview")
    with c2: 
        # Forecast slider logic
        fc_window = st.selectbox("Forecast Window", [6, 12, 24, 48, 72], index=2, format_func=lambda x: f"{x} Hours")
    
    # --- Global Calculations ---
    # تصفية المرضى النشطين (الذين لم يخرجوا بعد)
    active_df = df[df['Actual_Discharge'].isnull()]
    
    total_beds = sum(d['cap'] for d in DEPARTMENTS.values())
    occupied_beds = len(active_df)
    available_beds = total_beds - occupied_beds
    occupancy_rate = int((occupied_beds / total_beds) * 100)
    
    # حساب التوقعات (كم سرير سيفضى خلال X ساعة)
    future_time = datetime.now() + timedelta(hours=fc_window)
    expected_free_global = active_df[active_df['Exp_Discharge'] <= future_time].shape[0]

    # --- KPI Cards ---
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi-card" style="border-top: 4px solid #3b82f6;">
            <div class="kpi-label">Total Licensed Beds</div>
            <div class="kpi-num">{total_beds}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card" style="border-top: 4px solid #eab308;">
            <div class="kpi-label">Occupied Beds</div>
            <div class="kpi-num">{occupied_beds}</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-card" style="border-top: 4px solid #22c55e;">
            <div class="kpi-label">Available Now</div>
            <div class="kpi-num">{available_beds}</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card" style="border-top: 4px solid #a855f7;">
            <div class="kpi-label">Expected Free ({fc_window}h)</div>
            <div class="kpi-num">{expected_free_global}</div>
        </div>""", unsafe_allow_html=True)

    # --- Charts & AI Alerts ---
    g_col, ai_col = st.columns([1, 2])
    
    with g_col:
        st.markdown("### Hospital Pressure")
        # مؤشر (Gauge) يظهر الضغط بشكل واقعي
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = occupancy_rate,
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [0, 75], 'color': "#064e3b"},
                    {'range': [75, 90], 'color': "#78350f"},
                    {'range': [90, 100], 'color': "#7f1d1d"}
                ],
                'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': occupancy_rate}
            }
        ))
        fig.update_layout(height=250, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)
        
    with ai_col:
        st.markdown("### AI Suggested Actions")
        # منطق الـ AI المعتمد على البيانات الحقيقية
        alerts = []
        for dept, info in DEPARTMENTS.items():
            d_occ = len(active_df[active_df['Department'] == dept])
            d_rate = (d_occ / info['cap']) * 100
            
            if d_rate >= 90:
                st.error(f"CRITICAL: **{dept}** is at {d_rate:.1f}% capacity. Activate surge protocol.")
            elif d_rate >= 75:
                st.warning(f"WARNING: **{dept}** is high load ({d_rate:.1f}%). Prioritize discharges.")
            
            # Delayed discharges logic
            delayed = len(active_df[(active_df['Department'] == dept) & (active_df['Exp_Discharge'] < datetime.now())])
            if delayed > 0:
                st.info(f"ACTION: **{dept}** has {delayed} patients exceeding expected stay. Coordinate with physicians.")

        if occupancy_rate < 70 and not alerts:
             st.success("STATUS: Hospital capacity is optimal. No critical actions required.")

    # --- Department Cards (The detailed grid you asked for) ---
    st.markdown("### Department Status")
    
    cols = st.columns(3)
    dept_names = list(DEPARTMENTS.keys())
    
    for i, dept in enumerate(dept_names):
        info = DEPARTMENTS[dept]
        d_pats = active_df[active_df['Department'] == dept]
        
        d_occ = len(d_pats)
        d_cap = info['cap']
        d_avail = d_cap - d_occ
        d_rate = int((d_occ / d_cap) * 100)
        
        # التوقع الخاص بهذا القسم فقط
        d_exp_free = d_pats[d_pats['Exp_Discharge'] <= future_time].shape[0]
        
        # تحديد لون الحالة والنص
        status_cls = "bg-safe"
        status_txt = "SAFE"
        if d_rate > 75: 
            status_cls = "bg-warn"
            status_txt = "WARNING"
        if d_rate > 90: 
            status_cls = "bg-crit"
            status_txt = "CRITICAL"
        
        with cols[i % 3]:
            st.markdown(f"""
            <div class="dept-box">
                <div class="dept-title">
                    <span>{dept}</span>
                    <span class="status-badge {status_cls}">{status_txt}</span>
                </div>
                <div class="dept-stats">
                    <span>Capacity: <b>{d_cap}</b></span>
                    <span>Occupied: <b>{d_occ}</b></span>
                </div>
                <div class="dept-stats">
                    <span>Available: <b>{d_avail}</b></span>
                    <span style="color: #a855f7">Exp. Free ({fc_window}h): <b>{d_exp_free}</b></span>
                </div>
                <div style="background:#374151; height:6px; border-radius:3px; margin-top:5px;">
                    <div style="background-color: {'#22c55e' if d_rate<75 else ('#eab308' if d_rate<90 else '#ef4444')}; 
                                width:{d_rate}%; height:100%; border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. صفحة الإدخال (Live Admissions) - تم إصلاحها بالكامل
# ---------------------------------------------------------
elif menu == "Live Admissions":
    st.title("Patient Admission & Discharge Center")
    
    # 1. نقل أزرار البيانات هنا
    with st.expander("📂 Data Operations (Import / Export)", expanded=False):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Current Data (CSV)", csv, "bed_data.csv", "text/csv")
        with col_d2:
            uploaded_file = st.file_uploader("Import Data", type=['csv'])
            if uploaded_file:
                try:
                    loaded_df = pd.read_csv(uploaded_file)
                    # تحويل الأعمدة لتواريخ
                    for c in ['Admit_Date', 'Exp_Discharge', 'Actual_Discharge']:
                        loaded_df[c] = pd.to_datetime(loaded_df[c])
                    st.session_state.df = loaded_df
                    st.success("Data Imported Successfully!")
                    st.rerun()
                except:
                    st.error("Invalid CSV format.")

    st.markdown("---")
    
    # 2. نموذج الإدخال (بدون st.form للحصول على تفاعل فوري)
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("New Admission")
        # اختيار الـ PIN
        pin = st.selectbox("Select Patient PIN", ["Select..."] + list(PATIENT_DB.keys()))
        
        # --- التحقق الفوري من الجنس ---
        pat_gender = "Unknown"
        if pin != "Select...":
            pat_gender = PATIENT_DB[pin]
            st.info(f"👤 System Identified: **{pat_gender}**")
        
        # اختيار القسم
        dept_list = list(DEPARTMENTS.keys())
        sel_dept = st.selectbox("Assign Department", ["Select..."] + dept_list)
        
        # --- التحقق من توافق الجنس مع القسم ---
        if pin != "Select..." and sel_dept != "Select...":
            dept_gen_rule = DEPARTMENTS[sel_dept]['gen']
            if dept_gen_rule != "Mixed" and dept_gen_rule != pat_gender:
                st.error(f"⛔ Conflict: Patient is **{pat_gender}** but **{sel_dept}** is {dept_gen_rule} Only.")
        
        # اختيار السرير (يظهر الأسرة الفارغة فقط)
        bed_options = []
        if sel_dept != "Select...":
            # الأسرة المشغولة في هذا القسم
            active = df[(df['Department'] == sel_dept) & (df['Actual_Discharge'].isnull())]
            occupied_beds = active['Bed'].tolist()
            # كل الأسرة
            all_beds = [f"{sel_dept[:3]}-{i}" for i in range(1, DEPARTMENTS[sel_dept]['cap']+1)]
            # الفارغة
            bed_options = [b for b in all_beds if b not in occupied_beds]
            
        sel_bed = st.selectbox("Assign Bed", bed_options if bed_options else ["No Beds Available"])
        
    with c2:
        st.subheader("Timing & Source")
        admit_date = st.date_input("Admission Date", datetime.now())
        # تحويل الوقت لصيغة واضحة
        admit_time = st.time_input("Admission Time (24h)", datetime.now().time())
        
        source = st.selectbox("Source", ["Emergency", "Elective", "Transfer"])
        exp_days = st.number_input("Est. Length of Stay (Days)", min_value=1, value=3)

    # زر الإضافة (يحفظ في الذاكرة)
    if st.button("✅ Admit Patient", use_container_width=True):
        if pin != "Select..." and sel_dept != "Select..." and sel_bed:
            new_record = {
                "PIN": pin,
                "Gender": pat_gender,
                "Department": sel_dept,
                "Bed": sel_bed,
                "Admit_Date": datetime.combine(admit_date, admit_time),
                "Exp_Discharge": datetime.combine(admit_date, admit_time) + timedelta(days=exp_days),
                "Actual_Discharge": None,
                "Source": source
            }
            # إضافة للسجل وحفظه
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_record])], ignore_index=True)
            st.success(f"Successfully admitted {pin} to {sel_bed}")
            time.sleep(1)
            st.rerun() # تحديث الصفحة لرؤية النتيجة في الجدول
        else:
            st.warning("Please fill all required fields correctly.")

    # 3. جدول المرضى الحاليين (Recent Activity)
    st.markdown("### 🏥 Current Inpatients (Real-time)")
    # عرض آخر 10 مدخلات
    active_view = df[df['Actual_Discharge'].isnull()].sort_values(by="Admit_Date", ascending=False).head(10)
    st.dataframe(active_view[['PIN', 'Department', 'Bed', 'Admit_Date', 'Source']], use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 6. التحليلات (Analytics) - تم الإصلاح
# ---------------------------------------------------------
elif menu == "Analytics":
    st.title("Operational Analytics")
    
    # تحضير البيانات
    df['LOS'] = (df['Exp_Discharge'] - df['Admit_Date']).dt.total_seconds() / 86400
    avg_los = df['LOS'].mean()
    
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Avg Length of Stay", f"{avg_los:.1f} Days")
    with m2: st.metric("Total Admissions", len(df))
    with m3: st.metric("Discharge Rate", f"{int(len(df[df['Actual_Discharge'].notnull()])/len(df)*100)}%")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Admissions by Source")
        # Donut Chart
        src_counts = df['Source'].value_counts().reset_index()
        src_counts.columns = ['Source', 'Count']
        fig = px.pie(src_counts, values='Count', names='Source', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.markdown("#### Length of Stay Distribution")
        # Box Plot
        fig2 = px.box(df, x="Department", y="LOS", color="Department")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 7. الإعدادات (Settings)
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("System Settings")
    st.warning("⚠️ Warning: This will wipe all current data and reset to simulation mode.")
    if st.button("🔴 Factory Reset / Clear All Data"):
        del st.session_state.df
        st.rerun()