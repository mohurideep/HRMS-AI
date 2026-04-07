# app/tools/tool_builder.py

def build_llm_tools(parsed_tools):
    llm_tools = []

    for tool in parsed_tools:
        llm_tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    p["name"]: {"type": p["type"]}
                    for p in tool["parameters"]
                },
                "required": [
                    p["name"] for p in tool["parameters"] if p["required"]
                ]
            }
        })

    return llm_tools