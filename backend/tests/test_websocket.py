"""Tests for WebSocket ConnectionManager (Task 2)."""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestConnectionManager:

    @pytest.mark.asyncio
    async def test_connect_adds_websocket_to_org(self):
        """connect() should add the websocket to the org's connection list."""
        from app.ws import ConnectionManager
        mgr = ConnectionManager()
        mock_ws = AsyncMock()
        await mgr.connect(org_id=1, websocket=mock_ws)
        assert mgr.connection_count(1) == 1
        mock_ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_websocket(self):
        """disconnect() should remove the websocket and clean up empty org."""
        from app.ws import ConnectionManager
        mgr = ConnectionManager()
        mock_ws = AsyncMock()
        await mgr.connect(org_id=1, websocket=mock_ws)
        mgr.disconnect(org_id=1, websocket=mock_ws)
        assert mgr.connection_count(1) == 0
        assert 1 not in mgr._connections

    @pytest.mark.asyncio
    async def test_send_to_org_sends_json_message(self):
        """send_to_org() should send a JSON-encoded event+data message."""
        import json
        from app.ws import ConnectionManager
        mgr = ConnectionManager()
        mock_ws = AsyncMock()
        await mgr.connect(org_id=5, websocket=mock_ws)
        count = await mgr.send_to_org(5, "invoice.paid", {"invoice_id": "INV-001"})
        assert count == 1
        call_args = mock_ws.send_text.call_args[0][0]
        payload = json.loads(call_args)
        assert payload["event"] == "invoice.paid"
        assert payload["data"]["invoice_id"] == "INV-001"

    @pytest.mark.asyncio
    async def test_send_to_org_no_connections_returns_zero(self):
        """send_to_org() with no active connections returns 0."""
        from app.ws import ConnectionManager
        mgr = ConnectionManager()
        count = await mgr.send_to_org(99, "invoice.paid", {})
        assert count == 0

    @pytest.mark.asyncio
    async def test_dead_connections_removed_on_send(self):
        """Failed send should remove dead connection from pool."""
        from app.ws import ConnectionManager
        mgr = ConnectionManager()
        dead_ws = AsyncMock()
        dead_ws.send_text.side_effect = Exception("Connection closed")
        await mgr.connect(org_id=3, websocket=dead_ws)
        count = await mgr.send_to_org(3, "test", {})
        assert count == 0
        assert mgr.connection_count(3) == 0
