import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import io
from io import BytesIO

# ---------------------------------------------------------
# 1. Page Settings and Caching
# ---------------------------------------------------------
st.set_page_config(
    page_title="OccupyBed AI Pro | Bed Management System", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخزين مؤقت للبيانات الثقيلة
@st.cache_data(ttl=300, show_spinner=False)
def load_initial_data():
    """Load initial data with caching"""
    # Patient database
    patients = []
    for i in range(1, 51):  # Reduced from 101 to 50
        patient_id = f"P{str(i).zfill(3)}"
        gender = "Male" if i % 2 == 0 else "Female"
        patients.append({"PIN": patient_id, "Gender": gender})
    
    patient_db = pd.DataFrame(patients)
    
    # Departments configuration - simplified
    DEPARTMENTS = {
        "Medical - Male": {"capacity": 50, "gender": "Male", "color": "#3FB950"},
        "Medical - Female": {"capacity": 50, "gender": "Female", "color": "#A371F7"},
        "Surgical - Male": {"capacity": 40, "gender": "Male", "color": "#1F6FEB"},
        "Surgical - Female": {"capacity": 40, "gender": "Female", "color": "#FF7B72"},
        "ICU": {"capacity": 16, "gender": "Mixed", "color": "#FFA657"},
        "Pediatric": {"capacity": 30, "gender": "Mixed", "color": "#7EE787"},
        "Obstetrics and Gynecology": {"capacity": 24, "gender": "Female", "color": "#D2A8FF"}
    }
    
    # Generate sample patient data - minimized
    now = datetime.now()
    sample_data = []
    
    # Create rooms and beds
    room_counter = 100
    
    for dept_name, dept_info in DEPARTMENTS.items():
        # Create 5-10 patients per department
        num_patients = np.random.randint(5, min(15, dept_info["capacity"]))
        
        for i in range(num_patients):
            room_counter += 1
            bed_num = (i % 4) + 1  # 4 beds per room
            room = f"{dept_name[:3].upper()}-{room_counter}"
            bed = f"{room}-B{bed_num}"
            
            pin = f"P{np.random.randint(1, 51):03d}"
            gender = dept_info["gender"] if dept_info["gender"] != "Mixed" else np.random.choice(["Male", "Female"])
            
            sample_data.append({
                "PIN": pin,
                "Department": dept_name,
                "Room": room,
                "Bed": bed,
                "Admission_Date": (now - timedelta(days=np.random.randint(0, 5))).date(),
                "Admission_Time": (datetime.now() - timedelta(hours=np.random.randint(0, 24))).time(),
                "Admission_Source": np.random.choice(["Emergency", "Elective", "Transfer"]),
                "Expected_Discharge_Date": (now + timedelta(days=np.random.randint(1, 7))).date(),
                "Expected_Discharge_Time": datetime.now().time(),
                "Actual_Discharge_Date": None,
                "Actual_Discharge_Time": None,
                "Status": np.random.choice(["Active", "Ready for Discharge", "Delayed Discharge"], p=[0.7, 0.2, 0.1]),
                "Gender": gender
            })
    
    patients_df = pd.DataFrame(sample_data)
    
    return patient_db, patients_df, DEPARTMENTS

# Load data with caching
patient_db, patients_df, DEPARTMENTS = load_initial_data()

# Initialize session state
if 'patients_df' not in st.session_state:
    st.session_state.patients_df = patients_df.copy()

if 'patient_db' not in st.session_state:
    st.session_state.patient_db = patient_db.copy()

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# ---------------------------------------------------------
# 2. CSS Styling
# ---------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }
    
    .kpi-card {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; text-align: center; height: 100%;
    }
    .kpi-title { color: #8B949E; font-size: 12px; text-transform: uppercase; font-weight: 700; }
    .kpi-val { font-size: 28px; font-weight: 800; margin: 5px 0; }
    .kpi-note { font-size: 11px; opacity: 0.8; }
    
    .dept-card {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px;
    }
    
    .ai-box {
        background: linear-gradient(90deg, #161B22 0%, #0D1117 100%);
        border: 1px solid #30363D; border-left: 6px solid #A371F7;
        border-radius: 8px; padding: 20px; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. Helper Functions with Caching
# ---------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def get_department_status(dept_name, forecast_hours=6):
    """Get department status - cached"""
    dept_info = DEPARTMENTS[dept_name]
    
    current_patients = st.session_state.patients_df[
        (st.session_state.patients_df['Department'] == dept_name) &
        (st.session_state.patients_df['Actual_Discharge_Date'].isna())
    ]
    
    total_beds = dept_info['capacity']
    occupied = len(current_patients)
    available = total_beds - occupied
    occupancy_rate = (occupied / total_beds) * 100 if total_beds > 0 else 0
    
    # Simplified forecast calculation
    ready_to_discharge = current_patients[
        current_patients['Status'] == 'Ready for Discharge'
    ].shape[0]
    
    delayed_discharge = current_patients[
        current_patients['Status'] == 'Delayed Discharge'
    ].shape[0]
    
    # Determine status
    if occupancy_rate < 70:
        status_color = "#3FB950"
        status_text = "SAFE"
    elif occupancy_rate < 85:
        status_color = "#D29922"
        status_text = "WARNING"
    else:
        status_color = "#F85149"
        status_text = "CRITICAL"
    
    return {
        "department": dept_name,
        "total_beds": total_beds,
        "occupied": occupied,
        "available": available,
        "occupancy_rate": occupancy_rate,
        "ready_to_discharge": ready_to_discharge,
        "delayed_discharge": delayed_discharge,
        "status_color": status_color,
        "status_text": status_text
    }

@st.cache_data(ttl=60, show_spinner=False)
def calculate_hospital_kpis():
    """Calculate hospital KPIs - cached"""
    total_capacity = sum(dept['capacity'] for dept in DEPARTMENTS.values())
    
    current_patients = st.session_state.patients_df[
        st.session_state.patients_df['Actual_Discharge_Date'].isna()
    ]
    
    total_occupied = len(current_patients)
    occupancy_rate = (total_occupied / total_capacity) * 100 if total_capacity > 0 else 0
    
    # Simplified calculations
    today = datetime.now().date()
    admissions_today = 5  # Mock value for performance
    discharges_today = 3  # Mock value for performance
    net_flow = admissions_today - discharges_today
    
    return {
        "total_beds": total_capacity,
        "occupied_beds": total_occupied,
        "available_beds": total_capacity - total_occupied,
        "occupancy_rate": occupancy_rate,
        "admissions_today": admissions_today,
        "discharges_today": discharges_today,
        "net_flow": net_flow,
        "ready_to_discharge": current_patients[current_patients['Status'] == 'Ready for Discharge'].shape[0],
        "delayed_discharge": current_patients[current_patients['Status'] == 'Delayed Discharge'].shape[0]
    }

def generate_ai_recommendations():
    """Generate AI recommendations - lightweight"""
    recommendations = []
    
    # Check only critical departments
    for dept_name in DEPARTMENTS.keys():
        status = get_department_status(dept_name)
        
        if status['occupancy_rate'] >= 85:
            recommendations.append({
                "department": dept_name,
                "type": "CRITICAL",
                "message": f"High occupancy in {dept_name}. Consider accelerating discharge.",
                "priority": 1
            })
        
        if status['delayed_discharge'] > 2:
            recommendations.append({
                "department": dept_name,
                "type": "WARNING",
                "message": f"Delayed discharges in {dept_name}. Review pending approvals.",
                "priority": 2
            })
    
    recommendations.sort(key=lambda x: x['priority'])
    return recommendations[:3]  # Return only top 3

# ---------------------------------------------------------
# 4. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## OccupyBed AI Pro")
    st.markdown("---")
    
    menu = st.radio(
        "Main Menu",
        ["Dashboard", "Admission Management", "KPIs", "Settings"],
        key="main_menu"
    )
    
    st.markdown("---")
    st.caption(f"Last Update: {st.session_state.last_update.strftime('%H:%M:%S')}")
    
    # Simplified file upload
    st.markdown("---")
    if st.button("Reset Sample Data", key="reset_btn"):
        st.session_state.patients_df = patients_df.copy()
        st.session_state.last_update = datetime.now()
        st.success("Data reset!")
        st.rerun()

# ---------------------------------------------------------
# 5. Dashboard Page - Optimized
# ---------------------------------------------------------
if menu == "Dashboard":
    st.title("Dashboard - Overview")
    
    # Forecast selection
    col1, col2 = st.columns([3, 1])
    with col2:
        forecast_hours = st.selectbox(
            "Forecast Hours:",
            [6, 12, 24, 48, 72],
            index=0,
            key="forecast_select"
        )
    
    # AI Recommendations - minimal
    with st.container():
        st.subheader("AI Suggestions")
        ai_recommendations = generate_ai_recommendations()
        
        if ai_recommendations:
            for rec in ai_recommendations:
                color = "#F85149" if rec['type'] == "CRITICAL" else "#D29922"
                st.markdown(f"""
                <div class="ai-box" style="border-left-color: {color};">
                    <div><strong>{rec['department']}</strong> - {rec['message']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No critical issues detected.")
    
    # Hospital KPIs - simplified
    st.markdown("---")
    st.subheader("Hospital KPIs")
    
    hospital_kpis = calculate_hospital_kpis()
    
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        occ_color = "#3FB950" if hospital_kpis['occupancy_rate'] < 70 else "#D29922" if hospital_kpis['occupancy_rate'] < 85 else "#F85149"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Occupancy Rate</div>
            <div class="kpi-val" style="color:{occ_color}">{hospital_kpis['occupancy_rate']:.1f}%</div>
            <div class="kpi-note">{hospital_kpis['occupied_beds']}/{hospital_kpis['total_beds']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[1]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Available Beds</div>
            <div class="kpi-val" style="color:#3FB950">{hospital_kpis['available_beds']}</div>
            <div class="kpi-note">Total capacity</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[2]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Ready for Discharge</div>
            <div class="kpi-val" style="color:#3FB950">{hospital_kpis['ready_to_discharge']}</div>
            <div class="kpi-note">Patients</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[3]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Delayed Discharge</div>
            <div class="kpi-val" style="color:#F85149">{hospital_kpis['delayed_discharge']}</div>
            <div class="kpi-note">Patients</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Department Status - optimized
    st.markdown("---")
    st.subheader("Department Status")
    
    # Use tabs instead of all cards at once
    dept_tabs = st.tabs(list(DEPARTMENTS.keys()))
    
    for idx, (dept_name, tab) in enumerate(zip(DEPARTMENTS.keys(), dept_tabs)):
        with tab:
            status = get_department_status(dept_name, forecast_hours)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Total Beds:** {status['total_beds']}")
                st.markdown(f"**Occupied:** {status['occupied']}")
                st.markdown(f"**Available:** {status['available']}")
                st.markdown(f"**Occupancy Rate:** {status['occupancy_rate']:.1f}%")
            
            with col2:
                st.markdown(f"**Status:** <span style='color:{status['status_color']}'>{status['status_text']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Ready for Discharge:** {status['ready_to_discharge']}")
    
    # Simple chart
    st.markdown("---")
    st.subheader("Occupancy Overview")
    
    # Prepare chart data
    dept_names = list(DEPARTMENTS.keys())
    occupancy_rates = [get_department_status(dept)['occupancy_rate'] for dept in dept_names]
    
    chart_df = pd.DataFrame({
        'Department': dept_names,
        'Occupancy Rate': occupancy_rates
    })
    
    fig = px.bar(
        chart_df,
        x='Department',
        y='Occupancy Rate',
        title='Department Occupancy Rates',
        color='Occupancy Rate',
        color_continuous_scale=['#3FB950', '#D29922', '#F85149']
    )
    
    fig.update_layout(
        plot_bgcolor='#0D1117',
        paper_bgcolor='#0D1117',
        font_color='white',
        height=300,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 6. Admission Management - Simplified
# ---------------------------------------------------------
elif menu == "Admission Management":
    st.title("Admission Management")
    
    tab1, tab2 = st.tabs(["Current Patients", "Add New"])
    
    with tab1:
        # Display current patients
        current_df = st.session_state.patients_df[
            st.session_state.patients_df['Actual_Discharge_Date'].isna()
        ]
        
        if not current_df.empty:
            # Simplified display
            display_cols = ['PIN', 'Department', 'Room', 'Bed', 'Status', 'Admission_Date']
            st.dataframe(current_df[display_cols], use_container_width=True)
            
            # Quick actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Refresh Data", key="refresh_data"):
                    st.session_state.last_update = datetime.now()
                    st.rerun()
            
            with col2:
                if st.button("Export to CSV", key="export_csv"):
                    csv = current_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="current_patients.csv",
                        mime="text/csv"
                    )
        else:
            st.info("No current patients")
    
    with tab2:
        # Simplified admission form
        with st.form("simple_admission"):
            col1, col2 = st.columns(2)
            
            with col1:
                pin = st.selectbox("Patient ID", st.session_state.patient_db['PIN'].tolist())
                dept = st.selectbox("Department", list(DEPARTMENTS.keys()))
                room = st.text_input("Room Number", "RM-101")
                bed = st.text_input("Bed Number", "B1")
            
            with col2:
                admission_date = st.date_input("Admission Date", datetime.now().date())
                source = st.selectbox("Admission Source", ["Emergency", "Elective", "Transfer"])
                status = st.selectbox("Status", ["Active", "Ready for Discharge"])
            
            if st.form_submit_button("Admit Patient"):
                new_patient = {
                    "PIN": pin,
                    "Department": dept,
                    "Room": room,
                    "Bed": bed,
                    "Admission_Date": admission_date,
                    "Admission_Time": datetime.now().time(),
                    "Admission_Source": source,
                    "Expected_Discharge_Date": (datetime.now() + timedelta(days=3)).date(),
                    "Expected_Discharge_Time": datetime.now().time(),
                    "Actual_Discharge_Date": None,
                    "Actual_Discharge_Time": None,
                    "Status": status,
                    "Gender": st.session_state.patient_db[st.session_state.patient_db['PIN'] == pin].iloc[0]['Gender']
                }
                
                st.session_state.patients_df = pd.concat([
                    st.session_state.patients_df,
                    pd.DataFrame([new_patient])
                ], ignore_index=True)
                
                st.success("Patient admitted successfully!")
                st.session_state.last_update = datetime.now()
                time.sleep(1)
                st.rerun()

# ---------------------------------------------------------
# 7. KPIs Page - Simplified
# ---------------------------------------------------------
elif menu == "KPIs":
    st.title("Key Performance Indicators")
    
    hospital_kpis = calculate_hospital_kpis()
    
    # Main KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Bed Occupancy Rate", f"{hospital_kpis['occupancy_rate']:.1f}%")
    
    with col2:
        st.metric("Available Beds", hospital_kpis['available_beds'])
    
    with col3:
        st.metric("Net Flow", hospital_kpis['net_flow'])
    
    # Department breakdown
    st.markdown("---")
    st.subheader("Department Breakdown")
    
    for dept_name in DEPARTMENTS.keys():
        status = get_department_status(dept_name)
        
        with st.expander(f"{dept_name} ({status['occupied']}/{status['total_beds']})"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Occupancy", f"{status['occupancy_rate']:.1f}%")
            with col_b:
                st.metric("Available", status['available'])
            with col_c:
                st.metric("Status", status['status_text'])

# ---------------------------------------------------------
# 8. Settings Page
# ---------------------------------------------------------
elif menu == "Settings":
    st.title("Settings")
    
    st.info("System Configuration")
    
    # Simple settings
    st.subheader("Data Management")
    
    if st.button("Clear All Data", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("All data cleared. Refresh the page.")
        time.sleep(2)
        st.rerun()
    
    st.subheader("About")
    st.markdown("""
    **OccupyBed AI Pro v2.0**
    
    A smart hospital bed management system that transforms
    management from reactive to proactive.
    
    - Real-time bed occupancy tracking
    - AI-powered recommendations
    - Forecasting and analytics
    - Gender-based department allocation
    """)
    
    st.markdown("---")
    st.caption(f"Last data update: {st.session_state.last_update}")
