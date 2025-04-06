from fastapi import APIRouter, Query
from datetime import datetime
from app.services.video_monitor import start_detection_loop, get_latest_detections, capture_snapshot
from app.services.gemini_client import check_scene_with_gemini, log_detection_event
from pathlib import Path
import json

router = APIRouter()
EVENT_LOG_FILE = Path("app/data/event_log.jsonl")

@router.post("/start")
def start_monitoring():
    start_detection_loop()
    return {"status": "Camera started"}

@router.get("/detections")
def get_detections():
    return get_latest_detections()

@router.get("/monitor/ai-check")
def run_ai_check(rule: str = Query(..., description="User-defined rule to check against")):
    snapshot_path = capture_snapshot()

    if not snapshot_path:
        return {"error": "Failed to capture camera frame."}

    detections = get_latest_detections() or {"objects": [], "actions": []}
    current_time = datetime.now().strftime("%I:%M %p")

    response = check_scene_with_gemini(
        detections=detections,
        user_rules=rule,
        current_time=current_time,
        image_path=snapshot_path
    )

    return {
        "detections": detections,
        "ai_analysis": response
    }

@router.get("/ask")
def ask_surveillance_question(question: str = Query(..., description="Ask a question about the surveillance history")):
    if not EVENT_LOG_FILE.exists():
        return {"error": "No event log found."}

    # Load recent events (last 100 lines)
    with open(EVENT_LOG_FILE, "r") as f:
        lines = f.readlines()[-100:]

    context = "\n".join(lines)

    prompt = f"""
You are an AI assistant helping review surveillance logs.

Here is the recent surveillance event history:
{context}

Now answer the following question clearly and briefly:
{question}
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 300}
    }

    import os
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    response = requests.post(f"{endpoint}?key={GEMINI_API_KEY}", json=payload, headers=headers)

    if response.status_code == 200:
        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return {"question": question, "answer": reply}
    else:
        return {"error": response.text}
