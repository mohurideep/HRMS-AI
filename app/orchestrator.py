# app/orchestrator.py
from app.llm import get_intent, generate_answer
from app.hrms_client import get_holidays
from app.data_transformer import clean_holidays
import json

def handle_query(query: str, auth_token: str):

    # Rule shortcut (important for reliability)
    if "holiday" in query.lower():
        data = get_holidays(auth_token)
        cleaned_data = clean_holidays(data)
        return generate_answer(query, cleaned_data)

    # LLM intent
    intent_raw = get_intent(query)

    try:
        intent = json.loads(intent_raw)
    except json.JSONDecodeError:
        return "Sorry, I did not understand."

    if intent.get("intent") == "get_holidays":
        data = get_holidays(auth_token)
        cleaned_data = clean_holidays(data)
        return generate_answer(query, cleaned_data)

    return "Unsupported request"