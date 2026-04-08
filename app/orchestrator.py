# app/orchestrator.py

import re

from app.tools.registry import get_tools
from app.tools.executor import execute_tool
from app.llm.tool_selector import select_tool
from app.llm.response_generator import generate_response

def handle_query(query: str, auth_token: str):

    # # Rule shortcut (important for reliability)
    # if "holiday" in query.lower():
    #     data = get_holidays(auth_token)
    #     cleaned_data = clean_holidays(data)
    #     return generate_answer(query, cleaned_data)
    
    
    # 🔥 STEP 1 — Intent → Tool
    tool_name = select_tool(query)
    if not tool_name:
        return "Sorry, I could not find a relevant API."

    tools = get_tools()
    tool = find_tool(tools, tool_name)
    if not tool:
        return "Tool not found."
    
    # 🔥 STEP 2 — Execute API
    raw_data = execute_tool(tool, {}, auth_token)

    # 🔥 STEP 3 — Extract usable data
    cleaned_data = raw_data.get("data", [])

    # 🔥 STEP 4 — LLM Response Generation
    final_answer = generate_response(query, cleaned_data)

    return final_answer


def normalize(text: str):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', ' ', text)
    return set(text.split())

def match_score(a: str, b: str):
    set_a = normalize(a)
    set_b = normalize(b)

    if not set_a or not set_b:
        return 0

    return len(set_a & set_b) / len(set_a)

def find_tool(tools, tool_name):

    tool_name = tool_name.lower()

    best_tool = None
    best_score = 0

    for t in tools:
        score_name = match_score(tool_name, t["name"])
        score_alias = match_score(tool_name, t.get("alias", ""))

        score = max(score_name, score_alias)

        if score > best_score:
            best_score = score
            best_tool = t

    # 🔒 threshold to avoid wrong matches
    if best_score < 0.5:
        return None

    return best_tool