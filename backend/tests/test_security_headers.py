"""Tests for security headers middleware."""
from fastapi.testclient import TestClient
from app.main import app


def test_security_headers_present():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    # X-XSS-Protection intentionally removed — deprecated and can cause issues in modern browsers
    assert "X-XSS-Protection" not in resp.headers
    assert resp.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains; preload"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert resp.headers.get("Permissions-Policy") == "camera=(), microphone=(), geolocation=()"
    # Content-Security-Policy must be present with Stripe domains
    csp = resp.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "https://js.stripe.com" in csp


def test_headers_on_api_endpoints(client):
    resp = client.get("/api/invoices")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
