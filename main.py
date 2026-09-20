from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database
import models

# Automatically create the database tables when the app starts
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Pydantic schema (validates incoming data)
class PromptRequest(BaseModel):
    question: str

# Helper function to get the database connection
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {
        "message": "Memory Connected! Ready for AI.",
        "developer": "Zunzu",
        "status": "Phase 1 Complete"
    }

@app.post("/ask")
def ask_question(prompt: PromptRequest, db: Session = Depends(get_db)):
    # Save the question to the database (AI will be added in Phase 2)
    db_prompt = models.Prompt(
        question=prompt.question, 
        answer="Waiting for AI Brain in Phase 2..."
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    
    return {
        "id": db_prompt.id, 
        "status": "Saved to PostgreSQL!", 
        "question": db_prompt.question
    }

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    # Fetch all saved prompts from the database
    prompts = db.query(models.Prompt).all()
    return prompts