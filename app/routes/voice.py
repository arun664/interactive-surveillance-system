from fastapi import APIRouter
from app.services.voice_recognition import transcribe_voice
from app.services.nlp_parser import parse_command

router = APIRouter()

@router.post("/command")
async def handle_voice_command(audio_path: str):
    text = transcribe_voice(audio_path)
    result = parse_command(text)
    return {"transcription": text, "parsed_command": result}