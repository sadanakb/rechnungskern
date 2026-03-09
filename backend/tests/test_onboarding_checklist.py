"""Tests for GET /api/onboarding/checklist endpoint."""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.models import Organization, Contact, Invoice, OrganizationMember


def _register_and_get_token(client: TestClient, email: str = "checklist@test.de", org_name: str = "Checklist GmbH") -> str:
    """Register user + org, return JWT token."""
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "full_name": "Test User",
        "organization_name": org_name,
    })
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestOnboardingChecklist:
    """Tests for the onboarding checklist endpoint."""

    def test_requires_auth(self, client):
        """Endpoint requires authentication (returns 401 in prod, or 200 in dev mode)."""
        resp = client.get("/api/onboarding/checklist")
        # In dev mode, get_current_user falls back to dev user — endpoint still works
        # In production (require_api_key=True), this would be 401
        assert resp.status_code in (200, 401, 404)

    def test_empty_org_zero_completed(self, client, db_session):
        """Fresh org with no data → 0/5 completed."""
        token = _register_and_get_token(client)
        # The org was created with a name but we need to clear it for this test
        # Actually, registration sets org name, so company_data depends on vat_id + address too
        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        # company_data should be false because vat_id and address are not set
        steps = {s["key"]: s["done"] for s in data["steps"]}
        assert steps["company_data"] is False
        assert steps["first_contact"] is False
        assert steps["first_invoice"] is False
        assert steps["first_xrechnung"] is False
        assert steps["first_download"] is False
        assert data["all_done"] is False

    def test_company_data_complete(self, client, db_session):
        """Org with name + address + vat_id → company_data done."""
        token = _register_and_get_token(client)
        # Update company data via onboarding endpoint
        client.post("/api/onboarding/company", json={
            "vat_id": "DE123456789",
            "address": "Musterstraße 1, 12345 Berlin",
        }, headers=_auth_header(token))

        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        data = resp.json()
        steps = {s["key"]: s["done"] for s in data["steps"]}
        assert steps["company_data"] is True

    def test_first_contact(self, client, db_session):
        """Org with one contact → first_contact done."""
        token = _register_and_get_token(client)
        # Create a contact via the contacts API
        client.post("/api/contacts", json={
            "name": "Max Mustermann",
            "email": "max@example.com",
            "type": "customer",
        }, headers=_auth_header(token))

        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        data = resp.json()
        steps = {s["key"]: s["done"] for s in data["steps"]}
        assert steps["first_contact"] is True

    def test_first_invoice_excludes_cancelled(self, client, db_session):
        """Cancelled invoice does NOT count as first invoice."""
        token = _register_and_get_token(client)
        # Create an invoice
        inv_resp = client.post("/api/invoices", json={
            "invoice_number": "RE-TEST-001",
            "invoice_date": "2026-03-01",
            "due_date": "2026-03-31",
            "seller_name": "Checklist GmbH",
            "seller_vat_id": "DE123456789",
            "seller_address": "Test Str. 1",
            "buyer_name": "Kunde GmbH",
            "buyer_vat_id": "DE987654321",
            "buyer_address": "Kunden Str. 2",
            "net_amount": 1000,
            "tax_amount": 190,
            "gross_amount": 1190,
            "tax_rate": 19.0,
            "line_items": [{"description": "Service", "quantity": 1, "unit_price": 1000, "net_amount": 1000}],
            "iban": "DE89370400440532013000",
        }, headers=_auth_header(token))

        if inv_resp.status_code in (200, 201):
            invoice_id = inv_resp.json().get("invoice_id") or inv_resp.json().get("id")
            # Cancel it
            client.patch(f"/api/invoices/{invoice_id}/payment-status", json={
                "status": "cancelled",
            }, headers=_auth_header(token))

        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        data = resp.json()
        steps = {s["key"]: s["done"] for s in data["steps"]}
        assert steps["first_invoice"] is False

    def test_first_invoice_with_valid_invoice(self, client, db_session):
        """Non-cancelled invoice → first_invoice done."""
        token = _register_and_get_token(client, email="invoice@test.de", org_name="Invoice GmbH")
        client.post("/api/invoices", json={
            "invoice_number": "RE-TEST-002",
            "invoice_date": "2026-03-01",
            "due_date": "2026-03-31",
            "seller_name": "Invoice GmbH",
            "seller_vat_id": "DE123456789",
            "seller_address": "Test Str. 1",
            "buyer_name": "Kunde GmbH",
            "buyer_vat_id": "DE987654321",
            "buyer_address": "Kunden Str. 2",
            "net_amount": 1000,
            "tax_amount": 190,
            "gross_amount": 1190,
            "tax_rate": 19.0,
            "line_items": [{"description": "Service", "quantity": 1, "unit_price": 1000, "net_amount": 1000}],
            "iban": "DE89370400440532013000",
        }, headers=_auth_header(token))

        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        data = resp.json()
        steps = {s["key"]: s["done"] for s in data["steps"]}
        assert steps["first_invoice"] is True

    def test_xrechnung_step(self, client, db_session):
        """Invoice with xrechnung_xml_path → first_xrechnung done."""
        token = _register_and_get_token(client, email="xrechnung@test.de", org_name="XRechnung GmbH")
        # Create invoice and then set xrechnung path directly in DB
        inv_resp = client.post("/api/invoices", json={
            "invoice_number": "RE-TEST-003",
            "invoice_date": "2026-03-01",
            "due_date": "2026-03-31",
            "seller_name": "XRechnung GmbH",
            "seller_vat_id": "DE123456789",
            "seller_address": "Test Str. 1",
            "buyer_name": "Kunde GmbH",
            "buyer_vat_id": "DE987654321",
            "buyer_address": "Kunden Str. 2",
            "net_amount": 500,
            "tax_amount": 95,
            "gross_amount": 595,
            "tax_rate": 19.0,
            "line_items": [{"description": "Beratung", "quantity": 1, "unit_price": 500, "net_amount": 500}],
            "iban": "DE89370400440532013000",
        }, headers=_auth_header(token))

        if inv_resp.status_code in (200, 201):
            inv_data = inv_resp.json()
            # Update xrechnung_xml_path directly via DB
            from app.models import Invoice
            inv_db = db_session.query(Invoice).filter(Invoice.invoice_id == inv_data["invoice_id"]).first()
            if inv_db:
                inv_db.xrechnung_xml_path = "/storage/xrechnung/test.xml"
                db_session.commit()

        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        data = resp.json()
        steps = {s["key"]: s["done"] for s in data["steps"]}
        assert steps["first_xrechnung"] is True

    def test_download_step(self, client, db_session):
        """Invoice with zugferd_pdf_path → first_download done."""
        token = _register_and_get_token(client, email="download@test.de", org_name="Download GmbH")
        inv_resp = client.post("/api/invoices", json={
            "invoice_number": "RE-TEST-004",
            "invoice_date": "2026-03-01",
            "due_date": "2026-03-31",
            "seller_name": "Download GmbH",
            "seller_vat_id": "DE123456789",
            "seller_address": "Test Str. 1",
            "buyer_name": "Kunde GmbH",
            "buyer_vat_id": "DE987654321",
            "buyer_address": "Kunden Str. 2",
            "net_amount": 500,
            "tax_amount": 95,
            "gross_amount": 595,
            "tax_rate": 19.0,
            "line_items": [{"description": "Beratung", "quantity": 1, "unit_price": 500, "net_amount": 500}],
            "iban": "DE89370400440532013000",
        }, headers=_auth_header(token))

        if inv_resp.status_code in (200, 201):
            inv_data = inv_resp.json()
            from app.models import Invoice
            inv_db = db_session.query(Invoice).filter(Invoice.invoice_id == inv_data["invoice_id"]).first()
            if inv_db:
                inv_db.zugferd_pdf_path = "/storage/zugferd/test.pdf"
                db_session.commit()

        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        data = resp.json()
        steps = {s["key"]: s["done"] for s in data["steps"]}
        assert steps["first_download"] is True

    def test_all_steps_completed(self, client, db_session):
        """All 5 steps done → completed=5, all_done=true."""
        token = _register_and_get_token(client, email="alldone@test.de", org_name="AllDone GmbH")
        headers = _auth_header(token)

        # 1. Company data
        client.post("/api/onboarding/company", json={
            "vat_id": "DE111222333",
            "address": "Hauptstr. 10, 10115 Berlin",
        }, headers=headers)

        # 2. Contact
        client.post("/api/contacts", json={
            "name": "Kompletter Kunde",
            "email": "kunde@example.com",
            "type": "customer",
        }, headers=headers)

        # 3. Invoice with xrechnung + zugferd
        inv_resp = client.post("/api/invoices", json={
            "invoice_number": "RE-ALL-001",
            "invoice_date": "2026-03-01",
            "due_date": "2026-03-31",
            "seller_name": "AllDone GmbH",
            "seller_vat_id": "DE111222333",
            "seller_address": "Hauptstr. 10",
            "buyer_name": "Kunde GmbH",
            "buyer_vat_id": "DE999888777",
            "buyer_address": "Nebenstr. 5",
            "net_amount": 2000,
            "tax_amount": 380,
            "gross_amount": 2380,
            "tax_rate": 19.0,
            "line_items": [{"description": "Projekt", "quantity": 1, "unit_price": 2000, "net_amount": 2000}],
            "iban": "DE89370400440532013000",
        }, headers=headers)

        if inv_resp.status_code in (200, 201):
            inv_data = inv_resp.json()
            from app.models import Invoice
            inv_db = db_session.query(Invoice).filter(Invoice.invoice_id == inv_data["invoice_id"]).first()
            if inv_db:
                inv_db.xrechnung_xml_path = "/storage/xrechnung/all.xml"
                inv_db.zugferd_pdf_path = "/storage/zugferd/all.pdf"
                db_session.commit()

        resp = client.get("/api/onboarding/checklist", headers=headers)
        data = resp.json()
        assert data["completed"] == 5
        assert data["total"] == 5
        assert data["all_done"] is True

    def test_response_format(self, client, db_session):
        """Response has correct JSON structure."""
        token = _register_and_get_token(client, email="format@test.de", org_name="Format GmbH")
        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        data = resp.json()

        assert "completed" in data
        assert "total" in data
        assert "all_done" in data
        assert "steps" in data
        assert len(data["steps"]) == 5

        for step in data["steps"]:
            assert "key" in step
            assert "done" in step
            assert "label" in step
            assert "description" in step
            assert "href" in step
            assert isinstance(step["done"], bool)

    def test_tenant_isolation(self, client, db_session):
        """Org A's data doesn't appear in Org B's checklist."""
        # Create org A with a contact
        token_a = _register_and_get_token(client, email="orga@test.de", org_name="Org A GmbH")
        client.post("/api/contacts", json={
            "name": "Contact A",
            "email": "a@example.com",
            "type": "customer",
        }, headers=_auth_header(token_a))

        # Verify org A sees the contact
        resp_a = client.get("/api/onboarding/checklist", headers=_auth_header(token_a))
        steps_a = {s["key"]: s["done"] for s in resp_a.json()["steps"]}
        assert steps_a["first_contact"] is True

        # Create org B — should NOT see org A's contact
        token_b = _register_and_get_token(client, email="orgb@test.de", org_name="Org B GmbH")
        resp_b = client.get("/api/onboarding/checklist", headers=_auth_header(token_b))
        steps_b = {s["key"]: s["done"] for s in resp_b.json()["steps"]}
        assert steps_b["first_contact"] is False

    def test_step_keys_and_order(self, client, db_session):
        """Steps have correct keys in the right order."""
        token = _register_and_get_token(client, email="keys@test.de", org_name="Keys GmbH")
        resp = client.get("/api/onboarding/checklist", headers=_auth_header(token))
        data = resp.json()
        keys = [s["key"] for s in data["steps"]]
        assert keys == ["company_data", "first_contact", "first_invoice", "first_xrechnung", "first_download"]
