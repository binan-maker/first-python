from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "I just updated my live app without touching the server!",
        "developer": "Zunzu",
        "status": "AUTO-DEPLOYED VIA GITHUB!",
        "next_goal": "Building a RAG AI System"
    }
@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Hello {name}! Welcome to my app!"}

@app.get("/about")
def about():
    return {
        "about": "I am leaning Python and building real applications",
        "skills": ["Python", "Fast", "Doceter", "Deployment"],
        "goal": "Become a $100k+ Python engineer"

    }