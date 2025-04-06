from fastapi import APIRouter, HTTPException
from app.services.voice_recognition import transcribe_voice
from app.services.nlp_parser import parse_command
import os

router = APIRouter()

@router.post("/command")
async def handle_voice_command(audio_path: str):
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    text = transcribe_voice(audio_path)
    result = parse_command(text)
    return {"transcription": text, "parsed_command": result}