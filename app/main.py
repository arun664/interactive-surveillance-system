from fastapi import FastAPI
from app.routes import voice, alert

app = FastAPI(title="Interactive Surveillance Backend")

app.include_router(voice.router, prefix="/voice")
app.include_router(alert.router, prefix="/alert")

@app.get("/")
def root():
    return {"message": "Surveillance API is up!"}