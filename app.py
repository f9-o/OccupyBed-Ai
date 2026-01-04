import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتصميم (مطابق للطلب: تلوين وتنسيق)
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI | Pro Dashboard", layout="wide", page_icon="🏥")

st.markdown("""
<style>
    /* Global Dark Theme */
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }

    /* 1. AI Command Board (لوحة الذكاء الاصطناعي) */
    .ai-box {
        background: linear-gradient(90deg, #161B22 0%, #0D1117 100%);
        border: 1px solid #30363D; border-left: 6px solid #A371F7;
        border-radius: 8px; padding: 20px; margin-bottom: 20px;
    }
    .ai-header { color: #A371F7; font-weight: bold; font-size: 18px; display: flex; justify-content: space-between; }
    .ai-rec { color: #E6EDF3; font-size: 15px; margin-top: 10px; font-weight: 500; }
    .ai-risk { color: #F85149; font-size: 13px; margin-top: 5px; }

    /* 2. KPI Indicators (مؤشرات ملونة) */
    .kpi-card {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; text-align: center; height: 100%;
    }
    .kpi-title { color: #8B949E; font-size: 12px; text-transform: uppercase; font-weight: 700; }
    .kpi-val { font-size: 28px; font-weight: 800; margin: 5px 0; }
    .kpi-note { font-size: 11px; opacity: 0.8; }
    
    /* Colors for Status */
    .txt-green { color: #3FB950; }
    .txt-yellow { color: #D29922; }
    .txt-red { color: #F85149; }

    /* 3. Department Cards (تفاصيل الأقسام والجنس) */
    .dept-card {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px; position: relative;
    }
    .dept-head { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262D; padding-bottom: 8px; margin-bottom: 8px; }
    .dept-name { font-size: 15px; font-weight: 700; color: #E6EDF3; }
    .dept-metrics { display: flex; justify-content: space-between; font-size: 12px; color: #8B949E; }
    .gender-badge { background: #21262D; padding: 2px 6px; border-radius: 4px; color: #C9D1D9; font-size: 10px; }
    .overflow-alert { color: #D29922; font-size: 11px; margin-top: 6px; font-style: italic; }

    /* Custom Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Logic & Data (محاكاة ذكية للسيناريوهات المطلوبة)
# ---------------------------------------------------------

# تعريف الأقسام مع تحديد "القسم البديل" (Overflow Target)
DEPARTMENTS = {
    "ICU": {"cap": 16, "overflow": "HDU", "gen": "Mixed"},
    "Surgical Male": {"cap": 40, "overflow": "Medical Male", "gen": "Male"},
    "Surgical Female": {"cap": 40, "overflow": "Medical Female", "gen": "Female"},
    "Medical Male": {"cap": 50, "overflow": "Surgical Male", "gen": "Male"},
    "Medical Female": {"cap": 50, "overflow": "Surgical Female", "gen": "Female"},
    "Pediatric": {"cap": 30, "overflow": "None", "gen": "Mixed"},
    "Obstetrics": {"cap": 24, "overflow": "Gynae", "gen": "Female"},
}

def init_data():
    if 'df' not in st.session_state:
        data = []
        for _ in range(150):
            dept = np.random.choice(list(DEPARTMENTS.keys()))
            cap = DEPARTMENTS[dept]['cap']
            bed_n = np.random.randint(1, cap+1)
            
            # محاكاة تواريخ للدخول والخروج
            adm = datetime.now() - timedelta(days=np.random.randint(0, 5), hours=np.random.randint(1, 20))
            exp = adm + timedelta(days=np.random.randint(2, 8))
            
            # محاكاة حالة الخروج (البعض خرج والبعض لا)
            act = exp if np.random.random() < 0.15 else None
            
            # محاكاة "عدم توافق الجنس" (Gender Mismatch Scenario)
            # مثلاً 5% من الحالات تكون في قسم خطأ بسبب الضغط
            gender_rule = DEPARTMENTS[dept]['gen']
            if gender_rule == "Male": pat_gen = np.random.choice(["Male", "Female"], p=[0.95, 0.05])
            elif gender_rule == "Female": pat_gen = np.random.choice(["Female", "Male"], p=[0.95, 0.05])
            else: pat_gen = np.random.choice(["Male", "Female"])

            data.append({
                "Department": dept,
                "Bed": f"{dept[:3].upper()}-{bed_n}",
                "Gender": pat_gen,
                "Admit_Date": adm,
                "Exp_Discharge": exp,
                "Actual_Discharge": act
            })
        st.session_state.df = pd.DataFrame(data)

init_data()
df = st.session_state.df

# ---------------------------------------------------------
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.header("OccupyBed AI")
    
    st.markdown("---")
    menu = st.radio("القائمة الرئيسية", ["لوحة القيادة (Command Center)", "إدارة التنويم", "الإعدادات"])
    st.markdown("---")
    st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")

# ---------------------------------------------------------
# 4. Command Center (تنفيذ النواقص 1 و 2 و 3)
# ---------------------------------------------------------
if menu == "لوحة القيادة (Command Center)":
    
    # === الحسابات المركزية ===
    now = datetime.now()
    active = df[df['Actual_Discharge'].isnull()]
    
    # 1. Net Flow (التدفق الصافي)
    adm_today = len(df[df['Admit_Date'].dt.date == now.date()])
    dis_today = len(df[(df['Actual_Discharge'].notnull()) & (df['Actual_Discharge'].dt.date == now.date())])
    net_flow = adm_today - dis_today # الموجب يعني ضغط، السالب يعني تفريغ
    
    # 2. التوقعات (Forecast)
    exp_6h = active[active['Exp_Discharge'] <= (now + timedelta(hours=6))].shape[0]
    exp_24h = active[active['Exp_Discharge'] <= (now + timedelta(hours=24))].shape[0]
    
    # 3. الحالة العامة
    total_cap = sum(d['cap'] for d in DEPARTMENTS.values())
    curr_occ = len(active)
    occ_rate = (curr_occ / total_cap) * 100
    
    # تحديد الحالة واللون (Logic for Limits)
    if occ_rate > 90:
        sys_status, sys_color, css_cls = "CRITICAL", "#F85149", "txt-red"
        ai_rec = "إيقاف العمليات الاختيارية فوراً (Activate Code Black). تحويل الحالات الجديدة للمستشفيات المساندة."
        ai_risk = "خطر تكدس الطوارئ (ED Overcrowding) وشيك."
    elif occ_rate > 80:
        sys_status, sys_color, css_cls = "WARNING", "#D29922", "txt-yellow"
        ai_rec = "تسريع إجراءات الخروج للحالات المستقرة (Early Discharge)."
        ai_risk = "الأقسام الجراحية تقترب من الامتلاء."
    else:
        sys_status, sys_color, css_cls = "SAFE", "#3FB950", "txt-green"
        ai_rec = "الوضع مستقر. استمر في إجراءات التنويم القياسية."
        ai_risk = "لا يوجد مخاطر تشغيلية حالياً."

    # --- أولاً: لوحة AI العامة ---
    st.markdown(f"""
    <div class="ai-box" style="border-left-color: {sys_color};">
        <div class="ai-header">
            <span>🤖 AI Live Situation Report</span>
            <span style="color:{sys_color}; border:1px solid {sys_color}; padding:2px 8px; border-radius:4px;">{sys_status}</span>
        </div>
        <div style="margin-top:10px; font-size:14px;">
            <div><strong>💡 التوصية الفورية:</strong> {ai_rec}</div>
            <div style="margin-top:5px; color:#F85149;"><strong>⚠️ الخطر القادم:</strong> {ai_risk}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- ثانياً: مؤشرات المستشفى (Hospital KPIs) ---
    k1, k2, k3, k4, k5 = st.columns(5)
    
    # دالة لإنشاء الكرت الملون
    def kpi_html(label, val, note, color_class):
        return f"""
        <div class="kpi-card">
            <div class="kpi-title">{label}</div>
            <div class="kpi-val {color_class}">{val}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """
        
    flow_cls = "txt-red" if net_flow > 0 else "txt-green"
    
    k1.markdown(kpi_html("معدل الإشغال العام", f"{occ_rate:.1f}%", f"{curr_occ}/{total_cap} سرير", css_cls), unsafe_allow_html=True)
    k2.markdown(kpi_html("صافي التدفق (Net Flow)", f"{net_flow:+d}", "الدخول vs الخروج", flow_cls), unsafe_allow_html=True)
    k3.markdown(kpi_html("توقع خروج (6 ساعات)", str(exp_6h), "سرير متوقع خلوه", "txt-yellow"), unsafe_allow_html=True)
    k4.markdown(kpi_html("توقع خروج (24 ساعة)", str(exp_24h), "سرير متوقع خلوه", "txt-green"), unsafe_allow_html=True)
    
    # مؤشر تشغيلي: Turnover Interval (وهمي للمحاكاة)
    k5.markdown(kpi_html("معدل دوران السرير", "1.4", "يوم/مريض", "txt-green"), unsafe_allow_html=True)

    st.markdown("---")

    # --- ثالثاً: تفاصيل الأقسام (تطبيق النواقص) ---
    st.subheader("🏥 حالة الأقسام (Department Status & Logic)")
    
    d_cols = st.columns(3)
    dept_list = list(DEPARTMENTS.keys())
    
    for i, d_name in enumerate(dept_list):
        info = DEPARTMENTS[d_name]
        d_df = active[active['Department'] == d_name]
        
        # 1. الإشغال
        d_curr = len(d_df)
        d_pct = (d_curr / info['cap']) * 100
        
        # 2. الجنس (ذكور/إناث)
        males = len(d_df[d_df['Gender'] == "Male"])
        females = len(d_df[d_df['Gender'] == "Female"])
        
        # 3. تأخر الخروج (Bed Blockers)
        # نحسب من تجاوز وقت خروجه المتوقع
        delayed = len(d_df[d_df['Exp_Discharge'] < now])
        
        # 4. عدم توافق الجنس (Mismatch)
        mismatch_count = 0
        if info['gen'] == 'Male': mismatch_count = females
        elif info['gen'] == 'Female': mismatch_count = males
        
        # تحديد لون الكرت
        border_col = "#3FB950" # Green
        status_txt = "SAFE"
        overflow_msg = ""
        
        if d_pct >= 90:
            border_col = "#F85149" # Red
            status_txt = "CRITICAL"
            overflow_msg = f"⚠ Full! Divert to: <b>{info['overflow']}</b>"
        elif d_pct >= 75:
            border_col = "#D29922" # Yellow
            status_txt = "WARNING"
        
        with d_cols[i % 3]:
            st.markdown(f"""
            <div class="dept-card" style="border-top: 4px solid {border_col};">
                <div class="dept-head">
                    <span class="dept-name">{d_name}</span>
                    <span style="color:{border_col}; font-weight:bold; font-size:11px; border:1px solid {border_col}; padding:1px 5px; border-radius:4px;">{status_txt}</span>
                </div>
                <div class="dept-metrics">
                    <span>Occupancy: <b style="color:#E6EDF3">{d_curr}/{info['cap']}</b></span>
                    <span>{int(d_pct)}%</span>
                </div>
                <div style="background:#21262D; height:6px; border-radius:3px; margin:8px 0; overflow:hidden;">
                    <div style="width:{min(d_pct, 100)}%; background:{border_col}; height:100%;"></div>
                </div>
                
                <div style="display:flex; justify-content:space-between; margin-top:8px;">
                    <span class="gender-badge">🚹 {males} | 🚺 {females}</span>
                    <span class="gender-badge" style="color:#F85149">Delayed: {delayed}</span>
                </div>
                
                <div style="margin-top:8px; font-size:11px;">
                    {f'<div style="color:#F85149">⛔ Gender Mismatch: {mismatch_count}</div>' if mismatch_count > 0 else ''}
                    <div class="overflow-alert">{overflow_msg}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. الصفحات الأخرى (إبقاء الوظائف الأساسية)
# ---------------------------------------------------------
elif menu == "إدارة التنويم":
    st.title("إدارة الدخول والخروج")
    st.info("نظام التسجيل اليدوي (تم اختصاره للتركيز على الداشبورد)")
    st.dataframe(df.head(10), use_container_width=True)

elif menu == "الإعدادات":
    st.title("إعدادات النظام")
    if st.button("إعادة ضبط المصنع (Factory Reset)"):
        del st.session_state.df
        st.success("تم تصفير البيانات.")
        time.sleep(1)
        st.rerun()
