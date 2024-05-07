import streamlit as st
from system import System
from streamlit_pdf_viewer import pdf_viewer
import os
from record import Record

st.title('Nurse/Doctor portal')
st.write('This is a portal for nurses and doctors to view the priority of patients and their health summary')
nurse_id = st.text_input('Enter Nurse/doctor ID:')

if nurse_id:
    system = System()
    patient_orders = system.check_patients_order(nurse_id=nurse_id)
    st.subheader('Patients order:')
    count = 0
    for patient in patient_orders:
        count += 1
        if patient[-1] == 0:
            st.write(f'{count}. {patient[1]} {patient[2]} - Priority: {patient[13]} - ID: {patient[0]}')
            st.write(f'Room number: {patient[11]}')
            st.write("Notes: ", patient[-2])
            process_patient = st.checkbox('Process patient')
            system = System()
            if process_patient == True:
                
                system.update_patient_process(patient[0], 1)
                st.write('Patient has been processed')

            view_pdf = st.checkbox('View patient record')
            if view_pdf == True:
                record = Record()
                try:
                    pdf_viewer(os.path.join('./records/', f'patient_{patient[0]}.pdf'))
                except:
                    st.write('Record not found')
 

            st.write('-----------------------------------')

    st.subheader('Processed patients:')
    for patient in patient_orders:
        if patient[-1] == 1:
            st.write(f'{count}. {patient[1]} {patient[2]} - Priority: {patient[13]}')
            process_patient = st.checkbox('Uncheck patient')
            system = System()
            if process_patient == True:
                system.update_patient_process(patient[0], 0)
        
            st.write('-----------------------------------')
            
    
        
        