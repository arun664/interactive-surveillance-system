from fastapi import APIRouter, Query
from datetime import datetime
from app.services.video_monitor import start_detection_loop, get_latest_detections
from app.services.gemini_client import check_scene_with_gemini

router = APIRouter()

@router.post("/start")
def start_monitoring():
    start_detection_loop()
    return {"status": "Camera started"}

@router.get("/detections")
def get_detections():
    return get_latest_detections()

@router.get("/ai-check")
def run_ai_check(rule: str = Query(..., description="User-defined rule to check against")):
    detections = get_latest_detections()
    current_time = datetime.now().strftime("%I:%M %p")
    response = check_scene_with_gemini(detections, rule, current_time)
    return {
        "detections": detections,
        "ai_analysis": response
    }
