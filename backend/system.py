from pymongo import MongoClient
import os
from dotenv import load_dotenv
from objects import Patient, Nurse
import qrcode
import google.generativeai as genai
from bson import ObjectId
import resend
from databricks import sql
import sqlite3

load_dotenv(override=True)


class System:
    def __init__(self, ai_service="gemini", databse_service="local"):

        if databse_service == "databricks":
            self.connection = sql.connect(
                server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
                http_path=os.getenv("DATABRICKS_HTTP_PATH"),
                access_token=os.getenv("DATABRICKS_TOKEN"),
            )

            self.cursor = self.connection.cursor()

        elif databse_service == "local":
            self.connection = sqlite3.connect("local.db")
            self.cursor = self.connection.cursor()

        if ai_service == "gemini":
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = genai.GenerativeModel("gemini-pro")

    def ping_database(self):
        """Ping the database"""
        # return self.client.server_info()
        return self.cursor is not None

    def create_patient(self, patient_info: Patient):
        """Create a new patient in the database"""
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER NOT NULL PRIMARY KEY,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            age INT,
            dob DATE,
            address VARCHAR(255),
            weight INT,
            blood_type VARCHAR(5),
            phone VARCHAR(20),
            email VARCHAR(255),
            gender VARCHAR(10),
            room_number INT,
            assign_nurse_id INT,
            priority INT,
            note VARCHAR(1000), 
            process BOOLEAN
        )
        """

        self.cursor.execute(create_table_query)

        # Insert fake data
        insert_query = f"""
        INSERT INTO user (first_name, last_name, age, dob, address, weight, blood_type, phone, email, gender, room_number, assign_nurse_id, priority, note, process)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            patient_info.first_name,
            patient_info.last_name,
            patient_info.age,
            patient_info.dob,
            patient_info.address,
            patient_info.weight,
            patient_info.blood_type,
            patient_info.phone,
            patient_info.email,
            patient_info.gender,
            patient_info.room_number,
            patient_info.assign_nurse_id,
            patient_info.priority,
            patient_info.note,
            patient_info.process,
        )
        self.cursor.execute(insert_query, values)

        self.connection.commit()

        return self.cursor.lastrowid

    def get_patient(self, patient_id):
        """Get the patient information from the database"""
        self.cursor.execute(f"SELECT * FROM user WHERE id = {patient_id}")
        patient = self.cursor.fetchone()
        return patient

    def get_patient_record(self, patient_id):
        """Get the patient record from the database"""
        self.cursor.execute(
            f"SELECT * FROM conversations WHERE patient_id = {patient_id}"
        )
        patient = self.cursor.fetchall()
        return patient

    def update_patient_process(self, patient_id, process):
        """Update the patient process in the database"""
        self.cursor.execute(
            f"UPDATE user SET process = {process} WHERE id = {patient_id}"
        )
        self.connection.commit()
        return "Patient process updated"

    def update_patient_record(self, patient_id, new_note, timestamp):
        """Update the patient record in the database"""
        self.cursor.execute(f"SELECT * FROM user WHERE id = {patient_id}")
        patient = self.cursor.fetchone()
        notes = patient["note"]
        notes.append(new_note)
        self.cursor.execute(f"UPDATE user SET note = {notes} WHERE id = {patient_id}")
        self.connection.commit()
        return "Patient record updated"

    def delete_patient(self, patient_id):
        """Delete the patient from the database"""
        self.cursor.execute(f"DELETE FROM user WHERE id = {patient_id}")
        self.connection.commit()
        return "Patient deleted"

    def generate_qr_code(self, patient_id: str):
        """Generate a QR code for the patient"""
        img = qrcode.make(patient_id)
        img.save("qr_code/patient_{}_qrcode.png".format(patient_id))
        return "QR code generated"

    def delete_qr_code(self, patient_id):
        """Delete the QR code for the patient"""
        os.remove("qr_code/patient_{}_qrcode.png".format(patient_id))
        return "QR code deleted"

    def show_qr_code(self, patient_id):
        """Show the QR code for the patient"""
        img = qrcode.make(patient_id)
        img.show()
        return "QR code displayed"

    def get_all_patients(self):
        """Retrieve all patients from the database"""
        self.cursor.execute("SELECT * FROM user")
        patients = self.cursor.fetchall()
        return patients

    def get_all_documents(self):
        """Retrieve all documents from the database"""
        self.cursor.execute("SELECT * FROM documents")
        documents = self.cursor.fetchall()
        return documents

    def retrieve_conversations(self, patient_id):
        """Retrieve the conversations between nurse and patient from the database"""
        self.cursor.execute(f"SELECT * FROM documents WHERE patient_id = {patient_id}")
        conversations = self.cursor.fetchall()
        return conversations

    def get_latest_conversation(self, patient_id):
        """Retrieve the latest conversation between nurse and patient from the database"""
        conversations = self.retrieve_conversations(patient_id)
        return conversations[-1]

    def convert_dict_to_text(self, conversation):
        """Convert the conversation from dictionary to text"""
        content = conversation["content"]
        text = ""
        for c in content:
            text += c["question"] + "\n"
            text += c["answer"] + "\n"
        return text

    def update_patient_order(self, patient_id, priority, note):
        """Update the priority of the patient"""
        self.cursor.execute(
            f"UPDATE user SET priority = {priority}, note = '{note}' WHERE id = {patient_id}"
        )
        self.connection.commit()
        return "Patient order updated"

    def update_patient_note(self, patient_id, notes):
        """Update the note of the patient"""
        notes = '"' + notes + '"'

        self.cursor.execute(f"UPDATE user SET note = {notes} WHERE id = {patient_id}")
        self.connection.commit()
        return "Patient note updated"

    def process_patient(self, patient_id):
        """Process the patient information"""
        patient = self.get_patient(patient_id)
        if patient["process"] is True:
            patient["process"] = False
        else:
            patient["process"] = True
        self.client["nursecheck"]["patients"].update_one(
            {"_id": ObjectId(patient_id)}, {"$set": patient}
        )

    def check_patients_order(self, nurse_id):
        """Check the order of the patients"""
        self.cursor.execute(
            f"""SELECT * FROM user WHERE assign_nurse_id = {nurse_id} ORDER BY priority DESC"""
        )
        patients = self.cursor.fetchall()
        return patients

    def create_nurse(self, nurse_info: Nurse):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER NOT NULL PRIMARY KEY,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            age INT,
            work_shift VARCHAR(10),
            phone VARCHAR(20),
            email VARCHAR(255)
        )
        """
        self.cursor.execute(create_table_query)

        # Insert fake data
        insert_query = (
            f"INSERT INTO staff (first_name, last_name, age, work_shift, phone, email) VALUES (?, ?, ?, ?, ?, ?)"
            ""
        )
        values = (
            nurse_info.first_name,
            nurse_info.last_name,
            nurse_info.age,
            nurse_info.work_shift,
            nurse_info.phone,
            nurse_info.email,
        )

        self.cursor.execute(insert_query, values)
        self.connection.commit()

        return self.cursor.lastrowid

    def get_nurse(self, nurse_id):
        """Get the nurse information from the database"""
        nurse = self.client["nursecheck"]["nurses"].find_one(
            {"_id": ObjectId(nurse_id)}
        )
        return nurse

    def get_all_nurses(self):
        """Retrieve all nurses from the database"""
        nurses = self.client["nursecheck"]["nurses"].find()
        return [nurse for nurse in nurses]

    def delete_nurse(self, nurse_id):
        """Delete the nurse from the database"""
        self.client["nursecheck"]["nurses"].delete_one({"_id": ObjectId(nurse_id)})
        return "Nurse deleted"

    def update_nurse(self, nurse_id, nurse_info):
        """Update the nurse information in the database"""
        self.client["nursecheck"]["nurses"].update_one(
            {"_id": ObjectId(nurse_id)}, {"$set": nurse_info}
        )
        return "Nurse information updated"

    def find_nurse(self, first_name, last_name, age, phone):
        """Find the nurse in the database"""
        nurse = self.client["nursecheck"]["nurses"].find_one(
            {
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
                "phone": phone,
            }
        )
        return nurse

    def similarity_search(self, patient_id):
        """Find the similar cases in the database"""
        patient = self.get_patient(patient_id)
        patient_note = patient[-2]

        if os.getenv("DATABASE_SERVICE") == "databricks":
            self.cursor.execute(
                "SELECT id, ai_similarity(?, note) FROM user WHERE id != ?",
                (patient_note,),
            )
            conversations = self.cursor.fetchall()

            similarity = {}
            for conversation in conversations:
                similarity[conversation[0]] = conversation[1]
        else:
            self.cursor.execute("SELECT id, note FROM user WHERE id != ?", (patient_id,))
            conversations = self.cursor.fetchall()

            similarity = {}
            for conversation in conversations:
                if conversation[0] != 2:
                    try:
                        response = self.model.generate_content(
                            "Compare the patient's note with the database. Return the similarity score based on health condition in number from 1 (lowest) - to 100 (highest similarity). Return format: <similarity score>. \n Patient Note: {} \n Database Note: {}".format(
                                patient_note, str(conversation[1])
                            )
                        ).text
                        similarity[conversation[0]] = int(response)
                    except:
                        similarity[conversation[0]] = 0

            
            similarity = {k: int(v) for k, v in similarity.items() if int(v) > 0}

        return similarity

    def assign_patient_to_nurse(self, patient_id, nurse_id):
        """Assign the patient to a nurse"""
        patient = self.get_patient(patient_id)
        patient["assign_nurse_id"] = nurse_id
        self.client["nursecheck"]["patients"].update_one(
            {"_id": ObjectId(patient_id)}, {"$set": patient}
        )
        return "Patient assigned to nurse"

    def create_fake_patient_note(self):
        return self.model.generate_content(
            "Create a fake patient's short condition in 1 sentence either normal or not. Don't add any personal information."
        ).text

    def send_email(self, nurse_id, patient_id):
        """Send an email to the patient"""
        nurse = self.get_nurse(nurse_id)
        patient = self.get_patient(patient_id)
        email = nurse["email"]
        resend.api_key = os.getenv("RESEND_API_KEY")

        title = "Urgent care alert for nurse {}".format(
            nurse["first_name"] + " " + nurse["last_name"]
        )

        r = resend.Emails.send(
            {
                "from": "onboarding@resend.dev",
                "to": str(email),
                "subject": title,
                "html": """
                        <html>
                            <ul>
                                <li> Patient: {} (ID: {})</li>
                                <li> Status: Emergent </li>
                                <li> Action Required: Immediate attention needed. Review patient details promptly and proceed with urgent care protocols. </li>
                            </ul>
                        </html>
                        """.format(
                    patient["first_name"] + " " + patient["last_name"], patient_id
                ),
            }
        )
