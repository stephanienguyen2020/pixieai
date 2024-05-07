import unittest
from system import System
from objects import Patient, Nurse
import pytest
from bson import ObjectId
from faker import Faker
import os

fake = Faker()

def test_ping_database():
    # Add your test logic here
    system = System(databse_service=os.getenv("DATABASE_SERVICE"))
    assert system.ping_database() == True


def test_create_patient():
#     # Add your test logic here
    system = System(databse_service=os.getenv("DATABASE_SERVICE"))

    nurse_fake_first_name = fake.first_name()
    nurse_fake_last_name = fake.last_name()
    nurse_fake_age = fake.random_int(min=18, max=60)
    nurse_fake_work_shift = fake.random_element(elements=("morning", "afternoon", "night"))
    nurse_fake_phone = fake.phone_number()
    if "x" in nurse_fake_phone:
        nurse_fake_phone = nurse_fake_phone.replace("x", "0")
        
    nurse_fake_email = "locvicvn1234@gmail.com"

    nurse = Nurse(nurse_fake_first_name, nurse_fake_last_name, nurse_fake_age, nurse_fake_work_shift, nurse_fake_phone, nurse_fake_email)
    nurse_id = system.create_nurse(nurse)

    first_name = fake.first_name()
    last_name = fake.last_name()
    age = fake.random_int(min=18, max=90)
    dob = fake.date_of_birth(minimum_age=age, maximum_age=age).strftime('%Y-%m-%d')
    address = fake.address()
    weight = fake.random_int(min=40, max=150)
    blood_type = fake.random_element(elements=("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"))
    phone = fake.phone_number()

    if "x" in phone: 
        phone = phone.replace("x", "0")


    email = fake.email()
    gender = fake.random_element(elements=("Male", "Female", "Other"))
    room_number = str(fake.random_int(min=100, max=999))
    assign_nurse_id = str(nurse_id)
    priority = fake.random_int(min=1, max=10)
    note = system.create_fake_patient_note()

    patient = Patient(
        first_name,
        last_name,
        age,
        dob,
        address,
        weight,
        blood_type,
        phone,
        email,
        gender,
        room_number,
        assign_nurse_id,
        priority,
        note,
        process=False
    )
    patient_id = system.create_patient(patient)

if __name__ == "__main__":
    pytest.main(["-s", "unit_test.py"])
