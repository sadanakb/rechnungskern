"""Tests for Phase 12 portal payment endpoints."""
import os
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("REQUIRE_API_KEY", "false")

from app.main import app
from app.models import (
    Base, Organization, OrganizationMember, User, Invoice,
    InvoiceShareLink, PortalPaymentIntent
)
from app.database import get_db


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _setup_portal(db_session, onboarded=True, paypal_link=None):
    """Create org + invoice + share link. Returns (token, org, invoice, link)."""
    org = Organization(
        name="Payment Test Org",
        slug=f"payment-test-{uuid.uuid4().hex[:8]}",
        stripe_connect_account_id="acct_test_portal" if onboarded else None,
        stripe_connect_onboarded=onboarded,
        paypal_link=paypal_link,
    )
    db_session.add(org)
    db_session.flush()

    invoice = Invoice(
        invoice_number="TEST-001",
        organization_id=org.id,
        gross_amount=119.00,
        net_amount=100.00,
        tax_amount=19.00,
        tax_rate=19,
        currency="EUR",
        payment_status="unpaid",
    )
    db_session.add(invoice)
    db_session.flush()

    token = str(uuid.uuid4())
    link = InvoiceShareLink(
        invoice_id=invoice.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        created_by_user_id=1,
        access_count=0,
    )
    db_session.add(link)
    db_session.commit()
    return token, org, invoice, link


def test_create_payment_intent_returns_client_secret(client, db_session):
    token, org, invoice, link = _setup_portal(db_session, onboarded=True)
    with patch("app.routers.portal.stripe_service.create_portal_payment_intent") as mock_pi:
        mock_pi.return_value = {
            "intent_id": "pi_test_001",
            "client_secret": "pi_test_001_secret",
            "status": "requires_payment_method",
        }
        res = client.post(f"/api/portal/{token}/create-payment-intent")
    assert res.status_code == 200
    data = res.json()
    assert "client_secret" in data
    assert data["amount"] == 11900  # 119.00 EUR in cents
    assert data["currency"] == "EUR"


def test_create_payment_intent_idempotent(client, db_session):
    """Second call returns existing created intent, no new Stripe call."""
    token, org, invoice, link = _setup_portal(db_session, onboarded=True)
    existing_ppi = PortalPaymentIntent(
        invoice_id=invoice.id,
        share_link_id=link.id,
        stripe_intent_id="pi_existing_001",
        client_secret="pi_existing_001_secret_xyz",
        amount_cents=11900,
        fee_cents=60,
        status="created",
    )
    db_session.add(existing_ppi)
    db_session.commit()

    with patch("app.routers.portal.stripe_service.create_portal_payment_intent") as mock_pi:
        res = client.post(f"/api/portal/{token}/create-payment-intent")
    mock_pi.assert_not_called()
    assert res.status_code == 200
    data = res.json()
    assert data["intent_id"] == "pi_existing_001"
    assert data["client_secret"] == "pi_existing_001_secret_xyz"


def test_create_payment_intent_fails_if_org_not_onboarded(client, db_session):
    token, _, _, _ = _setup_portal(db_session, onboarded=False)
    res = client.post(f"/api/portal/{token}/create-payment-intent")
    assert res.status_code == 409


def test_create_payment_intent_fails_if_already_paid(client, db_session):
    token, org, invoice, _ = _setup_portal(db_session, onboarded=True)
    invoice.payment_status = "paid"
    db_session.commit()
    res = client.post(f"/api/portal/{token}/create-payment-intent")
    assert res.status_code == 409


def test_portal_get_returns_payment_info(client, db_session):
    """GET /{token} includes stripe_payment_enabled and paypal_link."""
    token, _, _, _ = _setup_portal(db_session, onboarded=True, paypal_link="https://paypal.me/testorg")
    res = client.get(f"/api/portal/{token}")
    assert res.status_code == 200
    data = res.json()
    assert data["stripe_payment_enabled"] is True
    assert data["paypal_link"] == "https://paypal.me/testorg"


def test_payment_status_returns_unpaid(client, db_session):
    token, _, invoice, _ = _setup_portal(db_session, onboarded=True)
    res = client.get(f"/api/portal/{token}/payment-status")
    assert res.status_code == 200
    assert res.json()["payment_status"] == "unpaid"


def test_existing_portal_endpoints_still_work(client, db_session):
    """Confirm that existing GET and POST /confirm-payment still work after refactor."""
    token, _, invoice, _ = _setup_portal(db_session, onboarded=True)
    # GET still works
    res = client.get(f"/api/portal/{token}")
    assert res.status_code == 200
    assert "invoice_number" in res.json()
    # confirm-payment still works
    res = client.post(f"/api/portal/{token}/confirm-payment")
    assert res.status_code == 200
