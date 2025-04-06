import whisper

model = whisper.load_model("base")  # options: tiny, base, small, medium, large

def transcribe_voice(audio_path: str) -> str:
    result = model.transcribe(audio_path)
    return result["text"]
