import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import time
import os
import io
from io import BytesIO

# ---------------------------------------------------------
# 1. Page Settings and Advanced Design
# ---------------------------------------------------------
st.set_page_config(page_title="OccupyBed AI Pro | Bed Management System", layout="wide")

st.markdown("""
<style>
    /* Global Dark Theme */
    .stApp { background-color: #0E1117; color: #E6EDF3; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363D; }

    /* 1. AI Command Board */
    .ai-box {
        background: linear-gradient(90deg, #161B22 0%, #0D1117 100%);
        border: 1px solid #30363D; border-left: 6px solid #A371F7;
        border-radius: 8px; padding: 20px; margin-bottom: 20px;
    }
    .ai-header { color: #A371F7; font-weight: bold; font-size: 18px; display: flex; justify-content: space-between; }
    .ai-rec { color: #E6EDF3; font-size: 15px; margin-top: 10px; font-weight: 500; }
    .ai-risk { color: #F85149; font-size: 13px; margin-top: 5px; }

    /* 2. KPI Indicators */
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

    /* 3. Department Cards */
    .dept-card {
        background-color: #0D1117; border: 1px solid #30363D; border-radius: 6px;
        padding: 15px; margin-bottom: 12px; position: relative;
    }
    .dept-head { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262D; padding-bottom: 8px; margin-bottom: 8px; }
    .dept-name { font-size: 15px; font-weight: 700; color: #E6EDF3; }
    .dept-metrics { display: flex; justify-content: space-between; font-size: 12px; color: #8B949E; }
    .gender-badge { background: #21262D; padding: 2px 6px; border-radius: 4px; color: #C9D1D9; font-size: 10px; }
    .overflow-alert { color: #D29922; font-size: 11px; margin-top: 6px; font-style: italic; }

    /* 4. Forecast Box */
    .forecast-box {
        background: linear-gradient(135deg, #0D1117 0%, #161B22 100%);
        border: 1px solid #30363D; border-radius: 8px;
        padding: 20px; margin-bottom: 20px;
    }
    
    /* 5. Patient Database */
    .patient-db {
        background-color: #0D1117;
        border: 1px solid #30363D;
        border-radius: 6px;
        padding: 10px;
        font-size: 12px;
        margin-bottom: 10px;
    }

    /* Custom Inputs */
    div[data-baseweb="select"] > div, input { background-color: #0D1117 !important; border-color: #30363D !important; color: white !important; }
    
    /* 6. Chart Container */
    .chart-container {
        background-color: #0D1117;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    /* Status indicators */
    .status-green { color: #3FB950; }
    .status-yellow { color: #D29922; }
    .status-red { color: #F85149; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Internal Patient Database
# ---------------------------------------------------------
def init_patient_database():
    """Initialize patient database with PIN and Gender"""
    if 'patient_db' not in st.session_state:
        # Create mock patient data
        patients = []
        for i in range(1, 101):
            patient_id = f"P{str(i).zfill(3)}"
            gender = "Male" if i % 2 == 0 else "Female"
            patients.append({"PIN": patient_id, "Gender": gender})
        
        # Add some special cases
        special_patients = [
            {"PIN": "P101", "Gender": "Male"},
            {"PIN": "P102", "Gender": "Female"},
            {"PIN": "P103", "Gender": "Male"},
            {"PIN": "P104", "Gender": "Female"},
            {"PIN": "P105", "Gender": "Male"},
        ]
        patients.extend(special_patients)
        
        st.session_state.patient_db = pd.DataFrame(patients)

def get_patient_gender(pin):
    """Retrieve patient gender based on PIN"""
    if 'patient_db' in st.session_state:
        patient = st.session_state.patient_db[st.session_state.patient_db['PIN'] == pin]
        if not patient.empty:
            return patient.iloc[0]['Gender']
    return None

# ---------------------------------------------------------
# 3. Department, Room, and Bed Definitions
# ---------------------------------------------------------
DEPARTMENTS = {
    "Medical - Male": {
        "capacity": 50,
        "gender": "Male",
        "rooms": [f"M-M-{i}" for i in range(101, 126)],
        "beds_per_room": 2,
        "color": "#3FB950"
    },
    "Medical - Female": {
        "capacity": 50,
        "gender": "Female",
        "rooms": [f"M-F-{i}" for i in range(201, 226)],
        "beds_per_room": 2,
        "color": "#A371F7"
    },
    "Surgical - Male": {
        "capacity": 40,
        "gender": "Male",
        "rooms": [f"S-M-{i}" for i in range(301, 321)],
        "beds_per_room": 2,
        "color": "#1F6FEB"
    },
    "Surgical - Female": {
        "capacity": 40,
        "gender": "Female",
        "rooms": [f"S-F-{i}" for i in range(401, 421)],
        "beds_per_room": 2,
        "color": "#FF7B72"
    },
    "ICU": {
        "capacity": 16,
        "gender": "Mixed",
        "rooms": [f"ICU-{i}" for i in range(1, 9)],
        "beds_per_room": 2,
        "color": "#FFA657"
    },
    "Pediatric": {
        "capacity": 30,
        "gender": "Mixed",
        "rooms": [f"PED-{i}" for i in range(501, 516)],
        "beds_per_room": 2,
        "color": "#7EE787"
    },
    "Obstetrics and Gynecology": {
        "capacity": 24,
        "gender": "Female",
        "rooms": [f"OBG-{i}" for i in range(601, 613)],
        "beds_per_room": 2,
        "color": "#D2A8FF"
    }
}

# Create list of all beds
def generate_all_beds():
    beds = {}
    for dept_name, dept_info in DEPARTMENTS.items():
        beds[dept_name] = []
        for room in dept_info['rooms']:
            for bed_num in range(1, dept_info['beds_per_room'] + 1):
                beds[dept_name].append(f"{room}-B{bed_num}")
    return beds

ALL_BEDS = generate_all_beds()

# ---------------------------------------------------------
# 4. Main Data Initialization
# ---------------------------------------------------------
def init_main_data():
    """Initialize main patient data"""
    if 'patients_df' not in st.session_state:
        # Create empty DataFrame with required columns
        columns = [
            "PIN", "Department", "Room", "Bed", "Admission_Date", 
            "Admission_Time", "Admission_Source", "Expected_Discharge_Date",
            "Expected_Discharge_Time", "Actual_Discharge_Date", 
            "Actual_Discharge_Time", "Status", "Gender"
        ]
        st.session_state.patients_df = pd.DataFrame(columns=columns)
        
        # Add some mock data for simulation
        sample_data = []
        now = datetime.now()
        
        for i in range(20):
            dept = np.random.choice(list(DEPARTMENTS.keys()))
            dept_info = DEPARTMENTS[dept]
            
            # Select available room and bed
            available_beds = [bed for bed in ALL_BEDS[dept] 
                            if bed not in st.session_state.patients_df['Bed'].values if 'Bed' in st.session_state.patients_df.columns]
            if available_beds:
                bed = np.random.choice(available_beds)
                room = bed.split('-B')[0]
            else:
                continue
            
            # Create random PIN
            pin = f"P{np.random.randint(1, 106):03d}"
            gender = get_patient_gender(pin) or np.random.choice(["Male", "Female"])
            
            # Admission and discharge dates
            admit_date = (now - timedelta(days=np.random.randint(0, 7))).date()
            admit_time = datetime.now().time()
            
            exp_discharge_date = (now + timedelta(days=np.random.randint(1, 10))).date()
            exp_discharge_time = datetime.now().time()
            
            # Admission source
            sources = ["Emergency", "Elective", "Transfer"]
            admission_source = np.random.choice(sources)
            
            # Status
            status_options = ["Active", "Ready for Discharge", "Delayed Discharge"]
            weights = [0.7, 0.2, 0.1]
            status = np.random.choice(status_options, p=weights)
            
            sample_data.append({
                "PIN": pin,
                "Department": dept,
                "Room": room,
                "Bed": bed,
                "Admission_Date": admit_date,
                "Admission_Time": admit_time,
                "Admission_Source": admission_source,
                "Expected_Discharge_Date": exp_discharge_date,
                "Expected_Discharge_Time": exp_discharge_time,
                "Actual_Discharge_Date": None,
                "Actual_Discharge_Time": None,
                "Status": status,
                "Gender": gender
            })
        
        if sample_data:
            st.session_state.patients_df = pd.DataFrame(sample_data)

# ---------------------------------------------------------
# 5. Helper Functions
# ---------------------------------------------------------
def get_department_status(dept_name, forecast_hours=6):
    """Get department status with forecasts"""
    dept_info = DEPARTMENTS[dept_name]
    
    # Current patients in department
    current_patients = st.session_state.patients_df[
        (st.session_state.patients_df['Department'] == dept_name) &
        (st.session_state.patients_df['Actual_Discharge_Date'].isna())
    ]
    
    # Calculate indicators
    total_beds = dept_info['capacity']
    occupied = len(current_patients)
    available = total_beds - occupied
    occupancy_rate = (occupied / total_beds) * 100 if total_beds > 0 else 0
    
    # Patients ready for discharge within specified period
    now = datetime.now()
    forecast_cutoff = now + timedelta(hours=forecast_hours)
    
    ready_to_discharge = current_patients[
        (current_patients['Status'] == 'Ready for Discharge') |
        (
            (current_patients['Expected_Discharge_Date'].notna()) &
            (pd.to_datetime(current_patients['Expected_Discharge_Date']) <= forecast_cutoff)
        )
    ].shape[0]
    
    # Patients with delayed discharge
    delayed_discharge = current_patients[
        (current_patients['Status'] == 'Delayed Discharge') |
        (
            (current_patients['Expected_Discharge_Date'].notna()) &
            (pd.to_datetime(current_patients['Expected_Discharge_Date']) < now)
        )
    ].shape[0]
    
    # Determine status color
    if occupancy_rate < 70:
        status_color = "#3FB950"
        status_text = "SAFE"
    elif occupancy_rate < 85:
        status_color = "#D29922"
        status_text = "WARNING"
    else:
        status_color = "#F85149"
        status_text = "CRITICAL"
    
    # Gender mismatch
    gender_mismatch = 0
    if dept_info['gender'] != 'Mixed':
        gender_mismatch = current_patients[
            current_patients['Gender'] != dept_info['gender']
        ].shape[0]
    
    return {
        "department": dept_name,
        "total_beds": total_beds,
        "occupied": occupied,
        "available": available,
        "occupancy_rate": occupancy_rate,
        "ready_to_discharge": ready_to_discharge,
        "delayed_discharge": delayed_discharge,
        "status_color": status_color,
        "status_text": status_text,
        "gender_mismatch": gender_mismatch,
        "current_patients": current_patients
    }

def get_available_beds(dept_name):
    """Get available beds in a specific department"""
    occupied_beds = st.session_state.patients_df[
        (st.session_state.patients_df['Department'] == dept_name) &
        (st.session_state.patients_df['Actual_Discharge_Date'].isna())
    ]['Bed'].tolist()
    
    return [bed for bed in ALL_BEDS[dept_name] if bed not in occupied_beds]

def generate_ai_recommendations():
    """Generate AI recommendations based on current status"""
    recommendations = []
    
    # Analyze all departments
    for dept_name in DEPARTMENTS.keys():
        status = get_department_status(dept_name)
        
        if status['occupancy_rate'] >= 85:
            recommendations.append({
                "department": dept_name,
                "type": "CRITICAL",
                "message": f"High occupancy detected in {dept_name}. Consider accelerating discharge for stable patients.",
                "priority": 1
            })
        
        if status['delayed_discharge'] > 3:
            recommendations.append({
                "department": dept_name,
                "type": "WARNING",
                "message": f"High delayed discharge rate detected in {dept_name}. Review pending discharge approvals and coordination.",
                "priority": 2
            })
        
        if status['occupancy_rate'] < 50 and status['available'] > 10:
            recommendations.append({
                "department": dept_name,
                "type": "INFO",
                "message": f"Available capacity detected in {dept_name}. Elective admissions can proceed safely.",
                "priority": 3
            })
        
        if status['gender_mismatch'] > 0:
            recommendations.append({
                "department": dept_name,
                "type": "WARNING",
                "message": f"Gender mismatch detected in {dept_name}. Consider patient transfer to appropriate department.",
                "priority": 2
            })
    
    # Sort by priority
    recommendations.sort(key=lambda x: x['priority'])
    return recommendations[:5]  # Return top 5 recommendations

def calculate_hospital_kpis():
    """Calculate hospital-level KPIs"""
    total_capacity = sum(dept['capacity'] for dept in DEPARTMENTS.values())
    
    current_patients = st.session_state.patients_df[
        st.session_state.patients_df['Actual_Discharge_Date'].isna()
    ]
    
    total_occupied = len(current_patients)
    occupancy_rate = (total_occupied / total_capacity) * 100
    
    # Net flow (today)
    today = datetime.now().date()
    admissions_today = st.session_state.patients_df[
        pd.to_datetime(st.session_state.patients_df['Admission_Date']) == pd.Timestamp(today)
    ].shape[0]
    
    discharges_today = st.session_state.patients_df[
        (pd.to_datetime(st.session_state.patients_df['Actual_Discharge_Date']) == pd.Timestamp(today))
    ].shape[0]
    
    net_flow = admissions_today - discharges_today
    
    # Average Length of Stay (ALOS)
    if not current_patients.empty:
        current_patients['Admission_Datetime'] = pd.to_datetime(
            current_patients['Admission_Date'].astype(str) + ' ' + 
            current_patients['Admission_Time'].astype(str)
        )
        los_days = (datetime.now() - current_patients['Admission_Datetime']).dt.total_seconds() / (24 * 3600)
        average_los = los_days.mean()
    else:
        average_los = 0
    
    return {
        "total_beds": total_capacity,
        "occupied_beds": total_occupied,
        "available_beds": total_capacity - total_occupied,
        "occupancy_rate": occupancy_rate,
        "admissions_today": admissions_today,
        "discharges_today": discharges_today,
        "net_flow": net_flow,
        "average_los": average_los,
        "ready_to_discharge": current_patients[current_patients['Status'] == 'Ready for Discharge'].shape[0],
        "delayed_discharge": current_patients[current_patients['Status'] == 'Delayed Discharge'].shape[0]
    }

# ---------------------------------------------------------
# 6. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## OccupyBed AI Pro")
    st.markdown("---")
    
    menu = st.radio(
        "Main Menu",
        ["Dashboard", "Admission Management", "Performance Indicators (KPIs)", "Settings & Files"]
    )
    
    st.markdown("---")
    
    # Data update status
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    st.caption(f"Last Update: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # File upload option
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            # Read uploaded file
            df_uploaded = pd.read_excel(uploaded_file)
            
            # Verify required columns
            required_columns = ['PIN', 'Department', 'Room', 'Bed']
            if all(col in df_uploaded.columns for col in required_columns):
                st.session_state.patients_df = df_uploaded
                st.session_state.last_update = datetime.now()
                st.success("Data updated successfully!")
                st.rerun()
            else:
                st.error("File does not contain required columns")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # File download option
    st.markdown("---")
    if st.button("Download Current Data"):
        # Create Excel file for download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.patients_df.to_excel(writer, index=False, sheet_name='Patients')
        
        output.seek(0)
        
        st.download_button(
            label="Click to Download File",
            data=output,
            file_name=f"occupybed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ---------------------------------------------------------
# 7. Initialize All Data
# ---------------------------------------------------------
init_patient_database()
init_main_data()

# ---------------------------------------------------------
# 8. Dashboard Page
# ---------------------------------------------------------
if menu == "Dashboard":
    st.title("Dashboard - Overview")
    
    # --- Forecast and Control Section ---
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Forecast Window")
    
    with col2:
        forecast_options = {
            "6 hours": 6,
            "12 hours": 12,
            "24 hours": 24,
            "48 hours": 48,
            "72 hours": 72,
            "Custom": "custom"
        }
        
        selected_forecast = st.selectbox(
            "Select Forecast Duration:",
            list(forecast_options.keys())
        )
        
        forecast_hours = forecast_options[selected_forecast]
        
        if forecast_hours == "custom":
            forecast_hours = st.number_input(
                "Number of Hours:",
                min_value=1,
                max_value=168,
                value=24,
                step=1
            )
    
    # --- AI Recommendations ---
    st.markdown("---")
    st.subheader("AI Suggested Actions")
    
    ai_recommendations = generate_ai_recommendations()
    
    for rec in ai_recommendations:
        color_map = {
            "CRITICAL": "#F85149",
            "WARNING": "#D29922",
            "INFO": "#3FB950"
        }
        
        st.markdown(f"""
        <div class="ai-box" style="border-left-color: {color_map[rec['type']]};">
            <div class="ai-header">
                <span>{rec['department']}</span>
                <span style="color:{color_map[rec['type']]}; border:1px solid {color_map[rec['type']]}; padding:2px 8px; border-radius:4px;">
                    {rec['type']}
                </span>
            </div>
            <div class="ai-rec">{rec['message']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Hospital General Indicators ---
    st.markdown("---")
    st.subheader("Hospital General Indicators")
    
    hospital_kpis = calculate_hospital_kpis()
    
    kpi_cols = st.columns(5)
    
    with kpi_cols[0]:
        occ_color = "txt-green" if hospital_kpis['occupancy_rate'] < 70 else "txt-yellow" if hospital_kpis['occupancy_rate'] < 85 else "txt-red"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Occupancy Rate</div>
            <div class="kpi-val {occ_color}">{hospital_kpis['occupancy_rate']:.1f}%</div>
            <div class="kpi-note">{hospital_kpis['occupied_beds']}/{hospital_kpis['total_beds']} beds</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[1]:
        flow_color = "txt-green" if hospital_kpis['net_flow'] <= 0 else "txt-red"
        flow_sign = "+" if hospital_kpis['net_flow'] > 0 else ""
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Net Flow</div>
            <div class="kpi-val {flow_color}">{flow_sign}{hospital_kpis['net_flow']}</div>
            <div class="kpi-note">Admissions: {hospital_kpis['admissions_today']} | Discharges: {hospital_kpis['discharges_today']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[2]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Average Length of Stay</div>
            <div class="kpi-val txt-yellow">{hospital_kpis['average_los']:.1f} days</div>
            <div class="kpi-note">ALOS</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[3]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Ready for Discharge</div>
            <div class="kpi-val txt-green">{hospital_kpis['ready_to_discharge']}</div>
            <div class="kpi-note">patients</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[4]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Delayed Discharge</div>
            <div class="kpi-val txt-red">{hospital_kpis['delayed_discharge']}</div>
            <div class="kpi-note">patients</div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Department Status ---
    st.markdown("---")
    st.subheader("Department Status")
    
    # Display departments in columns
    dept_cols = st.columns(2)
    
    for idx, dept_name in enumerate(DEPARTMENTS.keys()):
        col_idx = idx % 2
        with dept_cols[col_idx]:
            dept_status = get_department_status(dept_name, forecast_hours)
            
            # Create department card
            status_badge = f"<span style='color:{dept_status['status_color']}; font-weight:bold;'>{dept_status['status_text']}</span>"
            
            st.markdown(f"""
            <div class="dept-card">
                <div class="dept-head">
                    <span class="dept-name">{dept_name}</span>
                    {status_badge}
                </div>
                
                <div class="dept-metrics">
                    <span>Total: <b>{dept_status['total_beds']}</b></span>
                    <span>Occupied: <b>{dept_status['occupied']}</b></span>
                    <span>Available: <b style="color:#3FB950">{dept_status['available']}</b></span>
                </div>
                
                <div style="margin: 10px 0; background: #21262D; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="width: {min(dept_status['occupancy_rate'], 100)}%; height: 100%; background: {DEPARTMENTS[dept_name]['color']};"></div>
                </div>
                
                <div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 10px;">
                    <div>
                        <div>Ready for Discharge (within {forecast_hours} hours):</div>
                        <div style="color: #3FB950; font-weight: bold; font-size: 14px;">{dept_status['ready_to_discharge']} beds</div>
                    </div>
                    <div style="text-align: right;">
                        <div>Occupancy Rate:</div>
                        <div style="color: #E6EDF3; font-weight: bold; font-size: 14px;">{dept_status['occupancy_rate']:.1f}%</div>
                    </div>
                </div>
                
                {f'<div style="color: #F85149; font-size: 11px; margin-top: 8px;">Gender Mismatch: {dept_status["gender_mismatch"]} cases</div>' if dept_status["gender_mismatch"] > 0 else ''}
            </div>
            """, unsafe_allow_html=True)
    
    # --- Forecast Charts ---
    st.markdown("---")
    st.subheader("Forecast Charts")
    
    # Create data for charts
    forecast_data = []
    time_points = [6, 12, 24, 48, 72]
    
    for hours in time_points:
        total_expected = 0
        for dept_name in DEPARTMENTS.keys():
            dept_status = get_department_status(dept_name, hours)
            total_expected += dept_status['ready_to_discharge']
        
        forecast_data.append({
            "hours": hours,
            "expected_beds": total_expected,
            "occupancy_rate": hospital_kpis['occupancy_rate'] - (total_expected / hospital_kpis['total_beds'] * 100)
        })
    
    forecast_df = pd.DataFrame(forecast_data)
    
    # Create charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        fig1 = px.line(
            forecast_df, 
            x='hours', 
            y='expected_beds',
            title=f'Expected Beds in Coming Hours',
            labels={'hours': 'Hours', 'expected_beds': 'Expected Beds'}
        )
        fig1.update_layout(
            plot_bgcolor='#0D1117',
            paper_bgcolor='#0D1117',
            font_color='white',
            height=300
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        fig2 = px.line(
            forecast_df, 
            x='hours', 
            y='occupancy_rate',
            title='Expected Occupancy Rate',
            labels={'hours': 'Hours', 'occupancy_rate': 'Occupancy Rate %'}
        )
        fig2.update_layout(
            plot_bgcolor='#0D1117',
            paper_bgcolor='#0D1117',
            font_color='white',
            height=300
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 9. Admission Management Page
# ---------------------------------------------------------
elif menu == "Admission Management":
    st.title("Admission and Discharge Management")
    
    # Tabs
    tab1, tab2 = st.tabs(["Add New Case", "Manage Current Cases"])
    
    with tab1:
        st.subheader("Add New Admission Case")
        
        with st.form("admission_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Select PIN
                pin_options = st.session_state.patient_db['PIN'].tolist()
                selected_pin = st.selectbox("Patient ID (PIN):", pin_options)
                
                # Display patient gender automatically
                if selected_pin:
                    patient_gender = get_patient_gender(selected_pin)
                    if patient_gender:
                        st.info(f"Patient Gender: {patient_gender}")
                
                # Select department (filtered by gender)
                if patient_gender:
                    # Filter suitable departments by gender
                    suitable_depts = []
                    for dept_name, dept_info in DEPARTMENTS.items():
                        if dept_info['gender'] == 'Mixed' or dept_info['gender'] == patient_gender:
                            suitable_depts.append(dept_name)
                    
                    selected_dept = st.selectbox("Department:", suitable_depts)
                else:
                    selected_dept = st.selectbox("Department:", list(DEPARTMENTS.keys()))
                
                # Select room and bed
                if selected_dept:
                    available_beds = get_available_beds(selected_dept)
                    if available_beds:
                        selected_bed = st.selectbox("Room and Bed:", available_beds)
                        selected_room = selected_bed.split('-B')[0]
                    else:
                        st.warning("No beds available in this department")
                        selected_bed = None
                        selected_room = None
            
            with col2:
                # Admission date and time
                admission_date = st.date_input("Admission Date:", datetime.now().date())
                admission_time = st.time_input("Admission Time:", datetime.now().time())
                
                # Admission source
                admission_source = st.selectbox(
                    "Admission Source:",
                    ["Emergency", "Elective", "Transfer"]
                )
                
                # Expected discharge date
                exp_discharge_date = st.date_input("Expected Discharge Date:", 
                                                  datetime.now().date() + timedelta(days=3))
                exp_discharge_time = st.time_input("Expected Discharge Time:", datetime.now().time())
            
            # Submit button
            submitted = st.form_submit_button("Save Case")
            
            if submitted and selected_pin and selected_dept and selected_bed:
                # Add new case
                new_patient = {
                    "PIN": selected_pin,
                    "Department": selected_dept,
                    "Room": selected_room,
                    "Bed": selected_bed,
                    "Admission_Date": admission_date,
                    "Admission_Time": admission_time,
                    "Admission_Source": admission_source,
                    "Expected_Discharge_Date": exp_discharge_date,
                    "Expected_Discharge_Time": exp_discharge_time,
                    "Actual_Discharge_Date": None,
                    "Actual_Discharge_Time": None,
                    "Status": "Active",
                    "Gender": patient_gender
                }
                
                # Add to DataFrame
                st.session_state.patients_df = pd.concat(
                    [st.session_state.patients_df, pd.DataFrame([new_patient])],
                    ignore_index=True
                )
                
                st.success("Case added successfully!")
                st.session_state.last_update = datetime.now()
                time.sleep(1)
                st.rerun()
    
    with tab2:
        st.subheader("Current Cases")
        
        # Display data
        current_patients = st.session_state.patients_df[
            st.session_state.patients_df['Actual_Discharge_Date'].isna()
        ]
        
        if not current_patients.empty:
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_dept = st.selectbox(
                    "Filter by Department:",
                    ["All"] + list(DEPARTMENTS.keys())
                )
            
            with col2:
                filter_status = st.selectbox(
                    "Filter by Status:",
                    ["All", "Active", "Ready for Discharge", "Delayed Discharge"]
                )
            
            # Apply filters
            filtered_df = current_patients.copy()
            if filter_dept != "All":
                filtered_df = filtered_df[filtered_df['Department'] == filter_dept]
            
            if filter_status != "All":
                filtered_df = filtered_df[filtered_df['Status'] == filter_status]
            
            # Display data
            st.dataframe(
                filtered_df[['PIN', 'Department', 'Room', 'Bed', 'Status', 'Admission_Date']],
                use_container_width=True,
                hide_index=True
            )
            
            # Patient status update option
            st.subheader("Update Patient Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                patient_to_update = st.selectbox(
                    "Select Patient:",
                    filtered_df['PIN'].tolist()
                )
            
            with col2:
                new_status = st.selectbox(
                    "New Status:",
                    ["Active", "Ready for Discharge", "Delayed Discharge"]
                )
            
            with col3:
                if st.button("Update Status"):
                    # Update status
                    idx = st.session_state.patients_df[
                        st.session_state.patients_df['PIN'] == patient_to_update
                    ].index
                    
                    if len(idx) > 0:
                        st.session_state.patients_df.loc[idx[0], 'Status'] = new_status
                        st.success("Status updated!")
                        st.session_state.last_update = datetime.now()
                        time.sleep(1)
                        st.rerun()
            
            # Patient discharge option
            st.subheader("Record Patient Discharge")
            
            col1, col2 = st.columns(2)
            
            with col1:
                patient_to_discharge = st.selectbox(
                    "Select Patient for Discharge:",
                    current_patients['PIN'].tolist(),
                    key="discharge_select"
                )
            
            with col2:
                actual_discharge_date = st.date_input(
                    "Actual Discharge Date:",
                    datetime.now().date(),
                    key="discharge_date"
                )
                actual_discharge_time = st.time_input(
                    "Actual Discharge Time:",
                    datetime.now().time(),
                    key="discharge_time"
                )
            
            if st.button("Record Discharge"):
                # Record discharge
                idx = st.session_state.patients_df[
                    st.session_state.patients_df['PIN'] == patient_to_discharge
                ].index
                
                if len(idx) > 0:
                    st.session_state.patients_df.loc[idx[0], 'Actual_Discharge_Date'] = actual_discharge_date
                    st.session_state.patients_df.loc[idx[0], 'Actual_Discharge_Time'] = actual_discharge_time
                    st.success("Discharge recorded successfully!")
                    st.session_state.last_update = datetime.now()
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("No current cases")

# ---------------------------------------------------------
# 10. Performance Indicators (KPIs) Page
# ---------------------------------------------------------
elif menu == "Performance Indicators (KPIs)":
    st.title("Key Performance Indicators (KPIs)")
    
    # Hospital Level
    st.subheader("Hospital Level KPIs")
    
    hospital_kpis = calculate_hospital_kpis()
    
    kpi_cols = st.columns(4)
    
    kpi_metrics = [
        {
            "title": "Bed Occupancy Rate (BOR)",
            "value": f"{hospital_kpis['occupancy_rate']:.1f}%",
            "description": f"{hospital_kpis['occupied_beds']}/{hospital_kpis['total_beds']}",
            "color": "txt-green" if hospital_kpis['occupancy_rate'] < 70 else "txt-yellow" if hospital_kpis['occupancy_rate'] < 85 else "txt-red"
        },
        {
            "title": "Average Length of Stay (ALOS)",
            "value": f"{hospital_kpis['average_los']:.1f} days",
            "description": "Average admission days",
            "color": "txt-green" if hospital_kpis['average_los'] < 5 else "txt-yellow" if hospital_kpis['average_los'] < 8 else "txt-red"
        },
        {
            "title": "Bed Turnover Rate",
            "value": f"{(hospital_kpis['discharges_today'] / hospital_kpis['total_beds']):.2f}",
            "description": "Turns per bed",
            "color": "txt-green"
        },
        {
            "title": "Emergency Occupancy Rate",
            "value": "78.5%",
            "description": "From incoming cases",
            "color": "txt-yellow"
        }
    ]
    
    for i, kpi in enumerate(kpi_metrics):
        with kpi_cols[i]:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">{kpi['title']}</div>
                <div class="kpi-val {kpi['color']}">{kpi['value']}</div>
                <div class="kpi-note">{kpi['description']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Department Level
    st.markdown("---")
    st.subheader("Department Level KPIs")
    
    selected_dept = st.selectbox(
        "Select Department:",
        list(DEPARTMENTS.keys())
    )
    
    if selected_dept:
        dept_status = get_department_status(selected_dept, 24)
        dept_info = DEPARTMENTS[selected_dept]
        
        # Calculate additional department indicators
        dept_patients = dept_status['current_patients']
        
        if not dept_patients.empty:
            # Calculate ALOS for department
            dept_patients['Admission_Datetime'] = pd.to_datetime(
                dept_patients['Admission_Date'].astype(str) + ' ' + 
                dept_patients['Admission_Time'].astype(str)
            )
            los_days = (datetime.now() - dept_patients['Admission_Datetime']).dt.total_seconds() / (24 * 3600)
            dept_alos = los_days.mean()
        else:
            dept_alos = 0
        
        # Display department KPIs
        dept_kpi_cols = st.columns(4)
        
        dept_kpis = [
            {
                "title": "Department Occupancy Rate",
                "value": f"{dept_status['occupancy_rate']:.1f}%",
                "color": "txt-green" if dept_status['occupancy_rate'] < 70 else "txt-yellow" if dept_status['occupancy_rate'] < 85 else "txt-red"
            },
            {
                "title": "Average Length of Stay",
                "value": f"{dept_alos:.1f} days",
                "color": "txt-green" if dept_alos < 5 else "txt-yellow" if dept_alos < 8 else "txt-red"
            },
            {
                "title": "Delayed Discharge Rate",
                "value": f"{(dept_status['delayed_discharge'] / dept_status['total_beds'] * 100):.1f}%",
                "color": "txt-red" if dept_status['delayed_discharge'] > 3 else "txt-yellow" if dept_status['delayed_discharge'] > 1 else "txt-green"
            },
            {
                "title": "Current Admissions",
                "value": dept_status['occupied'],
                "color": "txt-yellow"
            }
        ]
        
        for i, kpi in enumerate(dept_kpis):
            with dept_kpi_cols[i]:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">{kpi['title']}</div>
                    <div class="kpi-val {kpi['color']}">{kpi['value']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Department analysis charts
        st.markdown("---")
        st.subheader(f"Department Analysis: {selected_dept}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Case distribution by status
            if not dept_patients.empty:
                status_dist = dept_patients['Status'].value_counts()
                fig1 = px.pie(
                    values=status_dist.values,
                    names=status_dist.index,
                    title="Case Distribution by Status",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig1.update_layout(
                    plot_bgcolor='#0D1117',
                    paper_bgcolor='#0D1117',
                    font_color='white',
                    height=300
                )
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Case distribution by admission source
            if not dept_patients.empty:
                source_dist = dept_patients['Admission_Source'].value_counts()
                fig2 = px.bar(
                    x=source_dist.index,
                    y=source_dist.values,
                    title="Case Distribution by Admission Source",
                    labels={'x': 'Admission Source', 'y': 'Number of Cases'}
                )
                fig2.update_layout(
                    plot_bgcolor='#0D1117',
                    paper_bgcolor='#0D1117',
                    font_color='white',
                    height=300
                )
                st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# 11. Settings and Files Page
# ---------------------------------------------------------
elif menu == "Settings & Files":
    st.title("Settings & Files")
    
    tab1, tab2, tab3 = st.tabs(["Patient Database", "System Management", "Data Export"])
    
    with tab1:
        st.subheader("Patient Database")
        
        # Display current database
        st.dataframe(
            st.session_state.patient_db,
            use_container_width=True,
            hide_index=True
        )
        
        # Add new patient
        st.subheader("Add New Patient")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_pin = st.text_input("New PIN (e.g., P106):")
        
        with col2:
            new_gender = st.selectbox("Gender:", ["Male", "Female"])
        
        if st.button("Add Patient") and new_pin:
            # Check for duplicate PIN
            if new_pin in st.session_state.patient_db['PIN'].values:
                st.error("This PIN already exists")
            else:
                # Add new patient
                new_patient = pd.DataFrame([{"PIN": new_pin, "Gender": new_gender}])
                st.session_state.patient_db = pd.concat(
                    [st.session_state.patient_db, new_patient],
                    ignore_index=True
                )
                st.success(f"Patient {new_pin} added successfully!")
                st.session_state.last_update = datetime.now()
                time.sleep(1)
                st.rerun()
    
    with tab2:
        st.subheader("System Management")
        
        # Reset data
        st.warning("Danger Zone - Data Reset")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Reset Patient Data", type="secondary"):
                del st.session_state.patients_df
                init_main_data()
                st.success("Patient data reset successfully")
                st.session_state.last_update = datetime.now()
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("Delete All Data", type="primary"):
                for key in ['patients_df', 'patient_db', 'last_update']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("All data deleted successfully")
                time.sleep(2)
                st.rerun()
        
        # System information
        st.markdown("---")
        st.subheader("System Information")
        
        info_cols = st.columns(2)
        
        with info_cols[0]:
            st.metric("Patients in Database", len(st.session_state.patient_db))
            st.metric("Departments", len(DEPARTMENTS))
        
        with info_cols[1]:
            st.metric("Total Beds", sum(dept['capacity'] for dept in DEPARTMENTS.values()))
            st.metric("Last Update", st.session_state.last_update.strftime("%Y-%m-%d %H:%M"))
    
    with tab3:
        st.subheader("Data Export")
        
        st.info("You can export data in different formats")
        
        # Export as Excel
        st.markdown("#### Export as Excel File")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_option = st.selectbox(
                "Select Data to Export:",
                ["All Data", "Current Patients Only", "Patient Database"]
            )
        
        with col2:
            if st.button("Export as Excel"):
                if export_option == "All Data":
                    data_to_export = st.session_state.patients_df
                elif export_option == "Current Patients Only":
                    data_to_export = st.session_state.patients_df[
                        st.session_state.patients_df['Actual_Discharge_Date'].isna()
                    ]
                else:
                    data_to_export = st.session_state.patient_db
                
                # Create file
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    data_to_export.to_excel(writer, index=False, sheet_name='Data')
                
                output.seek(0)
                
                # Download button
                st.download_button(
                    label="Click to Download File",
                    data=output,
                    file_name=f"occupybed_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Export as CSV
        st.markdown("---")
        st.markdown("#### Export as CSV File")
        
        if st.button("Export as CSV"):
            data_to_export = st.session_state.patients_df
            
            # Convert to CSV
            csv_data = data_to_export.to_csv(index=False)
            
            st.download_button(
                label="Download CSV File",
                data=csv_data,
                file_name=f"occupybed_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# ---------------------------------------------------------
# 12. Page Footer
# ---------------------------------------------------------
st.markdown("---")
footer_cols = st.columns(3)
with footer_cols[1]:
    st.caption("OccupyBed AI Pro v2.0 | Smart Hospital Bed Management System")
    st.caption("Transforming management from reactive to proactive")
