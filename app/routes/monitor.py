from fastapi import APIRouter, Query, requests
from fastapi.responses import StreamingResponse
import cv2
from datetime import datetime
from app.services.video_monitor import start_detection_loop, get_latest_detections, capture_snapshot, stop_monitoring, monitoring_status
from app.services.gemini_client import check_scene_with_gemini, log_detection_event
from app.services.rules import add_rule_from_dict
from pathlib import Path
import json
import re

router = APIRouter()
EVENT_LOG_FILE = Path("app/data/event_log.jsonl")

@router.post("/start")
def start_monitoring():
    start_detection_loop()
    return {"status": "Camera started"}

@router.get("/detections")
def get_detections():
    return get_latest_detections()

@router.get("/ai-check")
def run_ai_check(rule: str = Query(...)):
    snapshot_path = capture_snapshot()
    if not snapshot_path:
        return {"error": "Could not capture frame."}

    detections = get_latest_detections() or {"objects": [], "actions": []}
    current_time = datetime.now().strftime("%I:%M %p")
    response = check_scene_with_gemini(detections, rule, current_time, snapshot_path)

    # 🧠 Try to extract structured rule JSON from Gemini response
    try:
        json_match = re.search(r'{.*}', response, re.DOTALL)
        if json_match:
            candidate = json.loads(json_match.group())
            rule_added = add_rule_from_dict(candidate)
        else:
            rule_added = False
    except Exception:
        rule_added = False

    return {
        "detections": detections,
        "ai_analysis": response,
        "rule_added": rule_added
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
    
def generate_video():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break

        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()

@router.get("/stream")
def video_stream():
    return StreamingResponse(generate_video(), media_type='multipart/x-mixed-replace; boundary=frame')

@router.post("/stop")
def stop_monitor():
    stop_monitoring()
    monitoring_status["running"] = False
    return {"message": "Monitoring stopped."}
