import google.generativeai as genai
from pymongo import MongoClient
from hume import HumeVoiceClient, MicrophoneInterface
import os
from system import System
from datetime import datetime
import asyncio
import requests
import json
from dotenv import load_dotenv
from record import Record
import subprocess
from azure.ai.resources.client import AIClient
from azure.identity import DefaultAzureCredential
import openai

load_dotenv(override=True)
DATABASE_SERVICE = os.getenv("DATABASE_SERVICE")


class Chat:
    def __init__(
        self,
        patient_id,
        ai_service=os.getenv("AI_SERVICE"),
        databse_service="databricks",
    ):
        if not patient_id:
            raise ValueError("Patient ID is required")
        self.patient_id = patient_id
        self.client = MongoClient(os.getenv("MONGODB_URI"))

        if ai_service == "gemini":
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = genai.GenerativeModel("gemini-pro")
        elif ai_service == "azure":
            # Load config values
            with open(r"config.json") as config_file:
                config_details = json.load(config_file)

            # Setting up the deployment name
            chatgpt_model_name = config_details["CHATGPT_MODEL"]

            # This is set to `azure`
            openai.api_type = "azure"

            # The API key for your Azure OpenAI resource.
            openai.api_key = os.getenv("OPENAI_API_KEY")

            # The base URL for your Azure OpenAI resource. e.g. "https://<your resource name>.openai.azure.com"
            openai.api_base = config_details["OPENAI_API_BASE"]

            # Currently OPENAI API have the following versions available: 2022-12-01
            openai.api_version = config_details["OPENAI_API_VERSION"]

    async def record_streaming(self):
        # Retrieve the Hume API key from the environment variables
        HUME_API_KEY = os.getenv("HUME_API_KEY")
        # Connect and authenticate with Hume
        client = HumeVoiceClient(HUME_API_KEY)

        # Start streaming EVI over your device's microphone and speakers
        async with client.connect(config_id=os.getenv("HUME_CONFIG_ID")) as socket:
            await MicrophoneInterface.start(socket)

    def list_chats(self):
        # Retrieve the Hume API key from the environment variables
        HUME_API_KEY = os.getenv("HUME_API_KEY")
        # Connect and authenticate with Hume
        headers = {"X-Hume-Api-Key": HUME_API_KEY}
        response = requests.get(
            "https://api.hume.ai/v0/evi/chats",
            headers=headers,
            params={"page_size": 45, "page_number": 1},
        )

        return [chat["id"] for chat in response.json()["chats_page"]]

    def get_latest_chat_id(self):
        return self.list_chats()[-1]

    def list_chat_messages(self, chat_id):
        # Retrieve the Hume API key from the environment variables
        HUME_API_KEY = os.getenv("HUME_API_KEY")
        # Connect and authenticate with Hume
        headers = {"X-Hume-Api-Key": HUME_API_KEY}
        response = requests.get(
            f"https://api.hume.ai/v0/evi/chats/{chat_id}", headers=headers
        )
        result = response.json()
        start_timestamp = result["start_timestamp"]
        end_timestamp = result["end_timestamp"]
        events_page = result["events_page"]
        if events_page:
            emotion_features_dict = json.loads(events_page[0]["emotion_features"])
        else:
            emotion_features_dict = {}

        conversation = []

        for event in events_page:
            message = event["message_text"]
            role = event["role"]
            conversation.append({"role": role, "message": message})
            if event["emotion_features"]:
                event_dict = json.loads(event["emotion_features"])
                for key, value in event_dict.items():
                    if key in emotion_features_dict:
                        emotion_features_dict[key] += float(value)
                    else:
                        emotion_features_dict[key] = float(value)

        return {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "conversation": conversation,
            "emotion_features": emotion_features_dict,
        }

    def chat(self):
        while True:
            try:
                asyncio.run(self.record_streaming())
            except KeyboardInterrupt:
                print("Recording stopped. Processing conversation...")
                self.process_conversation()
                print("Conversation processed. Exiting...")
                break

    def detect_negative_emotion(self, emotion_dict):
        if os.getenv("AI_SERVICE") == "azure":
            response = openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=[
                    {
                        "role": "system",
                        "content": "From these emotion, determine if there are any negative emotion. Only return True or False.",
                    },
                    {"role": "user", "content": json.dumps(emotion_dict)},
                ],
            )
        else:
            response = self.model.generate_content(
                "From these emotion, determine if there are any negative emotion. Only return True or False.\n {}".format(
                    emotion_dict
                )
            )

        emotion_result = response.text
        print("Should visit or not based on emotion: ", emotion_result)
        if emotion_result == "True":
            system = System(databse_service=os.getenv("DATABASE_SERVICE"))
            patient_info = system.get_patient(self.patient_id)
            patient_info[-1] = 0
            system.update_patient_process(self.patient_id, patient_info)

        return emotion_result

    def process_priority(self, conversation, emotion_dict):
        if os.getenv("AI_SERVICE") == "azure":
            response = openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=[
                    {
                        "role": "system",
                        "content": "Process the priority of the patient from scale 1-10 based on the conversation and priority.  Return in format <priority number>. If cannot determine, return 1",
                    },
                    {
                        "role": "user",
                        "content": "Conversation: {}".format(conversation),
                    },
                    {"role": "user", "content": "Emotion: {}".format(emotion_dict)},
                ],
            )
            priority_result = response.choices[0].message
        else:
            response = self.model.generate_content(
                "Process the priority of the patient from scale 1-10 based on the conversation and priority.  Return in format <priority number>. If cannot determine, return 1 \n Conversation: {} \n Emotion: {}".format(
                    conversation, emotion_dict
                )
            )
        priority_result = response.text
        priority_result = int(priority_result)

        print("Priority of the patient: ", str(priority_result))
        return priority_result

    def summarize_conversation(self, conversation):
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if os.getenv("AI_SERVICE") == "azure":
            response = openai.ChatCompletion.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=[
                    {
                        "role": "system",
                        "content": "From the conversation, generate a summarized note on patient's health. Don't overlook anything. Return the summary in 1 line.",
                    },
                    {"role": "user", "content": conversation},
                ],
            )
            summary_result = response.choices[0].message
        else:
            response = self.model.generate_content(
                "From the conversation, generate a summarized note on patient's health. Don't overlook anything. Return the summary in 1 line. \n {}".format(
                    conversation
                )
            )

        summary_result = response.text
        print("Summary of patient's health: ", summary_result)
        system = System(databse_service=os.getenv("DATABASE_SERVICE"))
        system.update_patient_note(self.patient_id, summary_result)

        return summary_result

    def process_record(
        self,
        conversation,
        emotion_dict,
        priority_result,
        summary_result,
        patient_info,
        emotion_result,
        sentiment_result,
    ):
        system = System(databse_service=os.getenv("DATABASE_SERVICE"))
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_result = summary_result.replace("'", " ")
        system.update_patient_order(
            self.patient_id, str(priority_result), str(summary_result)
        )

        record = Record(conversation, databse_service=os.getenv("DATABASE_SERVICE"))
        record.update_record(
            self.patient_id,
            conversation,
            emotion_dict,
            priority_result,
            summary_result,
            sentiment_result,
        )

        # Send email to nurse if negative emotion detected
        nurse_id = patient_info[12]

        if emotion_result == "True":
            system.send_email(nurse_id, self.patient_id)
            print("Email sent to nurse")

    def sentiment_analysis(self, conversation):
        sentiment_dict = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        for line in conversation.split("\n"):
            if line.startswith("Patient:"):
                response = self.model.generate_content(
                    "From the conversation, determine the sentiment of the conversation. Return in format <postive/negative/neutral>:<score>  \n {}".format(
                        line
                    )
                )
                sentiment_result = response.text
                sentiment, score = sentiment_result.split(":")
                sentiment_dict[sentiment] += float(score)

        print("Sentiment analysis: ", sentiment_dict)
        return json.dumps(sentiment_dict)

    def process_conversation(self):
        conversation = ""
        emotion_dict = {}
        chat_id = self.get_latest_chat_id()
        chat_messages = self.list_chat_messages(chat_id)
        for message in chat_messages["conversation"]:
            if message["role"] == "USER":
                conversation += "Patient: " + message["message"] + "\n"
            else:
                conversation += "Nurse: " + message["message"] + "\n"

        if conversation == "":
            print("No conversation recorded. Exiting...")
            return
        emotion_features = chat_messages["emotion_features"]

        system = System(databse_service=os.getenv("DATABASE_SERVICE"))
        patient_info = system.get_patient(self.patient_id)
        top_5_emotions = sorted(
            emotion_features, key=emotion_features.get, reverse=True
        )[:5]

        for emotion in top_5_emotions:
            emotion_dict[emotion] = round(emotion_features[emotion], 2)
        # emotion_dict = json.dumps(emotion_dict)

        print("Conversation: ", conversation)
        print("Top 5 emotions: ", emotion_dict)

        emotion_result = self.detect_negative_emotion(emotion_dict)
        summary_result = self.summarize_conversation(conversation)
        priority_result = self.process_priority(conversation, emotion_dict)
        sentiment_result = self.sentiment_analysis(conversation)

        # self.save_to_db(patient_info, conversation, top_5_emotions)
        self.process_record(
            conversation,
            emotion_dict,
            priority_result,
            summary_result,
            patient_info,
            emotion_result,
            sentiment_result,
        )
        return conversation


if __name__ == "__main__":
    PATIENT_ID = "1"
    chat = Chat(PATIENT_ID)
    chat.chat()
    # chat.process_conversation()
