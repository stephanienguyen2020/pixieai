from pymongo import MongoClient
import os
from dotenv import load_dotenv
from system import System
from pdf import PDF
import google.generativeai as genai
from datetime import datetime
from databricks import sql
import json
import sqlite3

load_dotenv(override=True)


class Record:
    def __init__(self, conversation=None, ai_service="gemini", databse_service="local"):
        """
        Args:
            conversation (list): A list of conversation between nurse and patient.
        """

        if conversation:
            self.conversation = conversation
        else:
            self.conversation = []
        self.client = MongoClient(os.getenv("MONGODB_URI"))

        if ai_service == "gemini":
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = genai.GenerativeModel("gemini-pro")
        elif ai_service == "azure":
            genai.configure(api_key=os.getenv("AZURE_API_KEY"))
            self.model = genai.GenerativeModel("azure")
        
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

        self.database_mode = databse_service

    def check_conversation(self, patient_id):
        """Check if the latest conversation is processed or not.
        If not process, process the conversation, change the processed status to True,
        and process.
        """
        system = System(databse_service=self.database_mode)
        conversation_dict = system.get_latest_conversation(patient_id)
        if conversation_dict["processed"]:
            return "Conversation has been processed"
        else:
            return conversation_dict["content"]

    def process_conversation(self, conversation):
        """Process the conversation and output to document DB with timestamp.
        Use Gemini with functional calling to generate a record from a conversation.
        """
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = self.summarize_conversation(conversation)

        result = response.text

        return {"content": result, "timestamp": today}

    def summarize_conversation(self, conversation):
        """Summarize the conversation."""
        task_description = (
            "I'm going to give you a list of questions and answers between nurse and patient. "
            "You will give me a summary of the conversation."
        )
        response = self.model.generate_content(task_description)

        conversation_data = "\n".join(
            [f"{qa['question']}\n{qa['answer']}" for qa in conversation["content"]]
        )
        query = "Here is the conversation:\n" + conversation_data
        response = self.model.generate_content(query)

        return response.text

    def save_record(self, record):
        """Save the record to document DB."""
        db = self.client.get_database()
        collection_name = "records"

        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)

        records_collection = db.get_collection(collection_name)

        records_collection.insert_one(record)

    def get_record(self, patient_id):
        system = System(databse_service=self.database_mode)
        patient_info = system.get_patient(patient_id)
        patient_id = patient_info["_id"]

        result = self.client["nursecheck"]["records"].find_one(
            {"patient_id": patient_id}
        )
        return result

    def update_record(
        self,
        patient_id,
        conversation,
        emotion_dict,
        priority_result,
        summary_result,
        sentiment_result,
    ):
        """Generate a record from a conversation in sql."""

        create_table_query = """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER NOT NULL PRIMARY KEY,
            patient_id BIGINT,
            patient_name VARCHAR(255),
            assign_nurse_id BIGINT,
            content VARCHAR(1000),
            timestamp TIMESTAMP,
            emotions VARCHAR(1000),
            priority_result INT,
            summary_result VARCHAR(1000),
            sentiment_result VARCHAR(1000)
        )
        """
        self.cursor.execute(create_table_query)
        system = System(databse_service=self.database_mode)
        patient_info = system.get_patient(patient_id)
        patient_name = patient_info[1] + " " + patient_info[2]
        content = conversation
        content = '"' + content + '"'

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emotions = json.dumps(emotion_dict)
        priority_result = priority_result
        summary_result = summary_result
        summary_result = '"' + summary_result + '"'
        sentiment_result = sentiment_result
        assign_nurse_id = patient_info[12]

        insert_query = """
        INSERT INTO conversations (patient_id, patient_name, assign_nurse_id, content, timestamp, emotions, priority_result, summary_result, sentiment_result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            patient_id,
            patient_name,
            assign_nurse_id,
            content,
            timestamp,
            emotions,
            priority_result,
            summary_result,
            sentiment_result,
        )
        self.cursor.execute(insert_query, values)
        self.connection.commit()
        return "Record updated successfully"

    def generate_record_pdf(self, patient_id):
        pdf = PDF()
        pdf.create_pdf(patient_id)
        return "PDF created successfully"

    def generate_record(self, patient_id):
        conversation = self.check_conversation(patient_id)
        if conversation == "Conversation has been processed":
            return "Conversation has been processed"
        else:
            processed_conversation = self.process_conversation(conversation)
            self.update_record(patient_id, processed_conversation)
            return "Record generated successfully"

    def get_latest_record_priority(self, patient_id):
        record = self.get_record(patient_id)
        notes = record["notes"]
        latest_note = notes[-1]
        return latest_note["priority"]
