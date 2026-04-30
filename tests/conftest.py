import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


FAKE_SWAGGER = {
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
def mock_llm(monkeypatch):
    """Patch the Llama singleton so tests never touch the real model file.

    Returns the MagicMock so tests can reconfigure create_chat_completion:
        mock_llm.create_chat_completion.return_value = {"choices": [...]}
    """
    mock = MagicMock()
    mock.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "mock response"}}]
    }

    # Patch where the names are *used*, not where they are defined.
    # main.py: `from app.llm.llm import load_llm`
    monkeypatch.setattr("app.main.load_llm", lambda *args, **kwargs: mock)
    # llm_service.py: `from app.llm.llm import get_llm`
    monkeypatch.setattr("app.llm.llm_service.get_llm", lambda *args, **kwargs: mock)

    # Also keep the module globals consistent so any direct import of get_llm
    # from app.llm.llm never tries to load the real model.
    monkeypatch.setattr("app.llm.llm.llm_instance", mock)
    monkeypatch.setattr("app.llm.llm.llm_model_path", "mock_model_path")

    return mock


@pytest.fixture
def mock_swagger(monkeypatch):
    """Patch load_swagger (as imported in main.py) to return a minimal fake spec."""
    monkeypatch.setattr("app.main.load_swagger", lambda *args, **kwargs: FAKE_SWAGGER)
    return FAKE_SWAGGER


@pytest.fixture
def client(mock_llm, mock_swagger):
    """FastAPI TestClient with both LLM and Swagger mocks applied.

    Uses the context-manager form so the lifespan (which calls load_llm and
    load_swagger) runs with the patches already in place.
    """
    from app.main import app

    with TestClient(app) as c:
        yield c
