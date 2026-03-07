"""Tests for feature gate enforcement on DATEV, API Keys, Contacts, and Invoices."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base, Organization, OrganizationMember
from app.database import get_db
from app.config import settings


@pytest.fixture
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
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
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


def _register_user(client, email, org_name="Test GmbH"):
    """Helper: register and return access token."""
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "full_name": "Test User",
        "organization_name": org_name,
    })
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["access_token"]


def _set_org_plan(db_session, token, client, plan):
    """Helper: set the org plan for the user behind token."""
    from app.auth_jwt import decode_token
    payload = decode_token(token)
    user_id = int(payload["sub"])
    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id
    ).first()
    org = db_session.query(Organization).filter(
        Organization.id == member.organization_id
    ).first()
    org.plan = plan
    db_session.commit()


class TestDATEVGating:
    """DATEV export should require datev_export feature (Starter+)."""

    def test_free_plan_blocked(self, client, db_session):
        token = _register_user(client, "datev-free@test.de")
        with patch("app.feature_gate.settings") as mock:
            mock.cloud_mode = True
            resp = client.get(
                "/api/datev/export?from_month=2026-01&to_month=2026-01",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 403
            assert "datev_export" in resp.json()["detail"]

    def test_starter_plan_allowed(self, client, db_session):
        token = _register_user(client, "datev-starter@test.de")
        _set_org_plan(db_session, token, client, "starter")
        with patch("app.feature_gate.settings") as mock:
            mock.cloud_mode = True
            resp = client.get(
                "/api/datev/export?from_month=2026-01&to_month=2026-01",
                headers={"Authorization": f"Bearer {token}"},
            )
            # 200 = feature allowed (may return empty ZIP or validation error, but not 403)
            assert resp.status_code != 403

    def test_self_hosted_bypass(self, client, db_session):
        token = _register_user(client, "datev-sh@test.de")
        with patch("app.feature_gate.settings") as mock:
            mock.cloud_mode = False
            resp = client.get(
                "/api/datev/export?from_month=2026-01&to_month=2026-01",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code != 403


class TestAPIKeysGating:
    """API key management should require api_access feature (Starter+)."""

    def test_free_plan_blocked_list(self, client, db_session):
        token = _register_user(client, "apikey-free@test.de")
        with patch("app.feature_gate.settings") as mock:
            mock.cloud_mode = True
            resp = client.get(
                "/api/api-keys",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 403
            assert "api_access" in resp.json()["detail"]

    def test_free_plan_blocked_create(self, client, db_session):
        token = _register_user(client, "apikey-free2@test.de")
        with patch("app.feature_gate.settings") as mock:
            mock.cloud_mode = True
            resp = client.post(
                "/api/api-keys",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Test Key", "scopes": ["invoices:read"]},
            )
            assert resp.status_code == 403

    def test_starter_plan_allowed(self, client, db_session):
        token = _register_user(client, "apikey-starter@test.de")
        _set_org_plan(db_session, token, client, "starter")
        with patch("app.feature_gate.settings") as mock:
            mock.cloud_mode = True
            resp = client.get(
                "/api/api-keys",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200


class TestContactLimitGating:
    """Free plan should be limited to 10 contacts."""

    def test_free_plan_contact_limit(self, client, db_session):
        token = _register_user(client, "contact-limit@test.de")
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.feature_gate.settings") as mock:
            mock.cloud_mode = True
            # Create 10 contacts (should succeed)
            for i in range(10):
                resp = client.post(
                    "/api/contacts",
                    headers=headers,
                    json={"name": f"Kunde {i}", "type": "customer"},
                )
                assert resp.status_code == 201, f"Contact {i} failed: {resp.text}"

            # 11th contact should be blocked
            resp = client.post(
                "/api/contacts",
                headers=headers,
                json={"name": "Kunde 11", "type": "customer"},
            )
            assert resp.status_code == 403
            assert "Limit" in resp.json()["detail"]

    def test_starter_plan_unlimited_contacts(self, client, db_session):
        token = _register_user(client, "contact-starter@test.de")
        _set_org_plan(db_session, token, client, "starter")
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.feature_gate.settings") as mock:
            mock.cloud_mode = True
            # Should be able to create more than 10
            for i in range(11):
                resp = client.post(
                    "/api/contacts",
                    headers=headers,
                    json={"name": f"Kunde {i}", "type": "customer"},
                )
                assert resp.status_code == 201, f"Contact {i} failed: {resp.text}"
