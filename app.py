import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- 1. إعداد الصفحة ---
st.set_page_config(layout="wide", page_title="OccupyBed AI", page_icon="🏥")

# --- 2. تعريف ألوان الهوية البصرية (Brand Identity) ---
# تم تصحيح الأكواد لتتوافق مع الصورة (Hex Codes)
BRAND_WHITE = "#FFFFFF"
BRAND_LIGHT_BLUE = "#88ACDC"
BRAND_MED_BLUE = "#4C8EC0"  # (Updated hex)
BRAND_TEAL = "#60A487"      # للأسرة المتاحة / الحالات الآمنة
BRAND_PRIMARY = "#1B6AA0"   # اللون الأساسي للأزرار والعناصر النشطة
BRAND_DARK = "#2B4662"      # للعناوين والنصوص الغامقة
BRAND_GRAY = "#666666"      # للنصوص الفرعية
BRAND_BG_GRAY = "#F8F9FA"   # خلفية فاتحة جداً
BRAND_ALERT = "#D32F2F"     # لون أحمر (تكميلي) للتنبيهات القصوى

# --- 3. CSS لتطبيق الهوية على كامل التطبيق ---
st.markdown(f"""
<style>
    /* خلفية التطبيق */
    .stApp {{ background-color: {BRAND_WHITE} !important; }}
    
    /* العناوين (H1, H2, H3) بلون الهوية الداكن */
    h1, h2, h3, .streamlit-expanderHeader {{
        color: {BRAND_DARK} !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }}
    
    /* النصوص العادية */
    .stMarkdown p, .stCaption, li {{
        color: {BRAND_GRAY} !important;
        font-size: 1rem;
    }}
    
    /* الأرقام الكبيرة (KPIs) */
    div[data-testid="stMetricValue"] {{
        color: {BRAND_PRIMARY} !important;
        font-weight: 800;
        font-size: 2rem !important;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {BRAND_GRAY} !important;
    }}
    
    /* تخصيص القائمة الجانبية (Sidebar) */
    section[data-testid="stSidebar"] {{
        background-color: {BRAND_BG_GRAY} !important;
        border-right: 1px solid #E0E0E0;
    }}
    
    /* الأزرار (Primary Buttons) */
    .stButton > button {{
        background-color: {BRAND_PRIMARY} !important;
        color: {BRAND_WHITE} !important;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: background-color 0.3s;
    }}
    .stButton > button:hover {{
        background-color: {BRAND_MED_BLUE} !important;
    }}
    
    /* تحسين شكل الجداول والكروت */
    div[data-testid="stDataFrame"], .css-1r6slb0 {{
        border: 1px solid #E0E0E0;
        border-radius: 10px;
    }}
    
    /* تخصيص التابات */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {BRAND_BG_GRAY};
        border-radius: 4px;
        color: {BRAND_GRAY};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BRAND_LIGHT_BLUE} !important;
        color: {BRAND_WHITE} !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. البيانات الوهمية (Mock Data) ---
if 'bed_data' not in st.session_state:
    # إنشاء بيانات لـ 24 سرير
    beds = []
    statuses = ["Occupied", "Available", "Cleaning", "Maintenance"]
    depts = ["ICU", "Surgery", "General Ward", "ER"]
    
    for i in range(1, 25):
        status = np.random.choice(statuses, p=[0.6, 0.3, 0.05, 0.05])
        dept = np.random.choice(depts)
        if status == "Occupied":
            patient_id = f"P-{np.random.randint(1000,9999)}"
            pred_discharge = f"{np.random.randint(1,48)} hrs"
        else:
            patient_id = "--"
            pred_discharge = "--"
            
        beds.append({
            "Bed ID": f"B-{i:02d}",
            "Department": dept,
            "Status": status,
            "Patient": patient_id,
            "AI Prediction": pred_discharge
        })
    st.session_state.bed_data = pd.DataFrame(beds)

# --- 5. القائمة الجانبية ---
with st.sidebar:
    try:
        st.image("logo.png", width=180)
    except:
        st.markdown(f"<h1 style='color:{BRAND_PRIMARY}'>OccupyBed AI</h1>", unsafe_allow_html=True)
    
    st.markdown("### Navigation")
    page = st.radio("Go to", ["Dashboard Overview", "Visual Ward Map", "Analytics & Forecast"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown(f"**System Status:** <span style='color:{BRAND_TEAL}'>● Online</span>", unsafe_allow_html=True)
    st.caption("AI Model: v2.4 (Live)")

# =======================================================
# الصفحة 1: Dashboard Overview (نظرة عامة)
# =======================================================
if page == "Dashboard Overview":
    st.title("🏥 Hospital Command Center")
    st.caption("Real-time occupancy insights and AI-driven alerts.")
    
    # 1. KPIs Row
    k1, k2, k3, k4 = st.columns(4)
    df = st.session_state.bed_data
    occ_rate = int((len(df[df['Status']=='Occupied']) / len(df)) * 100)
    
    with k1:
        with st.container(border=True):
            st.metric("Total Occupancy", f"{occ_rate}%", "High Load", delta_color="inverse")
            st.progress(occ_rate)
    with k2:
        with st.container(border=True):
            st.metric("Available Beds", len(df[df['Status']=='Available']), "-2 vs Avg")
    with k3:
        with st.container(border=True):
            st.metric("Predicted Discharges", "5 Beds", "Next 4 Hours")
    with k4:
        with st.container(border=True):
            st.metric("ER Wait Time", "42 mins", "Stable", delta_color="normal")

    # 2. Alerts Section (إضافة مفيدة: تنبيهات ذكية)
    st.subheader("⚠️ AI Early Warning System")
    alert_col1, alert_col2 = st.columns([2, 1])
    
    with alert_col1:
        # كروت تنبيه بتصميم مخصص
        st.markdown(f"""
        <div style="background-color: #FFF4E5; border-left: 5px solid #FF9800; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
            <strong style="color: #E65100;">Warning: ICU Capacity at 90%</strong><br>
            <span style="color: {BRAND_GRAY};">AI predicts full saturation by 18:00 based on ER inflow trends. Recommend diverting non-critical transfers.</span>
        </div>
        <div style="background-color: #E8F5E9; border-left: 5px solid {BRAND_TEAL}; padding: 15px; border-radius: 5px;">
            <strong style="color: {BRAND_TEAL};">Optimization Opportunity</strong><br>
            <span style="color: {BRAND_GRAY};">3 Patients in Surgery Ward are marked "Ready for Discharge". Process now to clear beds.</span>
        </div>
        """, unsafe_allow_html=True)

    with alert_col2:
        st.info("💡 **AI Recommendation:**\nOpen Overflow Ward B to handle expected weekend surge.")

# =======================================================
# الصفحة 2: Visual Ward Map (الإضافة المبهرة - خريطة الأسرّة)
# =======================================================
elif page == "Visual Ward Map":
    st.title("🗺️ Live Ward Map")
    st.caption("Visual representation of bed status across departments.")
    
    # فلاتر
    f_col1, f_col2, f_col3 = st.columns([1,1,2])
    with f_col1:
        selected_dept = st.selectbox("Filter by Department", ["All"] + list(st.session_state.bed_data['Department'].unique()))
    with f_col3:
        st.markdown(f"""
        <div style="display: flex; gap: 15px; align-items: center; justify-content: flex-end; height: 100%;">
            <span style="color:{BRAND_PRIMARY}">■ Occupied</span>
            <span style="color:{BRAND_TEAL}">■ Available</span>
            <span style="color:{BRAND_GRAY}">■ Maintenance</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # تصفية البيانات
    display_df = st.session_state.bed_data
    if selected_dept != "All":
        display_df = display_df[display_df['Department'] == selected_dept]

    # رسم الخريطة (Grid Layout)
    cols = st.columns(4) # 4 أسرة في الصف
    for index, row in display_df.iterrows():
        # تحديد اللون بناءً على الحالة
        if row['Status'] == 'Occupied':
            card_color = BRAND_PRIMARY
            bg_color = "#E3F2FD" # Light Blue BG
            icon = "👤"
        elif row['Status'] == 'Available':
            card_color = BRAND_TEAL
            bg_color = "#E8F5E9" # Light Green BG
            icon = "🛏️"
        else:
            card_color = BRAND_GRAY
            bg_color = "#F5F5F5"
            icon = "🔧"

        with cols[index % 4]:
            st.markdown(f"""
            <div style="
                border: 2px solid {card_color};
                background-color: {bg_color};
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <div style="font-size: 2rem; margin-bottom: 5px;">{icon}</div>
                <h4 style="color: {BRAND_DARK}; margin: 0;">{row['Bed ID']}</h4>
                <p style="color: {BRAND_GRAY}; font-size: 0.8rem; margin: 0;">{row['Department']}</p>
                <div style="background-color: {card_color}; color: white; padding: 2px 8px; border-radius: 12px; display: inline-block; font-size: 0.8rem; margin-top: 5px;">
                    {row['Status']}
                </div>
                <p style="color: {BRAND_DARK}; font-size: 0.7rem; margin-top: 8px;">
                    <b>Prediction:</b> {row['AI Prediction']}
                </p>
            </div>
            """, unsafe_allow_html=True)

# =======================================================
# الصفحة 3: Analytics & Forecast (تحليلات متقدمة)
# =======================================================
elif page == "Analytics & Forecast":
    st.title("📊 Predictive Analytics")
    
    tab1, tab2 = st.tabs(["Occupancy Forecast", "Patient Demographics"])
    
    with tab1:
        st.subheader("48-Hour Occupancy Forecast")
        # بيانات وهمية للتنبؤ
        hours = list(range(0, 24, 2))
        actual = [70, 72, 75, 80, 85, 88, 90, 85, 80, 78, 75, 72]
        predicted = [70, 73, 78, 85, 92, 95, 92, 88, 82, 75, 70, 68]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hours, y=actual, mode='lines', name='Actual', line=dict(color=BRAND_PRIMARY, width=3)))
        fig.add_trace(go.Scatter(x=hours, y=predicted, mode='lines', name='AI Prediction', line=dict(color=BRAND_LIGHT_BLUE, width=3, dash='dash')))
        
        # إضافة منطقة "الخطر"
        fig.add_hrect(y0=90, y1=100, line_width=0, fillcolor="red", opacity=0.1, annotation_text="Critical Capacity", annotation_position="top right")
        
        fig.update_layout(
            xaxis_title="Hour of Day",
            yaxis_title="Occupancy %",
            plot_bgcolor="white",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Admission Sources")
            labels = ['Emergency', 'Referral', 'Elective']
            values = [55, 15, 30]
            # استخدام ألوان الهوية في الرسم البياني
            fig_pie = px.pie(values=values, names=labels, hole=0.6, 
                             color_discrete_sequence=[BRAND_PRIMARY, BRAND_LIGHT_BLUE, BRAND_TEAL])
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Patients by Department")
            dept_counts = st.session_state.bed_data['Department'].value_counts()
            fig_bar = px.bar(dept_counts, x=dept_counts.index, y=dept_counts.values,
                             color_discrete_sequence=[BRAND_MED_BLUE])
            fig_bar.update_layout(plot_bgcolor="white")
            st.plotly_chart(fig_bar, use_container_width=True)