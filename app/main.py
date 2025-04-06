from fastapi import FastAPI
from app.routes import voice, alert, rules, monitor
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="Interactive Surveillance Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice.router, prefix="/voice")
app.include_router(alert.router, prefix="/alert")
app.include_router(rules.router, prefix="/rules")
app.include_router(monitor.router, prefix="/monitor")

snapshots_dir = Path("frame_snapshots")
snapshots_dir.mkdir(exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=Path("frame_snapshots")), name="snapshots")

@app.get("/")
def root():
    return {"message": "Surveillance API is up!"}