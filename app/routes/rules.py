import json
from pathlib import Path
from fastapi import APIRouter
from app.models.rule_model import Rule

router = APIRouter()
RULES_FILE = Path("app/data/rules.json")
RULES_FILE.parent.mkdir(parents=True, exist_ok=True)

# Load existing rules from file
def load_rules():
    if RULES_FILE.exists():
        with open(RULES_FILE, "r") as f:
            return [Rule(**rule) for rule in json.load(f)]
    return []

# Save rules to file
def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump([rule.dict() for rule in rules], f, indent=2)

rules_store = load_rules()

@router.post("/add")
def add_rule(rule: Rule):
    rules_store.append(rule)
    save_rules(rules_store)
    return {"message": "Rule added", "rule": rule}

@router.get("/list")
def list_rules():
    return {"rules": rules_store}
