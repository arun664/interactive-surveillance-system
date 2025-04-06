from fastapi import FastAPI
from app.routes import voice, alert, rules, monitor
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Interactive Surveillance Backend")

app.include_router(voice.router, prefix="/voice")
app.include_router(alert.router, prefix="/alert")
app.include_router(rules.router, prefix="/rules")
app.include_router(monitor.router, prefix="/monitor")

@app.get("/")
def root():
    return {"message": "Surveillance API is up!"}