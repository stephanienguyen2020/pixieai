import streamlit as st
from system import System
from streamlit_pdf_viewer import pdf_viewer
import os
from record import Record
from objects import Patient

st.title("Nurse/Doctor portal")
st.write(
    "This is a portal for nurses and doctors to view the priority of patients and their health summary"
)
nurse_id = st.text_input("Enter Nurse/doctor ID:")


if nurse_id:
    tab1, tab2, tab3 = st.tabs(
        ["View patients order", "Query similar case", "Create patient"]
    )
    with tab1:
        system = System(databse_service=os.getenv("DATABASE_SERVICE"))
        patient_orders = system.check_patients_order(nurse_id=nurse_id)
        st.subheader("Patients order:")
        count = 0

        for patient in patient_orders:
            count += 1
            if patient[-1] == 0:
                st.write(
                    f"{count}. {patient[1]} {patient[2]} - Priority: {patient[13]} - ID: {patient[0]}"
                )
                st.write(f"Room number: {patient[11]}")
                st.write("Notes: ", patient[-2])
                process_patient = st.checkbox("Process patient")
                system = System(databse_service=os.getenv("DATABASE_SERVICE"))
                if process_patient == True:

                    system.update_patient_process(patient[0], 1)
                    st.write("Patient has been processed")

                view_pdf = st.checkbox("View patient record")
                if view_pdf == True:
                    record = Record(databse_service=os.getenv("DATABASE_SERVICE"))
                    try:
                        pdf_viewer(
                            os.path.join("./records/", f"patient_{patient[0]}.pdf")
                        )
                    except:
                        st.write("Record not found")
                st.write("-----------------------------------")

        for patient in patient_orders:
            if patient[-1] == 1:
                st.write(
                    f"{count}. {patient[1]} {patient[2]} - Priority: {patient[13]} - Processed: Done"
                )
                process_patient = st.checkbox("Uncheck patient")
                system = System(databse_service=os.getenv("DATABASE_SERVICE"))
                if process_patient == True:
                    system.update_patient_process(patient[0], 0)

                st.write("-----------------------------------")
    with tab2:
        st.write("Query similar case")
        patient_id = st.text_input("Enter patient ID:")
        if patient_id:
            system = System(databse_service=os.getenv("DATABASE_SERVICE"))
            patient = system.get_patient(patient_id)
            patient_first_name = patient[1]
            patient_last_name = patient[2]
            patient_note = patient[-2]

            st.write(f"Patient: {patient_first_name} {patient_last_name}")
            st.write("Notes: ", patient_note)

            system = System(databse_service=os.getenv("DATABASE_SERVICE"))
            similar_cases = system.similarity_search(patient_id)
            st.write("Similar cases:")
            count = 0
            similar_cases = {
                k: v
                for k, v in sorted(
                    similar_cases.items(), key=lambda item: item[1], reverse=True
                )
            }

            for key, value in similar_cases.items():
                if value > 1:
                    patient_compare_id = key
                    patient_compare = system.get_patient(patient_compare_id)
                    patient_compare_first_name = patient_compare[1]
                    patient_compare_last_name = patient_compare[2]
                    patient_compare_note = patient_compare[-2]
                    count += 1
                    st.write(
                        f"{count}. {patient_compare_first_name} {patient_compare_last_name} - Similarity: {value}"
                    )
                    st.write("Notes: ", patient_compare_note)
                    st.write("-----------------------------------")

    with tab3:
        system = System(databse_service=os.getenv("DATABASE_SERVICE"))
        patient_first_name = st.text_input("Enter patient first name:")
        patient_last_name = st.text_input("Enter patient last name:")
        patient_age = st.text_input("Enter patient age:")
        patient_dob = st.text_input("Enter patient date of birth (DD/MM/YYYY):")
        patient_address = st.text_input("Enter patient address:")
        patient_weight = st.text_input("Enter patient weight (ibs):")
        patient_blood_type = st.selectbox(
            "Enter patient blood type:",
            ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"),
        )
        patient_phone = st.text_input("Enter patient phone number:")
        patient_email = st.text_input('Enter patient email:')
        patient_gender = st.selectbox("Patient's gender", ["male", "female", "other"])
        patient_room_number = st.text_input("Enter patient room number:")
        patient_assign_nurse_id = st.text_input("Enter nurse ID:")
        patient_priority = st.number_input("Enter patient priority:")
        patient_note = st.text_area("Enter patient initial note:")
        patient_process = False

       
        st.button("Create patient")
        
        if st.button == True:
            patient = Patient(
                patient_first_name,
                patient_last_name,
                patient_age,
                patient_dob,
                patient_address,
                patient_weight,
                patient_blood_type,
                patient_phone,
                patient_email,
                patient_gender,
                patient_room_number,
                patient_assign_nurse_id,
                patient_priority,
                patient_note,
                patient_process,
            )
            patient = system.create_patient(patient)
            print("Patient created successfully")
            st.write("Patient created successfully")
