from app.models.rule_model import Rule
from app.routes.rules import rules_store, save_rules

def add_rule_from_dict(data: dict):
    try:
        rule = Rule(**data)
        rules_store.append(rule)
        save_rules(rules_store)
        return True
    except Exception as e:
        print("Failed to add rule:", e)
        return False
