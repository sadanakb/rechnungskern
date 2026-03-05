"""
Tests for Quote (Angebot) feature — CRUD, status transitions, conversion, tenant isolation.
"""
import pytest
from datetime import date

from fastapi.testclient import TestClient

from app.models import Quote, Invoice, Organization, User, OrganizationMember
from app.auth_jwt import get_current_user
from app.database import get_db
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_org(db, name="Test GmbH", slug="test-gmbh", org_id=None):
    """Create an organization in the test DB."""
    org = Organization(name=name, slug=slug)
    if org_id is not None:
        org.id = org_id
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _create_user_and_member(db, org, email="user@test.de", role="owner"):
    """Create a user and link them to an org."""
    user = User(
        email=email,
        hashed_password="$bcrypt_sha256$$2b$12$dummyhash",
        full_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    member = OrganizationMember(
        user_id=user.id,
        organization_id=org.id,
        role=role,
    )
    db.add(member)
    db.commit()
    return user


# ---------------------------------------------------------------------------
# Fixtures — override get_current_user so org_id is present
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def test_org(db_session):
    """Create a test organization and return it."""
    org = _create_org(db_session, name="Quote Test Org", slug="quote-test-org")
    return org


@pytest.fixture(scope="function")
def client(db_session, test_org):
    """FastAPI TestClient with overridden DB dependency AND get_current_user.

    The security fixes now require org_id in the JWT token (tenant isolation).
    We override get_current_user to return the test org's ID so all quote
    endpoints can verify org membership.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    async def _override_get_current_user():
        return {
            "user_id": "1",
            "email": "test@quote-test.de",
            "role": "owner",
            "org_id": str(test_org.id),
        }

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


SAMPLE_QUOTE_DATA = {
    "quote_date": "2026-03-01",
    "valid_until": "2026-04-01",
    "seller_name": "Musterfirma GmbH",
    "seller_vat_id": "DE123456789",
    "seller_address": "Musterstr. 1, 60311 Frankfurt",
    "buyer_name": "Kaeufer AG",
    "buyer_vat_id": "DE987654321",
    "buyer_address": "Hauptstr. 5, 10115 Berlin",
    "tax_rate": "19.00",
    "currency": "EUR",
    "line_items": [
        {
            "description": "Beratungsleistung",
            "quantity": "10",
            "unit_price": "150.00",
        },
        {
            "description": "Softwareentwicklung",
            "quantity": "5",
            "unit_price": "200.00",
        },
    ],
    "intro_text": "Vielen Dank fuer Ihre Anfrage.",
    "closing_text": "Wir freuen uns auf Ihre Rueckmeldung.",
}


# ---------------------------------------------------------------------------
# C7.1 — Create quote
# ---------------------------------------------------------------------------

class TestCreateQuote:
    def test_create_quote_success(self, client, db_session, test_org):
        """POST /api/quotes/create should create a quote with calculated amounts."""
        resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        assert resp.status_code == 200
        body = resp.json()

        # Verify quote_id generated
        assert body["quote_id"].startswith("ANB-")
        assert body["status"] == "draft"

        # Verify amounts calculated: 10*150 + 5*200 = 2500 net
        assert float(body["net_amount"]) == 2500.0
        assert float(body["gross_amount"]) == 2975.0  # 2500 + 19%

    def test_create_quote_empty_line_items(self, client, db_session, test_org):
        """Create quote with no line items should work (zero amounts)."""
        data = {
            "seller_name": "Test GmbH",
            "buyer_name": "Kunde AG",
        }
        resp = client.post("/api/quotes/create", json=data)
        assert resp.status_code == 200
        body = resp.json()
        assert body["quote_id"].startswith("ANB-")
        assert float(body.get("net_amount") or 0) == 0.0

    def test_create_quote_auto_date(self, client, db_session, test_org):
        """Quote without quote_date should default to today."""
        data = {"seller_name": "Test"}
        resp = client.post("/api/quotes/create", json=data)
        assert resp.status_code == 200
        body = resp.json()
        assert body["quote_date"] == str(date.today())


# ---------------------------------------------------------------------------
# C7.2 — List quotes (with org isolation)
# ---------------------------------------------------------------------------

class TestListQuotes:
    def test_list_quotes_empty(self, client, db_session, test_org):
        """List quotes when there are none should return empty list."""
        resp = client.get("/api/quotes/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["quotes"] == []
        assert body["total"] == 0

    def test_list_quotes_with_data(self, client, db_session, test_org):
        """List quotes should return created quotes."""
        # Create two quotes
        client.post("/api/quotes/create", json={**SAMPLE_QUOTE_DATA, "buyer_name": "A"})
        client.post("/api/quotes/create", json={**SAMPLE_QUOTE_DATA, "buyer_name": "B"})

        resp = client.get("/api/quotes/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2

    def test_list_quotes_filter_status(self, client, db_session, test_org):
        """Filter by status should work."""
        client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)

        resp = client.get("/api/quotes/list?status=draft")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = client.get("/api/quotes/list?status=sent")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_quotes_search(self, client, db_session, test_org):
        """Search by buyer_name should work."""
        client.post("/api/quotes/create", json={**SAMPLE_QUOTE_DATA, "buyer_name": "UniqueCompany123"})
        client.post("/api/quotes/create", json={**SAMPLE_QUOTE_DATA, "buyer_name": "OtherFirm"})

        resp = client.get("/api/quotes/list?search=UniqueCompany123")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


# ---------------------------------------------------------------------------
# C7.3 — Get quote detail
# ---------------------------------------------------------------------------

class TestGetQuote:
    def test_get_quote_success(self, client, db_session, test_org):
        """GET /api/quotes/{quote_id} should return full detail."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.get(f"/api/quotes/{qid}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["quote_id"] == qid
        assert body["seller_name"] == "Musterfirma GmbH"
        assert body["buyer_name"] == "Kaeufer AG"
        assert body["intro_text"] == "Vielen Dank fuer Ihre Anfrage."
        assert body["line_items"] is not None
        assert len(body["line_items"]) == 2

    def test_get_quote_not_found(self, client, db_session, test_org):
        """GET nonexistent quote should return 404."""
        resp = client.get("/api/quotes/ANB-20260301-nonexist")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# C7.4 — Update quote
# ---------------------------------------------------------------------------

class TestUpdateQuote:
    def test_update_quote(self, client, db_session, test_org):
        """PUT /api/quotes/{quote_id} should update fields."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.put(f"/api/quotes/{qid}", json={
            "buyer_name": "Neuer Kaeufer GmbH",
            "closing_text": "Updated closing",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["buyer_name"] == "Neuer Kaeufer GmbH"
        assert body["closing_text"] == "Updated closing"

    def test_update_quote_recalculates_amounts(self, client, db_session, test_org):
        """Updating line_items should recalculate amounts."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.put(f"/api/quotes/{qid}", json={
            "line_items": [
                {"description": "Single item", "quantity": "1", "unit_price": "1000.00"},
            ],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert float(body["net_amount"]) == 1000.0
        assert float(body["gross_amount"]) == 1190.0  # 1000 + 19%


# ---------------------------------------------------------------------------
# C7.5 — Delete quote (only draft)
# ---------------------------------------------------------------------------

class TestDeleteQuote:
    def test_delete_draft_quote(self, client, db_session, test_org):
        """DELETE draft quote should succeed."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.delete(f"/api/quotes/{qid}")
        assert resp.status_code == 200

        # Verify deleted
        resp = client.get(f"/api/quotes/{qid}")
        assert resp.status_code == 404

    def test_delete_sent_quote_fails(self, client, db_session, test_org):
        """DELETE a sent quote should fail with 400."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        # Send the quote first
        client.post(f"/api/quotes/{qid}/send")

        # Try to delete
        resp = client.delete(f"/api/quotes/{qid}")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# C7.6 — Status transitions: send, accept, reject
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    def test_send_quote(self, client, db_session, test_org):
        """POST /api/quotes/{quote_id}/send changes status to 'sent'."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.post(f"/api/quotes/{qid}/send")
        assert resp.status_code == 200
        assert resp.json()["status"] == "sent"

    def test_accept_quote(self, client, db_session, test_org):
        """POST /api/quotes/{quote_id}/accept changes status to 'accepted'."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        # Must be sent first
        client.post(f"/api/quotes/{qid}/send")

        resp = client.post(f"/api/quotes/{qid}/accept")
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    def test_accept_draft_fails(self, client, db_session, test_org):
        """Accept a draft quote should fail."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.post(f"/api/quotes/{qid}/accept")
        assert resp.status_code == 400

    def test_reject_quote(self, client, db_session, test_org):
        """POST /api/quotes/{quote_id}/reject changes status to 'rejected'."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        # Must be sent first
        client.post(f"/api/quotes/{qid}/send")

        resp = client.post(f"/api/quotes/{qid}/reject")
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_reject_draft_fails(self, client, db_session, test_org):
        """Reject a draft quote should fail."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.post(f"/api/quotes/{qid}/reject")
        assert resp.status_code == 400

    def test_send_already_sent_fails(self, client, db_session, test_org):
        """Sending an already-sent quote should fail."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        client.post(f"/api/quotes/{qid}/send")
        resp = client.post(f"/api/quotes/{qid}/send")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# C7.7 — Convert to invoice
# ---------------------------------------------------------------------------

class TestConvertToInvoice:
    def test_convert_accepted_quote(self, client, db_session, test_org):
        """Convert an accepted quote should create a new invoice."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        # Send and accept
        client.post(f"/api/quotes/{qid}/send")
        client.post(f"/api/quotes/{qid}/accept")

        # Convert
        resp = client.post(f"/api/quotes/{qid}/convert")
        assert resp.status_code == 200
        body = resp.json()
        assert body["quote_status"] == "converted"
        assert body["invoice_id"].startswith("INV-")

        # Verify the invoice was created in DB
        invoice = db_session.query(Invoice).filter(
            Invoice.invoice_id == body["invoice_id"]
        ).first()
        assert invoice is not None
        assert invoice.buyer_name == "Kaeufer AG"
        assert invoice.seller_name == "Musterfirma GmbH"
        assert float(invoice.net_amount) == 2500.0
        assert invoice.source_type == "quote"

        # Verify quote is now 'converted'
        quote = db_session.query(Quote).filter(Quote.quote_id == qid).first()
        assert quote.status == "converted"
        assert quote.converted_invoice_id == invoice.id

    def test_convert_draft_quote_fails(self, client, db_session, test_org):
        """Convert a draft quote should fail (only accepted quotes can convert)."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.post(f"/api/quotes/{qid}/convert")
        assert resp.status_code == 400

    def test_convert_already_converted_fails(self, client, db_session, test_org):
        """Converting an already-converted quote should fail."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        # Must send, accept, then convert
        client.post(f"/api/quotes/{qid}/send")
        client.post(f"/api/quotes/{qid}/accept")
        resp = client.post(f"/api/quotes/{qid}/convert")
        assert resp.status_code == 200

        # Second conversion should fail
        resp = client.post(f"/api/quotes/{qid}/convert")
        assert resp.status_code == 400

    def test_convert_rejected_quote_fails(self, client, db_session, test_org):
        """Converting a rejected quote should fail."""
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        client.post(f"/api/quotes/{qid}/send")
        client.post(f"/api/quotes/{qid}/reject")

        resp = client.post(f"/api/quotes/{qid}/convert")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# C7.8 — Tenant isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    def test_org_isolation_list(self, client, db_session, test_org):
        """Quotes from different orgs should not leak across tenants.

        The test client is authenticated as test_org. Quotes belonging to a
        different org should not be visible in the list endpoint.
        """
        org_b = _create_org(db_session, name="Org B", slug="org-b")

        # Insert quotes directly with specific org_ids
        import uuid
        q_a = Quote(
            quote_id=f"ANB-20260301-{uuid.uuid4().hex[:6]}",
            status="draft",
            organization_id=test_org.id,
            buyer_name="Client A",
        )
        q_b = Quote(
            quote_id=f"ANB-20260301-{uuid.uuid4().hex[:6]}",
            status="draft",
            organization_id=org_b.id,
            buyer_name="Client B",
        )
        db_session.add_all([q_a, q_b])
        db_session.commit()

        # Query filtered by test_org (via API — uses authenticated org_id)
        resp = client.get("/api/quotes/list")
        assert resp.status_code == 200
        body = resp.json()
        # Should only see quotes from test_org, not org_b
        assert body["total"] == 1
        assert body["quotes"][0]["buyer_name"] == "Client A"

        # Also verify at model level
        from sqlalchemy import select
        quotes_a = db_session.query(Quote).filter(
            Quote.organization_id == test_org.id
        ).all()
        assert len(quotes_a) == 1
        assert quotes_a[0].buyer_name == "Client A"

        quotes_b = db_session.query(Quote).filter(
            Quote.organization_id == org_b.id
        ).all()
        assert len(quotes_b) == 1
        assert quotes_b[0].buyer_name == "Client B"

    def test_ensure_quote_belongs_to_org(self, db_session):
        """_ensure_quote_belongs_to_org should raise 401 for None org and 404 for wrong org."""
        from app.routers.quotes import _ensure_quote_belongs_to_org
        from fastapi import HTTPException

        org = _create_org(db_session, slug="iso-org")
        import uuid
        quote = Quote(
            quote_id=f"ANB-20260301-{uuid.uuid4().hex[:6]}",
            status="draft",
            organization_id=org.id,
        )
        db_session.add(quote)
        db_session.commit()
        db_session.refresh(quote)

        # Same org — should not raise
        _ensure_quote_belongs_to_org(quote, str(org.id))

        # Different org — should raise 404
        with pytest.raises(HTTPException) as exc_info:
            _ensure_quote_belongs_to_org(quote, str(org.id + 999))
        assert exc_info.value.status_code == 404

        # None org — should raise 401 (security fix: org_id is now required)
        with pytest.raises(HTTPException) as exc_info:
            _ensure_quote_belongs_to_org(quote, None)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# C7.9 — Quote number service
# ---------------------------------------------------------------------------

class TestQuoteNumberService:
    def test_generate_without_sequence(self, db_session):
        """Without a configured sequence, should return UUID-based number."""
        from app.quote_number_service import generate_next_quote_number
        number = generate_next_quote_number(db_session, org_id=9999)
        assert number.startswith("ANB-")

    def test_generate_with_sequence(self, db_session):
        """With a configured sequence, should return formatted number."""
        from app.models import QuoteNumberSequence
        from app.quote_number_service import generate_next_quote_number

        org = _create_org(db_session, slug="seq-org")
        seq = QuoteNumberSequence(
            organization_id=org.id,
            prefix="ANB",
            separator="-",
            current_counter=0,
            padding=4,
            reset_yearly=True,
        )
        db_session.add(seq)
        db_session.commit()

        num1 = generate_next_quote_number(db_session, org.id)
        assert num1.startswith("ANB-")
        assert num1.endswith("-0001")

        num2 = generate_next_quote_number(db_session, org.id)
        assert num2.endswith("-0002")
