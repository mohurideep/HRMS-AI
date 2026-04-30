import logging
import pytest
import requests
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers shared by multiple tests
# ---------------------------------------------------------------------------

class _MockResponse:
    """Minimal requests.Response substitute for HRMS API calls.

    Only the three attributes that executor.py reads are implemented:
    status_code, text (used in error messages), and json().
    """

    def __init__(self, json_data, status_code=200, text="ok"):
        self._json = json_data
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._json


def _configure_llm(mock_llm, tool_name, answer):
    """Make mock_llm answer the two sequential LLM calls inside handle_query.

    handle_query calls generate() exactly twice per request:
      1. select_tool  → should return a recognisable tool name
      2. generate_response → should return the final conversational answer
    Using side_effect consumes one item per call so each call gets the right
    response without interfering with the other.
    """
    mock_llm.create_chat_completion.side_effect = [
        {"choices": [{"message": {"content": tool_name}}]},
        {"choices": [{"message": {"content": answer}}]},
    ]


def _mock_hrms_api(monkeypatch, payload):
    """Patch requests.get to return payload as the HRMS API response body."""
    mock_get = MagicMock(return_value=_MockResponse(payload, 200))
    monkeypatch.setattr(requests, "get", mock_get)
    return mock_get


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_full_chat_request_success(client, mock_llm, monkeypatch):
    """Verify the complete /chat pipeline returns a 200 with a string answer.

    This is the golden-path integration test. It wires together all three
    pipeline steps:
      1. LLM tool selection  – first mock call returns "get_employees", which
         fuzzy-matches (score 1.0) to the registered tool from FAKE_SWAGGER.
      2. HRMS API execution  – requests.get is patched to return employee data
         under the "data" key so that raw_data.get("data", []) is non-empty.
      3. LLM response generation – second mock call returns a plain sentence.

    Asserts that the HTTP response is 200 and {"response": <non-empty string>}.
    """
    _configure_llm(mock_llm, "get_employees", "There is 1 employee: Alice.")
    _mock_hrms_api(monkeypatch, {"data": [{"id": 1, "name": "Alice"}]})

    response = client.post(
        "/chat",
        json={"query": "show me all employees"},
        headers={"Authorization": "Bearer test-token-123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert isinstance(body["response"], str)
    assert len(body["response"]) > 0


def test_missing_auth_header_returns_401(client):
    """Verify /chat returns 401 when no Authorization header is present.

    HTTPBearer is configured with auto_error=False, so FastAPI will not raise
    on its own — credentials will be None. The manual check in main.py
    (`if credentials is None: raise HTTPException(401)`) is the only guard.
    This test confirms that guard is in place and cannot be bypassed by simply
    omitting the header.
    """
    response = client.post("/chat", json={"query": "show me all employees"})

    assert response.status_code == 401


def test_timing_checkpoints_recorded(client, mock_llm, monkeypatch, caplog):
    """Verify that all three pipeline steps emit a timing log on every request.

    Timer.checkpoint() calls logging.info() with the step label embedded in
    the message. Capturing the root logger at INFO level lets us assert that
    the orchestrator reached each stage — a regression guard against a step
    being silently skipped (e.g., if find_tool returns early or an exception
    is swallowed before the final checkpoint).

    The three labels checked correspond exactly to the strings in orchestrator.py:
      - "Tool Selection LLM"      after select_tool()
      - "Tool Execution API call" after execute_tool()
      - "Response Generation LLM" after generate_response()
    """
    _configure_llm(mock_llm, "get_employees", "There is 1 employee: Alice.")
    _mock_hrms_api(monkeypatch, {"data": [{"id": 1, "name": "Alice"}]})

    # Set level before the request so all INFO records from the worker thread
    # are captured by caplog's root-logger handler.
    caplog.set_level(logging.INFO)

    client.post(
        "/chat",
        json={"query": "show me all employees"},
        headers={"Authorization": "Bearer test-token-123"},
    )

    log_output = " ".join(caplog.messages)
    assert "Tool Selection LLM" in log_output
    assert "Tool Execution API call" in log_output
    assert "Response Generation LLM" in log_output
