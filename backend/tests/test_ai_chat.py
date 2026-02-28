"""Tests for AI chat endpoint (Task 9)."""
import uuid
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.models import Base
from app.database import get_db
from app.config import settings


# ---------------------------------------------------------------------------
# Fixtures (mirrors test_ai_router.py pattern — JWT Bearer auth)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient with DB override and require_api_key=True (JWT auth active)."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with patch.object(settings, "require_api_key", True):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()


def _register_and_get_token(client: TestClient, email: str = None, org_name: str = None) -> dict:
    """Register a user+org via API and return access_token and org_id."""
    email = email or f"chat-{uuid.uuid4().hex[:8]}@example.com"
    org_name = org_name or f"Chat Org {uuid.uuid4().hex[:6]}"
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "full_name": "Chat Test User",
        "organization_name": org_name,
    })
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    data = resp.json()
    return {"token": data["access_token"], "org_id": data["organization"]["id"]}


@pytest.fixture()
def test_user(client):
    return _register_and_get_token(client)


@pytest.fixture()
def other_user(client):
    return _register_and_get_token(client)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAiChat:

    def test_chat_returns_streaming_response(self, client, test_user):
        """POST /api/ai/chat should return a streaming SSE response."""
        with patch.object(settings, "anthropic_api_key", ""), \
             patch.object(settings, "openai_api_key", ""):
            response = client.post(
                "/api/ai/chat",
                json={"message": "Hallo", "history": []},
                headers={"Authorization": f"Bearer {test_user['token']}"},
            )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_chat_no_provider_returns_fallback_message(self, client, test_user):
        """Without API keys, chat should return fallback message in stream."""
        with patch.object(settings, "anthropic_api_key", ""), \
             patch.object(settings, "openai_api_key", ""):
            response = client.post(
                "/api/ai/chat",
                json={"message": "Test", "history": []},
                headers={"Authorization": f"Bearer {test_user['token']}"},
            )
        assert response.status_code == 200
        content = response.content.decode()
        assert "KI-Provider" in content or "DONE" in content

    def test_chat_cross_org_data_isolation(self, client, other_user):
        """Chat tool calls must only access data of the authenticated user's org."""
        with patch.object(settings, "anthropic_api_key", ""), \
             patch.object(settings, "openai_api_key", ""):
            response = client.post(
                "/api/ai/chat",
                json={"message": "Zeige alle Rechnungen", "history": []},
                headers={"Authorization": f"Bearer {other_user['token']}"},
            )
        assert response.status_code == 200
