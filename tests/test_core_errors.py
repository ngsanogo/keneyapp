# flake8: noqa: E402
import os

os.environ["TESTING"] = "true"

import json
import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from app.core.errors import validation_exception_handler, generic_exception_handler


class _FakeRequest:
    """Minimal fake request for testing exception handlers."""

    def __init__(self, path="/test"):
        self.url = type("obj", (object,), {"path": path})()
        self.method = "POST"
        self.headers = {}
        self.state = type("obj", (object,), {"correlation_id": "test-correlation-id"})()


@pytest.mark.asyncio
async def test_validation_exception_handler_structure():
    """Ensure validation_exception_handler returns structured 422 with correlation_id."""

    # Build a minimal validation error
    class DummyModel(BaseModel):
        name: str

    try:
        DummyModel(name=123)  # type error
    except ValidationError as ve:
        exc = RequestValidationError(errors=ve.errors())

    req = _FakeRequest()
    response = await validation_exception_handler(req, exc)

    assert response.status_code == 422
    body = json.loads(response.body.decode())

    # Validate envelope structure
    assert "correlation_id" in body
    assert "error" in body
    assert body["error"]["type"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed."
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) > 0


@pytest.mark.asyncio
async def test_generic_exception_handler_structure():
    """Ensure generic_exception_handler returns structured 500 with correlation_id."""
    req = _FakeRequest()
    exc = RuntimeError("Test error")

    response = await generic_exception_handler(req, exc)

    assert response.status_code == 500
    body = json.loads(response.body.decode())

    # Validate envelope structure
    assert "correlation_id" in body
    assert "error" in body
    assert body["error"]["type"] == "internal_error"
    assert "correlation ID" in body["error"]["message"]
    assert body["error"]["details"] is None
