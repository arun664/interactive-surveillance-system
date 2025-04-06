import requests
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Set in .env or manually

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def check_scene_with_gemini(detections: dict, user_rules: str, current_time: str):
    prompt = f"""
You are a security AI assistant. Analyze the following scene and check if any user-defined rules are violated.

Scene:
Objects: {', '.join(detections.get('objects', []))}
Actions: {', '.join(detections.get('actions', []))}

User-defined rule: {user_rules}
Current time: {current_time}

Respond with whether the rule is violated, and explain briefly why or why not.
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 256}
    }

    response = requests.post(f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}", json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Error: {response.status_code} - {response.text}"
