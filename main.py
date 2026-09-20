from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Hello World! This is my first live Python app!",
        "developer": "Zunzu",
        "status": "LIVE ON THE INTERNET!"
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