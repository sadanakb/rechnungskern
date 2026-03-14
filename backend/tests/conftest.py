"""
Shared test fixtures for RechnungsKern backend tests.

Uses an in-memory SQLite database so tests run fast and independently.
"""
import os
import sys
import types
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Override settings BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["REQUIRE_API_KEY"] = "false"


def _install_reportlab_test_stub() -> None:
    """Provide a tiny reportlab stub when optional PDF deps are unavailable."""
    if "reportlab" in sys.modules:
        return
    try:
        import reportlab  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    reportlab = types.ModuleType("reportlab")
    lib = types.ModuleType("reportlab.lib")
    pagesizes = types.ModuleType("reportlab.lib.pagesizes")
    pagesizes.A4 = (595, 842)

    styles = types.ModuleType("reportlab.lib.styles")

    def get_sample_stylesheet():
        return {"Title": object(), "Heading2": object(), "Heading3": object(), "Normal": object()}

    class ParagraphStyle:
        def __init__(self, *args, **kwargs):
            pass

    styles.getSampleStyleSheet = get_sample_stylesheet
    styles.ParagraphStyle = ParagraphStyle

    units = types.ModuleType("reportlab.lib.units")
    units.cm = 28.3465

    colors = types.ModuleType("reportlab.lib.colors")

    class Color:
        def __init__(self, *args, **kwargs):
            pass

    colors.Color = Color
    colors.whitesmoke = object()
    colors.grey = object()

    platypus = types.ModuleType("reportlab.platypus")

    class _Base:
        def __init__(self, *args, **kwargs):
            pass

    class SimpleDocTemplate(_Base):
        def __init__(self, buffer, *args, **kwargs):
            self._buffer = buffer

        def build(self, *args, **kwargs):
            # Keep a minimal PDF signature so tests checking the magic header pass.
            self._buffer.write(b"%PDF-1.4\n%stub\n")

    class Table(_Base):
        def setStyle(self, *args, **kwargs):
            pass

    class TableStyle(_Base):
        pass

    class Paragraph(_Base):
        pass

    class Spacer(_Base):
        pass

    platypus.SimpleDocTemplate = SimpleDocTemplate
    platypus.Paragraph = Paragraph
    platypus.Spacer = Spacer
    platypus.Table = Table
    platypus.TableStyle = TableStyle

    lib.pagesizes = pagesizes
    lib.styles = styles
    lib.units = units
    lib.colors = colors
    reportlab.lib = lib
    reportlab.platypus = platypus

    sys.modules["reportlab"] = reportlab
    sys.modules["reportlab.lib"] = lib
    sys.modules["reportlab.lib.pagesizes"] = pagesizes
    sys.modules["reportlab.lib.styles"] = styles
    sys.modules["reportlab.lib.units"] = units
    sys.modules["reportlab.lib.colors"] = colors
    sys.modules["reportlab.platypus"] = platypus


_install_reportlab_test_stub()


def _install_openai_test_stub() -> None:
    """Provide minimal openai module so tests can patch openai.OpenAI / AzureOpenAI."""
    if "openai" in sys.modules:
        return
    try:
        import openai  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    openai = types.ModuleType("openai")

    class OpenAI:
        def __init__(self, *args, **kwargs):
            pass

    class AzureOpenAI:
        def __init__(self, *args, **kwargs):
            pass

    class AsyncOpenAI:
        def __init__(self, *args, **kwargs):
            pass

    class AsyncAzureOpenAI:
        def __init__(self, *args, **kwargs):
            pass

    openai.OpenAI = OpenAI
    openai.AzureOpenAI = AzureOpenAI
    openai.AsyncOpenAI = AsyncOpenAI
    openai.AsyncAzureOpenAI = AsyncAzureOpenAI
    sys.modules["openai"] = openai


def _install_arq_test_stub() -> None:
    """Provide minimal arq module so worker imports succeed in tests."""
    if "arq" in sys.modules:
        return
    try:
        import arq  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    arq = types.ModuleType("arq")
    connections = types.ModuleType("arq.connections")

    def cron(func, *args, **kwargs):
        return {"func": func, "args": args, "kwargs": kwargs}

    async def create_pool(*args, **kwargs):
        return None

    class RedisSettings:
        @classmethod
        def from_dsn(cls, *_args, **_kwargs):
            return cls()

    arq.cron = cron
    arq.create_pool = create_pool
    connections.RedisSettings = RedisSettings

    sys.modules["arq"] = arq
    sys.modules["arq.connections"] = connections


