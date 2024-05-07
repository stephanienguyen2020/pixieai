from typing import Annotated
from fastapi import FastAPI
from chat import Chat 
import uvicorn

app = FastAPI()

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    chat = Chat(patient_id)
    chat.process_conversation()
    return {"status": "success"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5173)