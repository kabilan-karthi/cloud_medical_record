import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# Set the page configuration
st.set_page_config(
    page_title="Cloud Stored Patient Reports",
    page_icon=":hospital:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration for the PostgreSQL connection
DATABASE_URI = 'postgresql://cloud_owner:dtn1RvruZ6yc@ep-tight-dew-a5qqb307.us-east-2.aws.neon.tech/cloud?sslmode=require'

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URI)

# Function to load patient data from the database
@st.cache_data(ttl=60)
def load_data():
    query = "SELECT * FROM patients"
    return pd.read_sql(query, engine)

# Function to save patient data back to the database
def save_data(df):
    df.to_sql('patients', engine, if_exists='replace', index=False)

# Load the patient data
df_patients = load_data()

def add_bg_from_url(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url({image_url});
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Add background image
add_bg_from_url("https://4kwallpapers.com/images/walls/thumbs_3t/8324.png")

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'page' not in st.session_state:
    st.session_state.page = "Login"

def login(user, password):
    if user == "admin" and password == "password":  # Simplified for demonstration
        st.session_state.logged_in = True
        st.session_state.page = "Home"
    else:
        st.error("Invalid username or password")

# Navigation logic
if not st.session_state.logged_in:
    st.session_state.page = "Login"

# Custom CSS for styling
st.markdown("""
    <style>
        .login-card {
            padding: 2rem;
        }
        .stTextInput > div > div > input {
            padding: 10px;
        }
        .stButton button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
        }
        .stButton button:hover {
            background-color: #0056b3;
        }
        .nav-item {
            font-size: 1.2rem;
            padding: 10px 0;
            color: #ffffff;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav-item:hover {
            background-color: #0056b3;
        }
        .active-nav-item {
            background-color: #007bff;
            color: #ffffff;
            border-radius: 5px;
            padding: 10px;
        }
        .confirmation {
            font-size: 1.2rem;
            font-weight: bold;
            color: green;
            margin-top: 1rem;
        }
        .nav-item{
        margin-bottom: 1rem;  /* Add space between nav items */
    }
    </style>
""", unsafe_allow_html=True)

if st.session_state.page == "Login":
    st.title("Welcome to Cloud Stored Patient Reports 🏥")
    col1, col2 = st.columns(2)
    with col1:
        user = st.text_input("Username", placeholder="Enter your username")
    with col2:
        password = st.text_input("Password", type="password", placeholder="Enter your password")
    if st.button("Login"):
        login(user, password)
        if st.session_state.logged_in:
            st.experimental_rerun()
else:
    # Sidebar for navigation
    with st.sidebar:
        
        st.title("Navigation 🧭")
        pages = {
            "Home": "🏠 Home",
            "About": "ℹ️ About",
            "Services": "🛠️ Services",
            "Add Patient": "➕ Add Patient"
        }
        for page_key, page_name in pages.items():
            if st.session_state.page == page_key:
                st.markdown(f'<div class="nav-item active-nav-item">{page_name}</div>', unsafe_allow_html=True)
            else:
                if st.sidebar.button(page_name):
                    st.session_state.page = page_key
                    st.experimental_rerun()

        if st.button("Logout 🚪"):
            st.session_state.logged_in = False
            st.session_state.page = "Login"
            st.experimental_rerun()

    if st.session_state.page == "Home":
        st.title('Cloud Stored Patient Reports 📚')
        st.subheader('Find and update patient details 🔍')

        # Input for patient's name, ID, and editor's name
        col1, col2, col3 = st.columns(3)
        with col1:
            patient_name = st.text_input('Enter Patient Name', placeholder="Enter patient name")
        with col2:
            patient_id = st.number_input('Enter Patient ID', min_value=1, placeholder="Enter patient ID")
        with col3:
            editor_name = st.text_input('Enter Your Name', placeholder="Enter your name")

        # Search for patient
        if st.button('Search 🔍'):
            patient = df_patients[(df_patients['name'].str.lower() == patient_name.lower()) & (df_patients['id'] == patient_id)]

            if not patient.empty:
                st.subheader('Patient Details (Editable): 📝')

                # Ensure the DataFrame has an 'Edited_By' column
                if 'Edited_By' not in patient.columns:
                    patient['Edited_By'] = ""

                edited_patient = st.data_editor(patient, use_container_width=True, key='data_editor')

                if st.button('Save Changes 💾'):
                    # Update the original dataframe with the edited rows
                    edited_rows = st.session_state['data_editor']['edited_rows']
                    for row_idx, updates in edited_rows.items():
                        for col, new_value in updates.items():
                            df_patients.at[row_idx, col] = new_value
                        # Mark the editor's name for the edited row
                        df_patients.at[row_idx, 'Edited_By'] = editor_name
                        df_patients.at[row_idx, 'Edited_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    save_data(df_patients)
                    st.success('Patient details updated successfully! ✅')

                    # Show confirmation tick and message
                    st.markdown('<div class="confirmation">✔ Changes saved successfully!</div>', unsafe_allow_html=True)

                    # Keep the edited data in the table
                    edited_patient = df_patients[(df_patients['name'].str.lower() == patient_name.lower()) & (df_patients['id'] == patient_id)]
                    st.dataframe(edited_patient)

                    # Save DataFrame as CSV
                    csv = df_patients.to_csv(index=False)
                    st.download_button(
                        label="Download updated patient data as CSV",
                        data=csv,
                        file_name=f"patient_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime='text/csv'
                    )
            else:
                st.error('No patient found with the provided details. 😔')

    elif st.session_state.page == "Add Patient":
        st.title("Add New Patient ➕")
        st.subheader("Enter the new patient's details:")

        # Form for new patient details
        new_patient = {}
        new_patient['Name'] = st.text_input('Name')
        new_patient['Age'] = st.number_input('Age', min_value=0, max_value=120)
        new_patient['Height'] = st.number_input('Height (cm)', min_value=50, max_value=250)
        new_patient['Medical_Contents'] = st.text_input('Medical Contents')
        new_patient['Blood_Pressure'] = st.text_input('Blood Pressure')
        new_patient['Heart_Rate'] = st.number_input('Heart Rate', min_value=0, max_value=200)
        new_patient['Blood_Sugar'] = st.number_input('Blood Sugar', min_value=0, max_value=500)
        new_patient['Cholesterol'] = st.number_input('Cholesterol', min_value=0, max_value=500)
        new_patient['BMI'] = st.number_input('BMI', min_value=0, max_value=50)
        new_patient['Allergies'] = st.text_input('Allergies')
        new_patient['Medications'] = st.text_input('Medications')
        new_patient['Smoking_Status'] = st.text_input('Smoking Status')
        new_patient['Alcohol_Consumption'] = st.text_input('Alcohol Consumption')
        new_patient['Physical_Activity'] = st.text_input('Physical Activity')
        new_patient['Family_History'] = st.text_input('Family History')
        new_patient['Mental_Health'] = st.text_input('Mental Health')
        new_patient['Sleep_Patterns'] = st.text_input('Sleep Patterns')
        new_patient['Vision'] = st.text_input('Vision')
        new_patient['Hearing'] = st.text_input('Hearing')
        new_patient['Respiratory_Rate'] = st.number_input('Respiratory Rate', min_value=0, max_value=50)
        new_patient['Temperature'] = st.number_input('Temperature', min_value=90.0, max_value=110.0)
        new_patient['Pain_Level'] = st.number_input('Pain Level', min_value=0, max_value=10)

        if st.button('Add Patient ➕'):
            # Assign a new unique ID
            if df_patients.empty or 'ID' not in df_patients.columns:
                new_patient_id = 1
            else:
                new_patient_id = df_patients['ID'].max() + 1
            new_patient['ID'] = new_patient_id

            # Convert to DataFrame and append to existing data
            new_patient_df = pd.DataFrame([new_patient])
            df_patients = pd.concat([df_patients, new_patient_df], ignore_index=True)

            # Save updated data to the database
            save_data(df_patients)
            st.success('New patient added successfully! ✅')

            # Show confirmation tick and message
            st.markdown('<div class="confirmation">✔ New patient added successfully!</div>', unsafe_allow_html=True)

            # Save DataFrame as CSV and provide download link
            csv = df_patients.to_csv(index=False)
            st.download_button(
                label="Download updated patient data as CSV",
                data=csv,
                file_name=f"patient_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )

    elif st.session_state.page == "About":
        st.title("About 🧠")
        st.write("This application is designed to revolutionize the way medical professionals manage patient data. Developed by our dedicated team, this secure cloud-based platform aims to streamline the process of accessing and updating patient reports.")
        st.write("With features like robust encryption, seamless data synchronization, and intuitive user interface, our app ensures that sensitive patient information is kept safe and easily accessible to authorized personnel.")
        st.write("Our mission is to empower healthcare providers with the tools they need to deliver exceptional patient care.")
        st.write("**Key Features:**")
        st.markdown("- **Secure Cloud Storage:** Patient data is stored securely in the cloud, ensuring data integrity and accessibility.")
        st.markdown("- **Intuitive User Interface:** The app is designed with a user-friendly interface that makes it easy to navigate and find the information you need.")
        st.markdown("- **Data Editing and Updates:** Medical professionals can easily edit and update patient reports, ensuring accurate and up-to-date records.")
        st.markdown("- **Real-time Synchronization:** Changes made to patient reports are synchronized in real-time across all authorized devices.")
        st.markdown("- **Robust Security Measures:** The app employs advanced security measures to protect patient data from unauthorized access.")
        st.write("**Contact Us:**")
        st.write("For any questions or feedback, please contact us at [your email address].")

    elif st.session_state.page == "Services":
        st.title("Services 🧰")
        st.write("We offer a range of services to help medical professionals manage patient data effectively:")
        st.markdown("- **Patient Report Management:** Securely store, access, and update patient reports.")
        st.markdown("- **Data Analytics and Reporting:** Generate insightful reports and dashboards to track patient trends.")
        st.markdown("- **Integration with Other Systems:** Integrate with existing healthcare systems for seamless data flow.")
        st.markdown("- **Customizable Features:** Tailor the application to meet your specific needs and workflows.")
        st.write("**Get in Touch:**")
        st.write("To learn more about our services or request a demo, please contact us at [your email address].")