_install_openai_test_stub()
_install_arq_test_stub()

from app.models import Base, Invoice
from app.database import get_db
from app.main import app


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the slowapi in-memory rate-limit counters before every test.

    Without this, the shared limiter accumulates hits across all tests in a
    session.  After 5 POST /api/auth/register calls the limiter returns 429
    for every subsequent test that calls that endpoint.

    MemoryStorage.reset() clears the entire counter dict, which is exactly
    what we need between isolated unit tests.  The test_rate_limiting.py tests
    only check that a *single* request is NOT blocked (they never verify that
    the 6th request IS blocked), so resetting here does not break them.
    """
    from app.rate_limiter import limiter
    limiter._storage.reset()
    yield
    limiter._storage.reset()


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a transactional database session that rolls back after test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden DB dependency."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_invoice_data() -> dict:
    """Minimal valid invoice data for creating invoices."""
    return {
        "invoice_number": "RE-2026-001",
        "invoice_date": "2026-02-23",
        "due_date": "2026-03-23",
        "seller_name": "Musterfirma GmbH",
        "seller_vat_id": "DE123456789",
        "seller_address": "Musterstraße 1, 60311 Frankfurt am Main",
        "buyer_name": "Käufer AG",
        "buyer_vat_id": "DE987654321",
        "buyer_address": "Hauptstraße 5, 10115 Berlin",
        "line_items": [
            {
                "description": "Beratungsleistung",
                "quantity": 10.0,
                "unit_price": 150.0,
                "net_amount": 1500.0,
                "tax_rate": 19.0,
            }
        ],
        "tax_rate": 19.0,
        "iban": "DE89370400440532013000",
        "bic": "COBADEFFXXX",
        "payment_account_name": "Musterfirma GmbH",
        "currency": "EUR",
    }


@pytest.fixture()
def sample_invoice_dict(sample_invoice_data) -> dict:
    """Invoice data dict as expected by XRechnungGenerator.generate_xml()."""
    net = sum(i["net_amount"] for i in sample_invoice_data["line_items"])
    tax = round(net * sample_invoice_data["tax_rate"] / 100, 2)
    gross = round(net + tax, 2)
    return {
        **sample_invoice_data,
        "net_amount": net,
        "tax_amount": tax,
        "gross_amount": gross,
    }


@pytest.fixture()
def test_invoice(db_session) -> Invoice:
    """A minimal Invoice row persisted in the test DB for task tests."""
    import uuid

    inv = Invoice(
        invoice_id=f"INV-20260228-{uuid.uuid4().hex[:8]}",
        invoice_number="RE-TEST-001",
        invoice_date=date(2026, 2, 28),
        seller_name="Test GmbH",
        gross_amount=1190.0,
        net_amount=1000.0,
        tax_amount=190.0,
        tax_rate=19.0,
        line_items=[{"description": "Testleistung", "quantity": 1, "unit_price": 1000.0, "net_amount": 1000.0}],
        source_type="manual",
        validation_status="pending",
        organization_id=1,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)
    return inv


@pytest.fixture()
def saved_invoice(db_session, sample_invoice_dict) -> Invoice:
    """An Invoice row already persisted in the test DB."""
    import uuid

    inv = Invoice(
        invoice_id=f"INV-20260223-{uuid.uuid4().hex[:8]}",
        invoice_number=sample_invoice_dict["invoice_number"],
        invoice_date=date(2026, 2, 23),
        due_date=date(2026, 3, 23),
        seller_name=sample_invoice_dict["seller_name"],
        seller_vat_id=sample_invoice_dict["seller_vat_id"],
        seller_address=sample_invoice_dict["seller_address"],
        buyer_name=sample_invoice_dict["buyer_name"],
        buyer_vat_id=sample_invoice_dict["buyer_vat_id"],
        buyer_address=sample_invoice_dict["buyer_address"],
        net_amount=sample_invoice_dict["net_amount"],
        tax_amount=sample_invoice_dict["tax_amount"],
        gross_amount=sample_invoice_dict["gross_amount"],
        tax_rate=19.0,
        currency="EUR",
        line_items=sample_invoice_dict["line_items"],
        iban=sample_invoice_dict["iban"],
        bic=sample_invoice_dict["bic"],
        payment_account_name=sample_invoice_dict["payment_account_name"],
        source_type="manual",
        validation_status="pending",
        organization_id=1,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)
    return inv
