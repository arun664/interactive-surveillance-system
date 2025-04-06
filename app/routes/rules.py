from fastapi import APIRouter
from app.models.rule_model import Rule

router = APIRouter()
rules_store = []

@router.post("/add")
def add_rule(rule: Rule):
    rules_store.append(rule)
    return {"message": "Rule added", "rule": rule}

@router.get("/list")
def list_rules():
    return {"rules": rules_store}
