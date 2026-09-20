import os
import requests
import tempfile
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database
import models
import pypdf
import chromadb

# 1. Database Setup
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

# 2. ChromaDB Setup (Local Vector Database for RAG)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="rag_documents")

# 3. API Keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = os.environ.get("HF_TOKEN")

class PromptRequest(BaseModel):
    question: str

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_embedding(text: str):
    """Converts text to a vector using Hugging Face free API"""
    url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        response = requests.post(url, headers=headers, json={"inputs": text})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Embedding error: {e}")
        return []

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    try:
        # Extract text from PDF
        reader = pypdf.PdfReader(tmp_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Chunk text into 500-character pieces
        chunk_size = 500
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        # Embed and store in ChromaDB
        ids, documents, embeddings = [], [], []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:
                continue
            emb = get_embedding(chunk)
            if emb:
                ids.append(f"chunk_{i}")
                documents.append(chunk)
                embeddings.append(emb)
        
        if ids:
            collection.add(ids=ids, documents=documents, embeddings=embeddings)
            
        return {"message": f"Successfully processed {len(ids)} chunks from {file.filename}"}
    finally:
        os.remove(tmp_path)

def get_ai_answer(question: str, context: str = "") -> str:
    """Sends question to Groq, optionally with RAG context"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    system_prompt = "You are a helpful AI assistant."
    if context:
        system_prompt += f"\n\nUse the following context to answer the question. If the answer is not in the context, say 'I don't know based on the document.'\n\nContext:\n{context}"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-oss-20b", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code != 200:
            return f"Groq Error ({response.status_code}): {response.text}"
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI is currently busy. (Network Error: {str(e)})"

@app.post("/ask")
def ask_question(prompt: PromptRequest, db: Session = Depends(get_db)):
    # 1. RAG: Search ChromaDB for relevant context
    query_embedding = get_embedding(prompt.question)
    context = ""
    if query_embedding:
        results = collection.query(query_embeddings=[query_embedding], n_results=2)
        if results and results.get('documents'):
            context = "\n\n".join(results['documents'][0])
    
    # 2. Get AI answer with the retrieved context
    ai_answer = get_ai_answer(prompt.question, context)
    
    # 3. Save to PostgreSQL
    db_prompt = models.Prompt(question=prompt.question, answer=ai_answer)
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    
    return {
        "id": db_prompt.id, 
        "question": db_prompt.question,
        "ai_answer": db_prompt.answer,
        "status": "Answered with RAG!"
    }

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    prompts = db.query(models.Prompt).all()
    return [{"id": p.id, "question": p.question, "answer": p.answer} for p in prompts]