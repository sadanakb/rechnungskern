"""
Tests for Quote (Angebot) feature — CRUD, status transitions, conversion, tenant isolation.
"""
import pytest
from datetime import date

from app.models import Quote, Invoice, Organization, User, OrganizationMember


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
    def test_create_quote_success(self, client, db_session):
        """POST /api/quotes/create should create a quote with calculated amounts."""
        _create_org(db_session, slug="create-org")
        resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        assert resp.status_code == 200
        body = resp.json()

        # Verify quote_id generated
        assert body["quote_id"].startswith("ANB-")
        assert body["status"] == "draft"

        # Verify amounts calculated: 10*150 + 5*200 = 2500 net
        assert float(body["net_amount"]) == 2500.0
        assert float(body["gross_amount"]) == 2975.0  # 2500 + 19%

    def test_create_quote_empty_line_items(self, client, db_session):
        """Create quote with no line items should work (zero amounts)."""
        _create_org(db_session, slug="empty-items-org")
        data = {
            "seller_name": "Test GmbH",
            "buyer_name": "Kunde AG",
        }
        resp = client.post("/api/quotes/create", json=data)
        assert resp.status_code == 200
        body = resp.json()
        assert body["quote_id"].startswith("ANB-")
        assert float(body.get("net_amount") or 0) == 0.0

    def test_create_quote_auto_date(self, client, db_session):
        """Quote without quote_date should default to today."""
        _create_org(db_session, slug="auto-date-org")
        data = {"seller_name": "Test"}
        resp = client.post("/api/quotes/create", json=data)
        assert resp.status_code == 200
        body = resp.json()
        assert body["quote_date"] == str(date.today())


# ---------------------------------------------------------------------------
# C7.2 — List quotes (with org isolation)
# ---------------------------------------------------------------------------

