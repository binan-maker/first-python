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
    headers = {
        "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful, concise AI assistant."},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI is currently busy. (Error: {str(e)})"

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