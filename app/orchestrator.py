# app/orchestrator.py
from app.tools.registry import get_tools
from app.tools.executor import execute_tool
from app.llm.tool_selector import select_tool
from app.llm.response_generator import generate_response
from app.llm.llm import get_llm

def handle_query(query: str, auth_token: str):

    # # Rule shortcut (important for reliability)
    # if "holiday" in query.lower():
    #     data = get_holidays(auth_token)
    #     cleaned_data = clean_holidays(data)
    #     return generate_answer(query, cleaned_data)
    
    
    # 🔥 STEP 1 — Intent → Tool
    tool_name = select_tool(get_llm(), query)
    if not tool_name:
        return "Sorry, I could not find a relevant API."

    tools = get_tools()

    tool = next((t for t in tools if t["name"] == tool_name), None)
    if not tool:
        return "Tool not found."
    
    # 🔥 STEP 2 — Execute API
    raw_data = execute_tool(tool, {}, auth_token)

    # 🔥 STEP 3 — Extract usable data
    cleaned_data = raw_data.get("data", [])

    # 🔥 STEP 4 — LLM Response Generation
    final_answer = generate_response(get_llm(), query, cleaned_data)

    return final_answer
    # # LLM intent
    # intent_raw = get_intent(query)

    # try:
    #     intent = json.loads(intent_raw)
    # except json.JSONDecodeError:
    #     return "Sorry, I did not understand."

    # if intent.get("intent") == "get_holidays":
    #     data = get_holidays(auth_token)
    #     cleaned_data = clean_holidays(data)
    #     return generate_answer(query, cleaned_data)

    # return "Unsupported request"