class TestListQuotes:
    def test_list_quotes_empty(self, client, db_session):
        """List quotes when there are none should return empty list."""
        resp = client.get("/api/quotes/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["quotes"] == []
        assert body["total"] == 0

    def test_list_quotes_with_data(self, client, db_session):
        """List quotes should return created quotes."""
        _create_org(db_session, slug="list-org")
        # Create two quotes
        client.post("/api/quotes/create", json={**SAMPLE_QUOTE_DATA, "buyer_name": "A"})
        client.post("/api/quotes/create", json={**SAMPLE_QUOTE_DATA, "buyer_name": "B"})

        resp = client.get("/api/quotes/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2

    def test_list_quotes_filter_status(self, client, db_session):
        """Filter by status should work."""
        _create_org(db_session, slug="filter-status-org")
        client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)

        resp = client.get("/api/quotes/list?status=draft")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = client.get("/api/quotes/list?status=sent")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_quotes_search(self, client, db_session):
        """Search by buyer_name should work."""
        _create_org(db_session, slug="search-org")
        client.post("/api/quotes/create", json={**SAMPLE_QUOTE_DATA, "buyer_name": "UniqueCompany123"})
        client.post("/api/quotes/create", json={**SAMPLE_QUOTE_DATA, "buyer_name": "OtherFirm"})

        resp = client.get("/api/quotes/list?search=UniqueCompany123")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


# ---------------------------------------------------------------------------
# C7.3 — Get quote detail
# ---------------------------------------------------------------------------

class TestGetQuote:
    def test_get_quote_success(self, client, db_session):
        """GET /api/quotes/{quote_id} should return full detail."""
        _create_org(db_session, slug="get-detail-org")
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

    def test_get_quote_not_found(self, client, db_session):
        """GET nonexistent quote should return 404."""
        resp = client.get("/api/quotes/ANB-20260301-nonexist")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# C7.4 — Update quote
# ---------------------------------------------------------------------------

class TestUpdateQuote:
    def test_update_quote(self, client, db_session):
        """PUT /api/quotes/{quote_id} should update fields."""
        _create_org(db_session, slug="update-org")
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

    def test_update_quote_recalculates_amounts(self, client, db_session):
        """Updating line_items should recalculate amounts."""
        _create_org(db_session, slug="recalc-org")
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
    def test_delete_draft_quote(self, client, db_session):
        """DELETE draft quote should succeed."""
        _create_org(db_session, slug="delete-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.delete(f"/api/quotes/{qid}")
        assert resp.status_code == 200

        # Verify deleted
        resp = client.get(f"/api/quotes/{qid}")
        assert resp.status_code == 404

    def test_delete_sent_quote_fails(self, client, db_session):
        """DELETE a sent quote should fail with 400."""
        _create_org(db_session, slug="delete-sent-org")
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
    def test_send_quote(self, client, db_session):
        """POST /api/quotes/{quote_id}/send changes status to 'sent'."""
        _create_org(db_session, slug="send-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.post(f"/api/quotes/{qid}/send")
        assert resp.status_code == 200
        assert resp.json()["status"] == "sent"

    def test_accept_quote(self, client, db_session):
        """POST /api/quotes/{quote_id}/accept changes status to 'accepted'."""
        _create_org(db_session, slug="accept-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        # Must be sent first
        client.post(f"/api/quotes/{qid}/send")

        resp = client.post(f"/api/quotes/{qid}/accept")
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    def test_accept_draft_fails(self, client, db_session):
        """Accept a draft quote should fail."""
        _create_org(db_session, slug="accept-draft-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.post(f"/api/quotes/{qid}/accept")
        assert resp.status_code == 400

    def test_reject_quote(self, client, db_session):
        """POST /api/quotes/{quote_id}/reject changes status to 'rejected'."""
        _create_org(db_session, slug="reject-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        # Must be sent first
        client.post(f"/api/quotes/{qid}/send")

        resp = client.post(f"/api/quotes/{qid}/reject")
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_reject_draft_fails(self, client, db_session):
        """Reject a draft quote should fail."""
        _create_org(db_session, slug="reject-draft-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.post(f"/api/quotes/{qid}/reject")
        assert resp.status_code == 400

    def test_send_already_sent_fails(self, client, db_session):
        """Sending an already-sent quote should fail."""
        _create_org(db_session, slug="double-send-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        client.post(f"/api/quotes/{qid}/send")
        resp = client.post(f"/api/quotes/{qid}/send")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# C7.7 — Convert to invoice
# ---------------------------------------------------------------------------

class TestConvertToInvoice:
    def test_convert_accepted_quote(self, client, db_session):
        """Convert an accepted quote should create a new invoice."""
        _create_org(db_session, slug="convert-org")
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

    def test_convert_draft_quote(self, client, db_session):
        """Convert a draft quote should also work."""
        _create_org(db_session, slug="convert-draft-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        resp = client.post(f"/api/quotes/{qid}/convert")
        assert resp.status_code == 200
        assert resp.json()["quote_status"] == "converted"

    def test_convert_already_converted_fails(self, client, db_session):
        """Converting an already-converted quote should fail."""
        _create_org(db_session, slug="double-convert-org")
        create_resp = client.post("/api/quotes/create", json=SAMPLE_QUOTE_DATA)
        qid = create_resp.json()["quote_id"]

        client.post(f"/api/quotes/{qid}/convert")
        resp = client.post(f"/api/quotes/{qid}/convert")
        assert resp.status_code == 400

    def test_convert_rejected_quote_fails(self, client, db_session):
        """Converting a rejected quote should fail."""
        _create_org(db_session, slug="convert-rejected-org")
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
    def test_org_isolation_list(self, client, db_session):
        """Quotes from different orgs should not leak across tenants.

        In dev mode (REQUIRE_API_KEY=false), org_id is None so all quotes
        are visible. This test creates quotes with different org_ids directly
        in the DB and verifies the query filter works at the model level.
        """
        org_a = _create_org(db_session, name="Org A", slug="org-a")
        org_b = _create_org(db_session, name="Org B", slug="org-b")

        # Insert quotes directly with specific org_ids
        import uuid
        q_a = Quote(
            quote_id=f"ANB-20260301-{uuid.uuid4().hex[:6]}",
            status="draft",
            organization_id=org_a.id,
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

        # Query filtered by org A
        from sqlalchemy import select
        quotes_a = db_session.query(Quote).filter(
            Quote.organization_id == org_a.id
        ).all()
        assert len(quotes_a) == 1
        assert quotes_a[0].buyer_name == "Client A"

        # Query filtered by org B
        quotes_b = db_session.query(Quote).filter(
            Quote.organization_id == org_b.id
        ).all()
        assert len(quotes_b) == 1
        assert quotes_b[0].buyer_name == "Client B"

    def test_ensure_quote_belongs_to_org(self, db_session):
        """_ensure_quote_belongs_to_org should raise 404 for wrong org."""
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

        # Different org — should raise
        with pytest.raises(HTTPException) as exc_info:
            _ensure_quote_belongs_to_org(quote, str(org.id + 999))
        assert exc_info.value.status_code == 404

        # None org (dev mode) — should not raise
        _ensure_quote_belongs_to_org(quote, None)


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
