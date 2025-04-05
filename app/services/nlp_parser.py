def parse_command(text: str) -> dict:
    # Simple rule-based placeholder
    if "track" in text:
        return {"intent": "track", "target": "person", "location": "front door", "time": "after 9 PM"}
    return {"intent": "unknown"}
