from app.tools.registry import get_llm_tools
from app.llm.llm_service import generate

def select_tool(query: str):

    tools = get_llm_tools()

    tool_names = [t["name"] for t in tools]

    messages = [
        {
            "role": "system",
            "content": f"""
You are an HR assistant.

Available tools:
{tool_names}

Select the MOST relevant tool based on the user's query.

IMPORTANT:
- Return EXACT tool name Only
- Do NOT simplify or rename
- Choose closest match
"""
        },
        {
            "role": "user",
            "content": query
        }
    ]

    response = generate(
        messages=messages,
        temperature=0
    )

    return response.strip()