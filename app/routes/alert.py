# File: app/routes/alert.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_alert():
    return {"status": "Alert system ready (mock)"}
