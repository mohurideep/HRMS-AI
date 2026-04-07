# app/tools/registry.py

TOOLS = []
LLM_TOOLS = []

def register_tools(parsed_tools, llm_tools):
    global TOOLS, LLM_TOOLS
    TOOLS = parsed_tools
    LLM_TOOLS = llm_tools


def get_tools():
    return TOOLS


def get_llm_tools():
    return LLM_TOOLS