import pytest
import requests
from unittest.mock import MagicMock

from app.tools.executor import execute_tool
from app.core.config import BASE_URL


class _MockResponse:
    """Minimal stand-in for requests.Response.

    Only the three attributes that executor.py touches are provided:
    status_code, text (used in the error message), and json().
    """

    def __init__(self, json_data, status_code=200, text="ok"):
        self._json = json_data
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._json


def _get_tool(path="/employees"):
    """Return a minimal parsed-tool dict for a GET endpoint."""
    return {"name": "get_employees", "method": "GET", "path": path}


def test_bearer_token_forwarded(monkeypatch):
    """Verify the auth_token is forwarded verbatim in the Authorization header.

    The executor stores auth_token directly as headers["Authorization"] with no
    modification. This test passes a full 'Bearer <token>' string and asserts
    that the outgoing request carries it unchanged — the upstream HRMS API must
    receive exactly what the client sent, otherwise the proxied credential is
    silently corrupted.
    """
    mock_get = MagicMock(return_value=_MockResponse({}, 200))
    monkeypatch.setattr(requests, "get", mock_get)

    execute_tool(_get_tool(), {}, "Bearer secret-token-123")

    outgoing_headers = mock_get.call_args.kwargs["headers"]
    assert outgoing_headers["Authorization"] == "Bearer secret-token-123"


def test_get_request_succeeds(monkeypatch):
    """Verify execute_tool returns the parsed JSON body on a 200 response.

    The executor calls response.json() and returns it directly — no wrapping,
    no filtering. This test confirms that the caller receives the exact dict
    the HRMS API returned, which the orchestrator later passes to the LLM.
    """
    payload = {"employees": [{"id": 1, "name": "Alice"}]}
    mock_get = MagicMock(return_value=_MockResponse(payload, 200))
    monkeypatch.setattr(requests, "get", mock_get)

    result = execute_tool(_get_tool(), {}, "Bearer token")

    assert result == payload


def test_api_error_returns_gracefully(monkeypatch):
    """Verify a non-200 response raises an Exception with a clear message.

    The executor raises Exception(f"API failed: {response.text}") for any
    status other than 200. This test asserts that the exception propagates
    (not swallowed) and that its message contains "API failed" so the
    orchestrator/caller can present a meaningful error rather than an
    AttributeError from trying to call .json() on an error response.
    """
    mock_get = MagicMock(
        return_value=_MockResponse(None, 500, text="Internal Server Error")
    )
    monkeypatch.setattr(requests, "get", mock_get)

    with pytest.raises(Exception, match="API failed"):
        execute_tool(_get_tool(), {}, "Bearer token")


def test_url_constructed_correctly(monkeypatch):
    """Verify the outgoing request URL is BASE_URL + tool['path'].

    URL construction is a simple concatenation with no separator normalisation
    — if tool['path'] is missing the leading slash, or BASE_URL has a trailing
    slash, the URL will be wrong. This test pins the expected shape so that a
    config change or path format change breaks loudly rather than silently
    routing to a wrong endpoint.
    """
    mock_get = MagicMock(return_value=_MockResponse({}, 200))
    monkeypatch.setattr(requests, "get", mock_get)

    execute_tool(_get_tool("/employees"), {}, "Bearer token")

    # url is the first positional argument to requests.get
    called_url = mock_get.call_args.args[0]
    assert called_url == BASE_URL + "/employees"
