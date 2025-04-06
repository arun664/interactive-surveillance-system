import requests
import os
from pathlib import Path
import base64
import json
from datetime import datetime

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Set in .env or manually
GEMINI_TEXT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GEMINI_VISION_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
EVENT_LOG_FILE = Path("app/data/event_log.jsonl")
EVENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
monitoring_status = {"running": False}

def log_detection_event(detections: dict, image_path: str):
    timestamp = datetime.now().isoformat()
    event = {
        "timestamp": timestamp,
        "objects": detections.get("objects", []),
        "actions": detections.get("actions", []),
        "image_path": image_path
    }
    with open(EVENT_LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

def check_scene_with_gemini(detections: dict, user_rules: str, current_time: str, image_path: str = None):
    prompt = f"""
You are a security AI assistant. Analyze the following scene and check if any user-defined rules are violated.

Scene:
Objects: {', '.join(detections.get('objects', []))}
Actions: {', '.join(detections.get('actions', []))}

User-defined rule: {user_rules}
Current time: {current_time}

Respond with whether the rule is violated, and explain briefly why or why not.
If the rule should be tracked going forward, suggest a structured format to track it automatically.
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 256}
    }

    try:
        response = requests.post(f"{GEMINI_TEXT_ENDPOINT}?key={GEMINI_API_KEY}", json=payload, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error during Gemini API call: {e}"

    result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    if "not sure" in result.lower() or "can't tell" in result.lower():
        if image_path and Path(image_path).exists():
            return check_scene_with_gemini_using_image(image_path, prompt)
    return result

def check_scene_with_gemini_using_image(image_path: str, prompt: str):
    with open(image_path, "rb") as img_file:
        img_data = base64.b64encode(img_file.read()).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 256}
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(f"{GEMINI_VISION_ENDPOINT}?key={GEMINI_API_KEY}", json=payload, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error using vision API: {e}"

    return response.json()["candidates"][0]["content"]["parts"][0]["text"]
