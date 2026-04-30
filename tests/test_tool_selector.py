import pytest

from app.llm.tool_selector import select_tool
from app.orchestrator import find_tool
from app.tools.swagger_parser import parse_swagger
from app.tools.tool_builder import build_llm_tools
import app.tools.registry as _registry

# Minimal Swagger spec — two HRMS endpoints used throughout these tests.
# Produces tools: name="get_employees" alias="employees"
#                 name="get_{id}_leave" alias="leave"
_SWAGGER = {
    "openapi": "3.0.1",
    "info": {"title": "HRMS API", "version": "v1"},
    "paths": {
        "/employees": {
            "get": {
                "summary": "List all employees",
                "parameters": [],
            }
        },
        "/employees/{id}/leave": {
            "get": {
                "summary": "Get leave balance for an employee",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
            }
        },
    },
}


@pytest.fixture
def parsed_tools(monkeypatch):
    """Parse _SWAGGER and inject the results into the registry globals.

    monkeypatch restores the original TOOLS/LLM_TOOLS after each test so
    registry state never leaks between tests.
    """
    parsed = parse_swagger(_SWAGGER)
    llm_tools = build_llm_tools(parsed)
    monkeypatch.setattr(_registry, "TOOLS", parsed)
    monkeypatch.setattr(_registry, "LLM_TOOLS", llm_tools)
    return parsed


# Checks the happy path: the LLM returns an exact tool name and find_tool
# locates it in the registry with a perfect score. If this breaks, the entire
# pipeline is broken regardless of fuzzy logic.
def test_selects_correct_tool_via_llm(mock_llm, parsed_tools):
    mock_llm.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "get_employees"}}]
    }

    llm_output = select_tool("list all employees")
    # "get_employees" → tokens {get, employees}
    # vs tool name "get_employees" → {get, employees}: score = 2/2 = 1.0
    result = find_tool(parsed_tools, llm_output)

    assert result is not None
    assert result["name"] == "get_employees"


# Checks the fuzzy fallback: the LLM returns a wordy but recognisable output
# ("get employees list") rather than the exact tool name. The token-overlap
# score is 2/3 ≈ 0.67 — above the 0.5 threshold — so the correct tool is
# still selected. This matters because real LLMs often emit extra words.
def test_falls_back_to_fuzzy_match(mock_llm, parsed_tools):
    # "get employees list" → tokens {get, employees, list}
    # vs tool name "get_employees" → {get, employees}: overlap = 2/3 ≈ 0.67 > 0.5
    mock_llm.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "get employees list"}}]
    }

    llm_output = select_tool("show all employees")
    result = find_tool(parsed_tools, llm_output)

    assert result is not None
    assert result["name"] == "get_employees"


# Checks that a completely unrelated LLM output returns None rather than a
# false-positive match. Zero token overlap means best_score = 0 < 0.5, so
# find_tool must return None — not call a random HRMS endpoint.
def test_returns_none_for_unknown_query(mock_llm, parsed_tools):
    # "xyz abc def gibberish" → tokens {xyz, abc, def, gibberish}
    # no intersection with any tool name or alias → score = 0
    mock_llm.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "xyz abc def gibberish"}}]
    }

    llm_output = select_tool("what is the weather today")
    result = find_tool(parsed_tools, llm_output)

    assert result is None


# Checks the rejection side of the 0.5 threshold: a score of 1/3 ≈ 0.33 must
# be rejected. "employees data report" shares only the token "employees" with
# "get_employees" (score = 1/3 < 0.5). The threshold check in find_tool is
# `best_score < 0.5`, so anything strictly below 0.5 returns None. Note: a
# score of exactly 0.5 passes the current check (>= 0.5 is accepted); this
# test uses 1/3 to verify the sub-threshold rejection path is enforced.
def test_fuzzy_threshold_boundary(mock_llm, parsed_tools):
    # "employees data report" → tokens {employees, data, report} (3 tokens)
    # vs "get_employees" → {get, employees}: intersection = {employees}
    # score = 1/3 ≈ 0.33 < 0.5 → rejected
    mock_llm.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "employees data report"}}]
    }

    llm_output = select_tool("employees salary data report")
    result = find_tool(parsed_tools, llm_output)

    assert result is None
