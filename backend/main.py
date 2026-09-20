from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database
import models
import requests
import os

# Automatically create the database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

class PromptRequest(BaseModel):
    question: str

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_ai_answer(question: str) -> str:
    """Sends the question directly to Groq via HTTP"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    api_key = os.environ.get("GROQ_API_KEY")
    
    # Safety check: Make sure the key actually loaded
    if not api_key or not api_key.startswith("gsk_"):
        return "Error: GROQ_API_KEY is missing or invalid in Render settings."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
       # Updated to Groq's current, stable, production-ready model
    payload = {
        "model": "llama-3.3-70b-versatile",  # <-- CHANGE THIS LINE
        "messages": [
            {"role": "system", "content": "You are a helpful, concise AI assistant."},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # If it fails, print the EXACT reason Groq rejected it
        if response.status_code != 200:
            return f"Groq Error ({response.status_code}): {response.text}"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
        
    except Exception as e:
        return f"AI is currently busy. (Network Error: {str(e)})"
@app.get("/")
def home():
    return {
        "message": "Memory Connected! AI Brain Active (Powered by Groq)!",
        "developer": "Zunzu",
        "status": "Production Ready"
    }

@app.post("/ask")
def ask_question(prompt: PromptRequest, db: Session = Depends(get_db)):
    # 1. Get the answer from the reliable AI
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
    prompts = db.query(models.Prompt).all()
    return [{"id": p.id, "question": p.question, "answer": p.answer} for p in prompts]