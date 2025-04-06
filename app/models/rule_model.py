from pydantic import BaseModel

class Rule(BaseModel):
    intent: str
    target: str
    location: str
    time: str