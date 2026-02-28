"""Tests for async invoice categorization ARQ task (Task 7)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_session_factory(db_session):
    """Return a callable that yields db_session but swallows close() calls."""

    class _NoCloseSession:
        """Thin proxy around db_session that ignores close()."""

        def __init__(self, session):
            self._s = session

        def __getattr__(self, name):
            return getattr(self._s, name)

        def close(self):
            # Do NOT close the shared test session
            pass

    proxy = _NoCloseSession(db_session)
    return lambda: proxy


class TestCategorizeInvoiceTask:

    @pytest.mark.asyncio
    async def test_categorize_task_updates_invoice(self, db_session, test_invoice):
        """categorize_invoice_task should update skr03_account and ai_category on invoice."""
        from app.tasks.worker import categorize_invoice_task

        ctx = {}
        with patch("app.database.SessionLocal", side_effect=_make_session_factory(db_session)), \
             patch("app.ai_service.categorize_invoice", return_value={
                 "skr03_account": "4964", "category": "IT/Software"
             }), \
             patch("app.ws.notify_org", new_callable=AsyncMock):
            result = await categorize_invoice_task(
                ctx,
                invoice_id=test_invoice.invoice_id,
                org_id=test_invoice.organization_id or 1,
            )

        assert result["skr03_account"] == "4964"
        db_session.refresh(test_invoice)
        assert test_invoice.skr03_account == "4964"
        assert test_invoice.ai_category == "IT/Software"

    @pytest.mark.asyncio
    async def test_categorize_task_invoice_not_found(self, db_session):
        """categorize_invoice_task with unknown invoice_id should return error."""
        from app.tasks.worker import categorize_invoice_task

        ctx = {}
        with patch("app.database.SessionLocal", side_effect=_make_session_factory(db_session)):
            result = await categorize_invoice_task(ctx, invoice_id="NONEXISTENT-999", org_id=1)
        assert result.get("error") == "not found"

    @pytest.mark.asyncio
    async def test_categorize_task_sends_ws_notification(self, db_session, test_invoice):
        """After categorization, a WebSocket event should be sent."""
        from app.tasks.worker import categorize_invoice_task

        ctx = {}
        with patch("app.database.SessionLocal", side_effect=_make_session_factory(db_session)), \
             patch("app.ai_service.categorize_invoice", return_value={
                 "skr03_account": "4800", "category": "Personalkosten"
             }), \
             patch("app.ws.notify_org", new_callable=AsyncMock) as mock_notify:
            await categorize_invoice_task(
                ctx,
                invoice_id=test_invoice.invoice_id,
                org_id=test_invoice.organization_id or 1,
            )

        mock_notify.assert_called_once()
        assert mock_notify.call_args[0][1] == "invoice.categorized"
