from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import backend.database as database
import models
import requests
import os

# Automatically create the database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Get the Hugging Face token from Render's environment variables
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

class PromptRequest(BaseModel):
    question: str

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_ai_answer(question: str) -> str:
    """Sends the question to Hugging Face AI and returns the answer"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    # Format the prompt for the Mistral model
    payload = {
        "inputs": f"<s>[INST] Answer this question clearly and concisely: {question} [/INST]",
        "parameters": {"max_new_tokens": 150, "temperature": 0.7}
    }
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status() # Check for errors
        result = response.json()
        # Extract the generated text from the response
        return result[0]["generated_text"].split("[/INST]")[-1].strip()
    except Exception as e:
        return f"AI is currently waking up or busy. (Error: {str(e)})"

@app.get("/")
def home():
    return {
        "message": "Memory Connected! AI Brain Active!",
        "developer": "Zunzu",
        "status": "Phase 2 Complete"
    }

@app.post("/ask")
def ask_question(prompt: PromptRequest, db: Session = Depends(get_db)):
    # 1. Get the answer from the AI
    ai_answer = get_ai_answer(prompt.question)
    
    # 2. Save BOTH the question and the AI's answer to PostgreSQL
    db_prompt = models.Prompt(
        question=prompt.question, 
        answer=ai_answer
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    
    return {
        "id": db_prompt.id, 
        "question": db_prompt.question,
        "ai_answer": db_prompt.answer,
        "status": "Saved to database and answered by AI!"
    }

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    # Fetch all saved prompts from the database
    prompts = db.query(models.Prompt).all()
    return [{"id": p.id, "question": p.question, "answer": p.answer} for p in prompts]