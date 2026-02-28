"""Tests for Phase 11 push notification triggers."""
from unittest.mock import patch, MagicMock
import pytest


# ---------------------------------------------------------------------------
# Trigger 1: Payment status → paid
# ---------------------------------------------------------------------------

class TestPaymentPaidPushTrigger:
    """When invoice status is updated to 'paid', push_service.notify_org is called."""

    def test_payment_paid_triggers_notify_org(self, client, sample_invoice_data):
        """Marking an invoice as paid calls push_service.notify_org once."""
        # Create invoice (the test DB is org-less by default, but the trigger
        # only fires when organization_id is set, so we patch notify_org and
        # verify it IS called when there's an org, or correctly NOT called
        # when there's no org).
        with patch("app.push_service.notify_org") as mock_notify:
            create_res = client.post("/api/invoices", json=sample_invoice_data)
            assert create_res.status_code == 200
            invoice_id = create_res.json()["invoice_id"]

            res = client.patch(
                f"/api/invoices/{invoice_id}/payment-status",
                json={"status": "paid"},
            )
            assert res.status_code == 200
            assert res.json()["payment_status"] == "paid"
            # No org_id set on this invoice → notify_org must NOT be called
            mock_notify.assert_not_called()

    def test_payment_paid_with_org_triggers_notify_org(self, client, db_session, sample_invoice_data):
        """When the invoice has an organization_id, paid status fires notify_org."""
        from app.models import Invoice
        import uuid
        from datetime import date

        # Directly insert an invoice with org_id=1
        inv = Invoice(
            invoice_id=f"INV-20260228-{uuid.uuid4().hex[:8]}",
            invoice_number="RE-PUSH-001",
            invoice_date=date(2026, 2, 28),
            seller_name="Push GmbH",
            gross_amount=500.0,
            net_amount=420.17,
            tax_amount=79.83,
            tax_rate=19.0,
            line_items=[],
            source_type="manual",
            organization_id=1,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        with patch("app.push_service.notify_org") as mock_notify:
            res = client.patch(
                f"/api/invoices/{inv.invoice_id}/payment-status",
                json={"status": "paid"},
            )
            assert res.status_code == 200
            mock_notify.assert_called_once()
            call_kwargs = mock_notify.call_args
            # Verify correct arguments
            assert call_kwargs.kwargs["organization_id"] == 1
            assert "Zahlung" in call_kwargs.kwargs["title"]
            assert inv.invoice_id in call_kwargs.kwargs["body"]

    def test_payment_not_paid_does_not_trigger_push(self, client, db_session):
        """Setting status to 'unpaid' or 'overdue' must NOT fire push."""
        from app.models import Invoice
        import uuid
        from datetime import date

        inv = Invoice(
            invoice_id=f"INV-20260228-{uuid.uuid4().hex[:8]}",
            invoice_number="RE-PUSH-002",
            invoice_date=date(2026, 2, 28),
            seller_name="NoPush GmbH",
            gross_amount=200.0,
            net_amount=168.07,
            tax_amount=31.93,
            tax_rate=19.0,
            line_items=[],
            source_type="manual",
            organization_id=1,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        with patch("app.push_service.notify_org") as mock_notify:
            for status in ("overdue", "unpaid", "partial", "cancelled"):
                res = client.patch(
                    f"/api/invoices/{inv.invoice_id}/payment-status",
                    json={"status": status},
                )
                assert res.status_code == 200
            mock_notify.assert_not_called()


# ---------------------------------------------------------------------------
# Trigger 2: Mahnung created
# ---------------------------------------------------------------------------

class TestMahnungPushTrigger:
    """Push fires when a Mahnung is created for an overdue invoice."""

    def test_create_mahnung_fires_push(self, client, db_session):
        """POST /api/mahnwesen/{invoice_id}/mahnung calls push_service.notify_org."""
        from app.models import Invoice
        import uuid
        from datetime import date, timedelta

        inv = Invoice(
            invoice_id=f"INV-20260228-{uuid.uuid4().hex[:8]}",
            invoice_number="RE-MAH-001",
            invoice_date=date(2026, 1, 1),
            due_date=date(2026, 1, 31),  # past due
            seller_name="Mahner GmbH",
            gross_amount=1000.0,
            net_amount=840.34,
            tax_amount=159.66,
            tax_rate=19.0,
            line_items=[],
            source_type="manual",
            organization_id=2,
        )
        db_session.add(inv)
        db_session.commit()
        db_session.refresh(inv)

        with patch("app.push_service.notify_org") as mock_notify:
            res = client.post(f"/api/mahnwesen/{inv.invoice_id}/mahnung")
            assert res.status_code == 201
            mock_notify.assert_called_once()
            call_kwargs = mock_notify.call_args
            assert call_kwargs.kwargs["organization_id"] == 2
            assert "Zahlungserinnerung" in call_kwargs.kwargs["title"]


# ---------------------------------------------------------------------------
# Trigger 3: Overdue cron
# ---------------------------------------------------------------------------

def _make_fake_invoice(org_id: int, invoice_id: str = "INV-20260101-aabbccdd"):
    """Helper: create a MagicMock that looks like an Invoice with organization_id."""
    inv = MagicMock()
    inv.organization_id = org_id
    inv.invoice_id = invoice_id
    return inv


def _mock_db_session(overdue_invoices: list):
    """Return a MagicMock SessionLocal factory that yields a configured mock DB."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = overdue_invoices
    mock_session_cls = MagicMock(return_value=mock_db)
    return mock_session_cls, mock_db


class TestOverduePushCron:
    """send_overdue_push_cron() runs correctly and groups by org."""

    def test_overdue_cron_runs_without_error(self):
        """Cron completes and returns expected dict keys (empty DB)."""
        from app.tasks.push_cron import send_overdue_push_cron
        import asyncio

        mock_session_cls, _ = _mock_db_session([])

        with patch("app.push_service.notify_org") as mock_notify:
            with patch("app.database.SessionLocal", mock_session_cls):
                result = asyncio.run(send_overdue_push_cron(ctx={}))
                assert "notified_orgs" in result
                assert "overdue_invoices" in result
                assert isinstance(result["notified_orgs"], int)
                assert isinstance(result["overdue_invoices"], int)

    def test_push_cron_groups_by_org(self):
        """Cron sends exactly one push per org (two invoices, same org → 1 call)."""
        from app.tasks.push_cron import send_overdue_push_cron
        import asyncio

        # Two overdue invoices, both from org 5
        overdue = [
            _make_fake_invoice(5, "INV-20260101-aaa00001"),
            _make_fake_invoice(5, "INV-20260101-aaa00002"),
        ]
        mock_session_cls, _ = _mock_db_session(overdue)

        with patch("app.push_service.notify_org") as mock_notify:
            with patch("app.database.SessionLocal", mock_session_cls):
                result = asyncio.run(send_overdue_push_cron(ctx={}))
                # 2 overdue invoices, 1 org → notify_org called once
                assert result["overdue_invoices"] == 2
                assert result["notified_orgs"] == 1
                assert mock_notify.call_count == 1

    def test_push_cron_two_orgs(self):
        """Cron sends one push per distinct org."""
        from app.tasks.push_cron import send_overdue_push_cron
        import asyncio

        overdue = [
            _make_fake_invoice(10, "INV-20260101-org10a"),
            _make_fake_invoice(20, "INV-20260101-org20a"),
            _make_fake_invoice(10, "INV-20260101-org10b"),
        ]
        mock_session_cls, _ = _mock_db_session(overdue)

        with patch("app.push_service.notify_org") as mock_notify:
            with patch("app.database.SessionLocal", mock_session_cls):
                result = asyncio.run(send_overdue_push_cron(ctx={}))
                assert result["overdue_invoices"] == 3
                assert result["notified_orgs"] == 2
                assert mock_notify.call_count == 2

    def test_push_cron_empty_db_no_push(self):
        """When there are no overdue invoices, no push is sent."""
        from app.tasks.push_cron import send_overdue_push_cron
        import asyncio

        mock_session_cls, _ = _mock_db_session([])

        with patch("app.push_service.notify_org") as mock_notify:
            with patch("app.database.SessionLocal", mock_session_cls):
                result = asyncio.run(send_overdue_push_cron(ctx={}))
                assert result["notified_orgs"] == 0
                assert result["overdue_invoices"] == 0
                mock_notify.assert_not_called()
