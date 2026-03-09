# Phase 10 — DATEV-Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade RechnungsKern's existing DATEV export from a simple CSV dump to a full EXTF v700 ZIP export with Beraternummer/Mandantennummer, SKR03-filtered Buchungsstapel + Stammdaten, and Steuerberater email delivery.

**Architecture:** The existing `DATEVExporter` class in `backend/app/export/datev_export.py` is enhanced with Beraternummer/Mandantennummer params and a new `format_stammdaten()` method. Three new Organization columns (`datev_berater_nr`, `datev_mandant_nr`, `steuerberater_email`) are added via Alembic migration. A new `backend/app/routers/datev.py` serves two JWT-protected endpoints: `GET /api/datev/export` (ZIP download) and `POST /api/datev/send-email`. The frontend settings page gets a DATEV config section, and the existing `DATEVExportSection` in berichte is upgraded to use the new ZIP endpoint.

**Tech Stack:** FastAPI, SQLAlchemy (SQLite), Alembic, Python `zipfile` + `io.BytesIO`, Next.js 14, TypeScript, CSS variables (`rgb(var(--primary))`)

**Critical context:**
- The existing endpoint `GET /api/invoices/export-datev` uses year/quarter but NO `skr03_account` filter — the new endpoint at `/api/datev/export` replaces the frontend's use of it
- JWT auth pattern: register via `/api/auth/register` → get `access_token` → pass as `Authorization: Bearer <token>` header; `get_current_user` from `app.auth_jwt`; `_resolve_org_id()` from `app.routers.ai` (copy the pattern exactly)
- Existing `DATEVExporter._build_meta_header()` has Berater at index 9 and Mandant at index 10 — these are currently empty strings
- Phase 9 Alembic revision to chain from: `c8d4f0e5a3b2`
- Email: use `enqueue_email(arq_pool, task_type, **kwargs)` from `app.email_service`; add new task type `"datev_export"`
- Feature branch: `git checkout -b feature/phase10-datev-export`

---

## Setup

**Step 1: Create feature branch**

```bash
cd /Users/sadanakb/rechnungskern
git checkout -b feature/phase10-datev-export
```

Expected: `Switched to a new branch 'feature/phase10-datev-export'`

---

## Task 1: Enhance DATEVExporter

**Files:**
- Modify: `backend/app/export/datev_export.py`
- Create: `backend/tests/test_datev_formatter.py`

### Step 1: Write the failing tests

Create `backend/tests/test_datev_formatter.py`:

```python
"""Tests for enhanced DATEVExporter (Phase 10)."""
import io
import zipfile
import pytest
from app.export.datev_export import DATEVExporter


class TestDATEVFormatter:

    def _sample_invoice(self, skr03_account="4930", seller_name="Papier GmbH"):
        return {
            "invoice_number": "RE-2024-001",
            "invoice_date": "2024-01-15",
            "seller_name": seller_name,
            "buyer_name": "Musterfirma GmbH",
            "net_amount": 1000.0,
            "tax_rate": 19.0,
            "tax_amount": 190.0,
            "gross_amount": 1190.0,
            "currency": "EUR",
            "skr03_account": skr03_account,
        }

    def test_meta_header_contains_berater_nr(self):
        """_build_meta_header() should embed berater_nr and mandant_nr."""
        exporter = DATEVExporter()
        header = exporter._build_meta_header(berater_nr="12345", mandant_nr="67890")
        assert header[9] == "12345"
        assert header[10] == "67890"

    def test_meta_header_defaults_to_empty(self):
        """Without berater_nr/mandant_nr, header fields should be empty string."""
        exporter = DATEVExporter()
        header = exporter._build_meta_header()
        assert header[9] == ""
        assert header[10] == ""

    def test_export_buchungsstapel_uses_skr03_account(self):
        """When invoice has skr03_account, use it as Konto field instead of default."""
        exporter = DATEVExporter()
        inv = self._sample_invoice(skr03_account="4930")
        csv_str = exporter.export_buchungsstapel([inv], berater_nr="12345", mandant_nr="00001")
        # SKR03 account 4930 should appear in the CSV rows (not the default Forderungen konto)
        lines = csv_str.strip().split("\n")
        booking_line = lines[2]  # Line 0: header, Line 1: columns, Line 2: first booking
        assert "4930" in booking_line

    def test_decimal_comma_formatting(self):
        """Amounts must use comma as decimal separator (German DATEV format)."""
        exporter = DATEVExporter()
        result = exporter._format_amount(1190.0)
        assert result == "1190,00"

    def test_format_stammdaten_returns_csv(self):
        """format_stammdaten() should return CSV with Konto, Kontobeschriftung, Sprachkennung."""
        exporter = DATEVExporter()
        contacts = [
            {"account_nr": "70001", "name": "Papier GmbH"},
            {"account_nr": "70002", "name": "Tech AG"},
        ]
        csv_str = exporter.format_stammdaten(contacts)
        assert "70001" in csv_str
        assert "Papier GmbH" in csv_str
        assert "Sprachkennung" in csv_str or "sprachkennung" in csv_str.lower()

    def test_export_zip_contains_two_files(self):
        """export_zip() should return bytes of a ZIP with exactly 2 CSV files."""
        exporter = DATEVExporter()
        invoices = [self._sample_invoice()]
        contacts = [{"account_nr": "70001", "name": "Papier GmbH"}]
        zip_bytes = exporter.export_zip(
            invoices, contacts,
            berater_nr="12345", mandant_nr="00001",
            from_month="2024-01", to_month="2024-12",
        )
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
        assert len(names) == 2
        assert any("Buchungsstapel" in n for n in names)
        assert any("Stammdaten" in n for n in names)
```

### Step 2: Run tests to verify they fail

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest tests/test_datev_formatter.py -v
```

Expected: Multiple FAILs — `_build_meta_header` doesn't accept berater_nr yet, `format_stammdaten` doesn't exist, `export_zip` doesn't exist.

### Step 3: Implement the changes in datev_export.py

Open `backend/app/export/datev_export.py`. Make the following changes:

**3a. Update `_build_meta_header` signature** (currently around line 105):

Change:
```python
def _build_meta_header(self) -> List[str]:
    """Build DATEV meta header row."""
    now = datetime.now()
    return [
        "EXTF",  # DATEV format identifier
        "700",   # Version
        "21",    # Kategorie: Buchungsstapel
        "Buchungsstapel",
        "13",    # Formatversion
        str(now.year * 10000 + now.month * 100 + now.day),
        "",      # Herkunft
        "",      # Exportiert von
        "",      # Importiert von
        "",      # Berater
        "",      # Mandant
```

To:
```python
def _build_meta_header(
    self,
    berater_nr: str = "",
    mandant_nr: str = "",
) -> List[str]:
    """Build DATEV meta header row."""
    now = datetime.now()
    return [
        "EXTF",  # DATEV format identifier
        "700",   # Version
        "21",    # Kategorie: Buchungsstapel
        "Buchungsstapel",
        "13",    # Formatversion
        str(now.year * 10000 + now.month * 100 + now.day),
        "",      # Herkunft
        "",      # Exportiert von
        "",      # Importiert von
        berater_nr,   # Berater
        mandant_nr,   # Mandant
```

**3b. Update `export_buchungsstapel` to pass berater_nr/mandant_nr:**

Change:
```python
def export_buchungsstapel(self, invoices: List[Dict]) -> str:
    ...
    # DATEV file header (meta row)
    writer.writerow(self._build_meta_header())
```

To:
```python
def export_buchungsstapel(
    self,
    invoices: List[Dict],
    berater_nr: str = "",
    mandant_nr: str = "",
) -> str:
    ...
    # DATEV file header (meta row)
    writer.writerow(self._build_meta_header(berater_nr=berater_nr, mandant_nr=mandant_nr))
```

**3c. Update `_invoice_to_rows` to use `skr03_account` when available:**

In `_invoice_to_rows`, find the section that sets `row[6]` (Konto). Change:
```python
row[6] = self.accounts["accounts_receivable"]  # Konto (Forderungen)
row[7] = revenue_account                       # Gegenkonto (Erloese)
```

To:
```python
# Use AI-assigned SKR03 account if available, else default
konto = invoice.get("skr03_account") or self.accounts["accounts_receivable"]
row[6] = konto                                 # Konto
row[7] = revenue_account                       # Gegenkonto (Erloese)
```

**3d. Add `format_stammdaten` method** (add after `_format_amount`):

```python
def format_stammdaten(self, contacts: List[Dict]) -> str:
    """
    Generate DATEV Stammdaten CSV (Kreditoren/Debitoren).

    Args:
        contacts: List of dicts with 'account_nr' and 'name' keys.

    Returns:
        CSV string with columns: Konto;Kontobeschriftung;Sprachkennung
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Konto", "Kontobeschriftung", "Sprachkennung"])
    for contact in contacts:
        writer.writerow([
            contact.get("account_nr", ""),
            contact.get("name", "")[:40],  # DATEV max 40 chars
            "0",  # 0 = Deutsch
        ])
    return output.getvalue()
```

**3e. Add `export_zip` method** (add after `format_stammdaten`):

```python
def export_zip(
    self,
    invoices: List[Dict],
    contacts: List[Dict],
    berater_nr: str = "",
    mandant_nr: str = "",
    from_month: str = "",
    to_month: str = "",
) -> bytes:
    """
    Generate an in-memory ZIP containing Buchungsstapel.csv and Stammdaten.csv.

    Returns:
        bytes of the ZIP archive
    """
    buchungsstapel_csv = self.export_buchungsstapel(
        invoices, berater_nr=berater_nr, mandant_nr=mandant_nr
    )
    stammdaten_csv = self.format_stammdaten(contacts)

    period = f"{from_month}_{to_month}" if from_month and to_month else "export"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"Buchungsstapel_{period}.csv", buchungsstapel_csv.encode("utf-8"))
        zf.writestr(f"Stammdaten_{period}.csv", stammdaten_csv.encode("utf-8"))
    return buf.getvalue()
```

Add `import zipfile` to the top-level imports.

### Step 4: Run tests to verify they pass

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest tests/test_datev_formatter.py -v
```

Expected: 6 PASSED

### Step 5: Commit

```bash
cd /Users/sadanakb/rechnungskern
git add backend/app/export/datev_export.py backend/tests/test_datev_formatter.py
git commit -m "feat: enhance DATEVExporter with berater_nr, stammdaten, ZIP export"
```

---

## Task 2: Organization Model + Alembic Migration

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/alembic/versions/phase10_datev_settings.py`

### Step 1: Write the failing test

Add to `backend/tests/test_datev_formatter.py` (in the `TestDATEVFormatter` class):

```python
def test_organization_has_datev_fields(self):
    """Organization model must have datev_berater_nr, datev_mandant_nr, steuerberater_email."""
    from app.models import Organization
    org = Organization()
    assert hasattr(org, "datev_berater_nr")
    assert hasattr(org, "datev_mandant_nr")
    assert hasattr(org, "steuerberater_email")
```

### Step 2: Run test to verify it fails

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest tests/test_datev_formatter.py::TestDATEVFormatter::test_organization_has_datev_fields -v
```

Expected: FAIL — `Organization` has no attribute `datev_berater_nr`

### Step 3: Add columns to Organization model

Open `backend/app/models.py`. Find the `Organization` class (around line 21). After the `plan_status` line, add:

```python
    # DATEV configuration (Phase 10)
    datev_berater_nr = Column(String(5), nullable=True)
    datev_mandant_nr = Column(String(5), nullable=True)
    steuerberater_email = Column(String(200), nullable=True)
```

### Step 4: Create Alembic migration

Create `backend/alembic/versions/phase10_datev_settings.py`:

```python
"""add Phase 10 — DATEV settings columns to organizations

Revision ID: d9e5g1h2i3j4
Revises: c8d4f0e5a3b2
Create Date: 2026-02-28 12:00:00.000000
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd9e5g1h2i3j4'
down_revision: Union[str, None] = 'c8d4f0e5a3b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('organizations', sa.Column('datev_berater_nr', sa.String(5), nullable=True))
    op.add_column('organizations', sa.Column('datev_mandant_nr', sa.String(5), nullable=True))
    op.add_column('organizations', sa.Column('steuerberater_email', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('organizations', 'steuerberater_email')
    op.drop_column('organizations', 'datev_mandant_nr')
    op.drop_column('organizations', 'datev_berater_nr')
```

### Step 5: Run test to verify it passes

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest tests/test_datev_formatter.py::TestDATEVFormatter::test_organization_has_datev_fields -v
```

Expected: PASS

### Step 6: Commit

```bash
cd /Users/sadanakb/rechnungskern
git add backend/app/models.py backend/alembic/versions/phase10_datev_settings.py backend/tests/test_datev_formatter.py
git commit -m "feat: add DATEV settings columns to Organization model + migration"
```

---

## Task 3: DATEV Settings API (in onboarding.py)

**Files:**
- Modify: `backend/app/routers/onboarding.py`
- Create: `backend/tests/test_datev_settings_api.py`

### Step 1: Write the failing tests

Create `backend/tests/test_datev_settings_api.py`:

```python
"""Tests for DATEV settings API (Phase 10)."""
import uuid
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.models import Base
from app.database import get_db
from app.config import settings


@pytest.fixture(scope="function")
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
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    with patch.object(settings, "require_api_key", True):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()


def _register_and_get_token(client):
    email = f"datev-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "full_name": "DATEV Test",
        "organization_name": f"TestOrg {uuid.uuid4().hex[:6]}",
    })
    assert resp.status_code == 201
    data = resp.json()
    return {"token": data["access_token"], "org_id": data["organization"]["id"]}


class TestDATEVSettingsApi:

    def test_get_datev_settings_initially_null(self, client):
        """GET /api/onboarding/datev-settings returns nulls for fresh org."""
        user = _register_and_get_token(client)
        resp = client.get(
            "/api/onboarding/datev-settings",
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["datev_berater_nr"] is None
        assert data["datev_mandant_nr"] is None
        assert data["steuerberater_email"] is None

    def test_post_datev_settings_saves_fields(self, client):
        """POST /api/onboarding/datev-settings should persist the three fields."""
        user = _register_and_get_token(client)
        resp = client.post(
            "/api/onboarding/datev-settings",
            json={
                "datev_berater_nr": "12345",
                "datev_mandant_nr": "00001",
                "steuerberater_email": "stb@kanzlei.de",
            },
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["datev_berater_nr"] == "12345"
        assert data["datev_mandant_nr"] == "00001"
        assert data["steuerberater_email"] == "stb@kanzlei.de"

    def test_post_datev_settings_partial_update(self, client):
        """POST with only berater_nr should not overwrite existing mandant_nr."""
        user = _register_and_get_token(client)
        # First: set both
        client.post(
            "/api/onboarding/datev-settings",
            json={"datev_berater_nr": "12345", "datev_mandant_nr": "00001"},
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        # Then: update only berater_nr
        resp = client.post(
            "/api/onboarding/datev-settings",
            json={"datev_berater_nr": "99999"},
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["datev_berater_nr"] == "99999"
        assert data["datev_mandant_nr"] == "00001"  # unchanged
```

### Step 2: Run tests to verify they fail

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest tests/test_datev_settings_api.py -v
```

Expected: FAIL — endpoints don't exist yet

### Step 3: Add endpoints to onboarding.py

Open `backend/app/routers/onboarding.py`. Add the following **before** the last function:

```python
# ---------------------------------------------------------------------------
# DATEV Settings
# ---------------------------------------------------------------------------

class DatevSettingsPayload(BaseModel):
    datev_berater_nr: Optional[str] = None
    datev_mandant_nr: Optional[str] = None
    steuerberater_email: Optional[str] = None


class DatevSettingsResponse(BaseModel):
    datev_berater_nr: Optional[str]
    datev_mandant_nr: Optional[str]
    steuerberater_email: Optional[str]


@router.get("/datev-settings", response_model=DatevSettingsResponse)
def get_datev_settings(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return DATEV configuration for current organization."""
    from app.models import OrganizationMember, Organization
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == int(current_user["user_id"])
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    return DatevSettingsResponse(
        datev_berater_nr=org.datev_berater_nr,
        datev_mandant_nr=org.datev_mandant_nr,
        steuerberater_email=org.steuerberater_email,
    )


@router.post("/datev-settings", response_model=DatevSettingsResponse)
def update_datev_settings(
    payload: DatevSettingsPayload,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update DATEV configuration (Beraternummer, Mandantennummer, Steuerberater-E-Mail)."""
    from app.models import OrganizationMember, Organization
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == int(current_user["user_id"])
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")

    if payload.datev_berater_nr is not None:
        org.datev_berater_nr = payload.datev_berater_nr
    if payload.datev_mandant_nr is not None:
        org.datev_mandant_nr = payload.datev_mandant_nr
    if payload.steuerberater_email is not None:
        org.steuerberater_email = payload.steuerberater_email

    db.commit()
    db.refresh(org)
    return DatevSettingsResponse(
        datev_berater_nr=org.datev_berater_nr,
        datev_mandant_nr=org.datev_mandant_nr,
        steuerberater_email=org.steuerberater_email,
    )
```

Also add `Optional` to the imports if not already there:
```python
from typing import Optional
```

And ensure `get_current_user` is imported (check top of file; add if missing):
```python
from app.auth_jwt import get_current_user
```

### Step 4: Run tests to verify they pass

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest tests/test_datev_settings_api.py -v
```

Expected: 3 PASSED

### Step 5: Commit

```bash
cd /Users/sadanakb/rechnungskern
git add backend/app/routers/onboarding.py backend/tests/test_datev_settings_api.py
git commit -m "feat: add GET/POST /api/onboarding/datev-settings endpoints"
```

---

## Task 4: DATEV Export + Send-Email Router

**Files:**
- Create: `backend/app/routers/datev.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/email_service.py`
- Create: `backend/tests/test_datev_export_endpoint.py`

### Step 1: Write failing tests

Create `backend/tests/test_datev_export_endpoint.py`:

```python
"""Tests for DATEV export endpoint (Phase 10)."""
import io
import uuid
import zipfile
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.models import Base, Invoice
from app.database import get_db
from app.config import settings


@pytest.fixture(scope="function")
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
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    with patch.object(settings, "require_api_key", True):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()


def _register_and_get_token(client):
    email = f"datev-export-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "full_name": "Export Test",
        "organization_name": f"ExportOrg {uuid.uuid4().hex[:6]}",
    })
    assert resp.status_code == 201
    data = resp.json()
    return {"token": data["access_token"], "org_id": data["organization"]["id"]}


def _make_invoice(db_session, org_id, skr03_account=None, invoice_date=None):
    """Insert a test invoice into the DB."""
    inv = Invoice(
        invoice_id=f"INV-{uuid.uuid4().hex[:12]}",
        invoice_number=f"RE-{uuid.uuid4().hex[:6]}",
        invoice_date=invoice_date or date(2024, 3, 15),
        due_date=date(2024, 4, 15),
        seller_name="Lieferant GmbH",
        seller_vat_id="DE100000001",
        seller_address="Lieferantenstr. 1, 60311 Frankfurt",
        buyer_name="Käufer AG",
        buyer_vat_id="DE200000002",
        buyer_address="Käuferstr. 2, 10115 Berlin",
        net_amount=Decimal("1000.00"),
        tax_amount=Decimal("190.00"),
        gross_amount=Decimal("1190.00"),
        tax_rate=Decimal("19.00"),
        currency="EUR",
        line_items=[{"description": "Büromaterial", "quantity": 1, "unit_price": 1190.0}],
        payment_status="unpaid",
        source_type="manual",
        validation_status="pending",
        organization_id=org_id,
        skr03_account=skr03_account,
    )
    db_session.add(inv)
    db_session.commit()
    return inv


class TestDATEVExportEndpoint:

    def test_export_returns_zip(self, client, db_session):
        """GET /api/datev/export should return application/zip."""
        user = _register_and_get_token(client)
        _make_invoice(db_session, user["org_id"], skr03_account="4930")

        resp = client.get(
            "/api/datev/export?from_month=2024-01&to_month=2024-12",
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 200
        assert "zip" in resp.headers["content-type"]
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            assert len(zf.namelist()) == 2

    def test_export_excludes_uncategorized(self, client, db_session):
        """Invoices without skr03_account must not appear in the export."""
        user = _register_and_get_token(client)
        _make_invoice(db_session, user["org_id"], skr03_account="4930")      # included
        _make_invoice(db_session, user["org_id"], skr03_account=None)         # excluded

        resp = client.get(
            "/api/datev/export?from_month=2024-01&to_month=2024-12",
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            buchungsstapel = zf.read([n for n in zf.namelist() if "Buchungsstapel" in n][0]).decode()
        # Only 1 booking line (besides 2 header rows)
        lines = [l for l in buchungsstapel.strip().split("\n") if l]
        assert len(lines) == 3  # header + columns + 1 booking

    def test_export_empty_period_returns_400(self, client, db_session):
        """If no categorized invoices in period, return 400."""
        user = _register_and_get_token(client)
        # No invoices at all

        resp = client.get(
            "/api/datev/export?from_month=2024-01&to_month=2024-12",
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 400

    def test_export_uses_berater_nr_from_org(self, client, db_session):
        """EXTF header in ZIP should contain org's datev_berater_nr."""
        user = _register_and_get_token(client)
        # Set DATEV settings
        client.post(
            "/api/onboarding/datev-settings",
            json={"datev_berater_nr": "12345", "datev_mandant_nr": "00001"},
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        _make_invoice(db_session, user["org_id"], skr03_account="4930")

        resp = client.get(
            "/api/datev/export?from_month=2024-01&to_month=2024-12",
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            buchungsstapel = zf.read([n for n in zf.namelist() if "Buchungsstapel" in n][0]).decode()
        assert "12345" in buchungsstapel  # berater_nr in EXTF header
```

### Step 2: Run tests to verify they fail

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest tests/test_datev_export_endpoint.py -v
```

Expected: FAIL — `/api/datev/export` doesn't exist yet

### Step 3: Add send_datev_export_email to email_service.py

Open `backend/app/email_service.py`. Find the `enqueue_email` function (around line 365).

First, add a new handler function **before** `enqueue_email`:

```python
def send_datev_export_email(
    to_email: str,
    from_month: str,
    to_month: str,
    invoice_count: int,
) -> bool:
    """Send a notification email to the tax advisor about a new DATEV export."""
    subject = f"DATEV-Export {from_month} bis {to_month} — RechnungsKern"
    body = (
        f"Guten Tag,\n\n"
        f"ein neuer DATEV-Export wurde erstellt.\n\n"
        f"Zeitraum: {from_month} bis {to_month}\n"
        f"Anzahl Buchungssätze: {invoice_count}\n\n"
        f"Bitte loggen Sie sich in RechnungsKern ein, um den Export herunterzuladen:\n"
        f"https://app.rechnungskern.de/berichte\n\n"
        f"Mit freundlichen Grüßen,\n"
        f"RechnungsKern"
    )
    return _send_smtp(to_email=to_email, subject=subject, body=body)
```

Note: `_send_smtp` is the internal helper already used by other email functions. If the function name is different (check the file — it might be `_send_email` or similar), use the correct one.

Then register it in `enqueue_email`'s handlers dict:
```python
    handlers = {
        "password_reset": send_password_reset_email,
        "email_verification": send_email_verification,
        "team_invite": send_team_invite,
        "mahnung": send_mahnung_email,
        "contact": send_contact_email,
        "invoice_portal": send_invoice_portal_email,
        "datev_export": send_datev_export_email,  # Phase 10
    }
```

### Step 4: Create backend/app/routers/datev.py

```python
"""DATEV Export Router — Phase 10.

Endpoints:
    GET  /api/datev/export              — Download EXTF ZIP (only categorized invoices)
    POST /api/datev/send-email          — Notify Steuerberater by email
"""
import logging
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth_jwt import get_current_user
from app.database import get_db
from app.models import Invoice, Organization, OrganizationMember

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_org(current_user: dict, db: Session) -> Organization:
    """Return the Organization for the current user, or raise 404."""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == int(current_user["user_id"])
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    return org


def _parse_month(month_str: str, is_start: bool) -> date:
    """Parse 'YYYY-MM' to a date (first or last day of the month)."""
    import calendar
    try:
        year, month = map(int, month_str.split("-"))
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Ungültiges Monatsformat: {month_str}. Erwartet: YYYY-MM")
    if is_start:
        return date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


@router.get("/export")
async def export_datev(
    from_month: str = Query(..., description="Von-Monat im Format YYYY-MM"),
    to_month: str = Query(..., description="Bis-Monat im Format YYYY-MM"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export categorized invoices as DATEV EXTF Buchungsstapel ZIP.

    Only invoices with skr03_account set (Phase 9 AI categorization) are included.
    Returns ZIP with Buchungsstapel_<period>.csv + Stammdaten_<period>.csv.
    """
    from app.export.datev_export import DATEVExporter

    org = _resolve_org(current_user, db)
    date_from = _parse_month(from_month, is_start=True)
    date_to = _parse_month(to_month, is_start=False)

    # Only categorized invoices
    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.organization_id == org.id,
            Invoice.skr03_account.isnot(None),
            Invoice.invoice_date >= date_from,
            Invoice.invoice_date <= date_to,
        )
        .order_by(Invoice.invoice_date)
        .all()
    )

    if not invoices:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Keine kategorisierten Rechnungen im Zeitraum {from_month}–{to_month}. "
                "Bitte zuerst KI-Kategorisierung ausführen."
            ),
        )

    # Build invoice dicts
    invoice_dicts = [
        {
            "invoice_number": inv.invoice_number or "",
            "invoice_date": str(inv.invoice_date),
            "seller_name": inv.seller_name or "",
            "buyer_name": inv.buyer_name or "",
            "net_amount": float(inv.net_amount or 0),
            "tax_rate": float(inv.tax_rate or 19),
            "tax_amount": float(inv.tax_amount or 0),
            "gross_amount": float(inv.gross_amount or 0),
            "currency": "EUR",
            "skr03_account": inv.skr03_account or "",
        }
        for inv in invoices
    ]

    # Build contacts (unique sellers → Kreditoren, 70001+)
    seen = {}
    contacts = []
    for i, inv in enumerate(invoices):
        name = inv.seller_name or "Unbekannt"
        if name not in seen:
            seen[name] = True
            contacts.append({"account_nr": str(70001 + len(contacts)), "name": name})

    exporter = DATEVExporter(kontenrahmen="SKR03")
    zip_bytes = exporter.export_zip(
        invoice_dicts,
        contacts,
        berater_nr=org.datev_berater_nr or "",
        mandant_nr=org.datev_mandant_nr or "",
        from_month=from_month,
        to_month=to_month,
    )

    filename = f"DATEV_{from_month}_{to_month}.zip"
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class SendEmailRequest(BaseModel):
    from_month: str
    to_month: str


@router.post("/send-email")
async def send_datev_email(
    body: SendEmailRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a notification to the organization's Steuerberater about a new DATEV export.
    Requires steuerberater_email to be configured in DATEV settings.
    """
    from app.email_service import enqueue_email

    org = _resolve_org(current_user, db)

    if not org.steuerberater_email:
        raise HTTPException(
            status_code=400,
            detail="Keine Steuerberater-E-Mail konfiguriert. Bitte in Einstellungen > DATEV hinterlegen.",
        )

    # Count categorized invoices in period
    date_from = _parse_month(body.from_month, is_start=True)
    date_to = _parse_month(body.to_month, is_start=False)
    count = (
        db.query(Invoice)
        .filter(
            Invoice.organization_id == org.id,
            Invoice.skr03_account.isnot(None),
            Invoice.invoice_date >= date_from,
            Invoice.invoice_date <= date_to,
        )
        .count()
    )

    if count == 0:
        raise HTTPException(status_code=400, detail="Keine kategorisierten Rechnungen im Zeitraum")

    arq_pool = getattr(request.app.state, "arq_pool", None)
    await enqueue_email(
        arq_pool,
        "datev_export",
        to_email=org.steuerberater_email,
        from_month=body.from_month,
        to_month=body.to_month,
        invoice_count=count,
    )

    return {"message": "E-Mail an Steuerberater wird versendet", "to": org.steuerberater_email}
```

### Step 5: Register router in main.py

Open `backend/app/main.py`. Find the block of `app.include_router(...)` calls. After the ai router line, add:

```python
from app.routers import datev as datev_router
app.include_router(datev_router.router, prefix="/api/datev", tags=["datev"])
```

### Step 6: Run tests to verify they pass

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest tests/test_datev_export_endpoint.py -v
```

Expected: 4 PASSED

### Step 7: Run full backend test suite to ensure no regressions

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest --tb=short -q 2>&1 | tail -5
```

Expected: All previously passing tests still pass (436+)

### Step 8: Commit

```bash
cd /Users/sadanakb/rechnungskern
git add backend/app/routers/datev.py backend/app/email_service.py backend/app/main.py backend/tests/test_datev_export_endpoint.py
git commit -m "feat: add DATEV export + send-email endpoints with EXTF ZIP format"
```

---

## Task 5: Frontend Settings — DATEV-Konfiguration Section

**Files:**
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/(dashboard)/settings/page.tsx`

### Step 1: Add API functions to api.ts

Open `frontend/lib/api.ts`. Find the DATEV Export section (around line 512). After the existing functions, add:

```typescript
// ---------------------------------------------------------------------------
// DATEV Settings (Phase 10)
// ---------------------------------------------------------------------------

export interface DatevSettings {
  datev_berater_nr: string | null
  datev_mandant_nr: string | null
  steuerberater_email: string | null
}

export async function getDatevSettings(): Promise<DatevSettings> {
  const res = await api.get('/api/onboarding/datev-settings')
  return res.data
}

export async function saveDatevSettings(settings: Partial<DatevSettings>): Promise<DatevSettings> {
  const res = await api.post('/api/onboarding/datev-settings', settings)
  return res.data
}

export async function sendDatevEmail(fromMonth: string, toMonth: string): Promise<{ message: string }> {
  const res = await api.post('/api/datev/send-email', { from_month: fromMonth, to_month: toMonth })
  return res.data
}
```

### Step 2: Add DATEV-Konfiguration section to settings page

Open `frontend/app/(dashboard)/settings/page.tsx`.

**2a.** Find the imports section at the top. Add import for the new API functions:

```typescript
import { getDatevSettings, saveDatevSettings, type DatevSettings } from '@/lib/api'
```

**2b.** In the main `SettingsPage` component (or create a `DatevTab` sub-component following the existing tab pattern), add a new DATEV tab.

Find where tabs are defined (look for `tabs` array or `TabsList`). Add a new tab entry `"Datev"` or `"DATEV"`.

Then create the tab content component:

```typescript
function DatevKonfigurationTab() {
  const [settings, setSettings] = useState<DatevSettings>({
    datev_berater_nr: null,
    datev_mandant_nr: null,
    steuerberater_email: null,
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDatevSettings().then(setSettings).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const updated = await saveDatevSettings(settings)
      setSettings(updated)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      setError('Speichern fehlgeschlagen.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold mb-1" style={{ color: 'rgb(var(--foreground))' }}>
          DATEV-Konfiguration
        </h3>
        <p className="text-xs" style={{ color: 'rgb(var(--foreground-muted))' }}>
          Pflichtfelder für den DATEV EXTF Buchungsstapel-Export.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Beraternummer */}
        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: 'rgb(var(--foreground-muted))' }}>
            Beraternummer (5-stellig)
          </label>
          <input
            type="text"
            maxLength={5}
            pattern="\d{5}"
            placeholder="12345"
            value={settings.datev_berater_nr ?? ''}
            onChange={(e) => setSettings((s) => ({ ...s, datev_berater_nr: e.target.value || null }))}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            style={{
              backgroundColor: 'rgb(var(--background))',
              borderColor: 'rgb(var(--border))',
              color: 'rgb(var(--foreground))',
            }}
          />
        </div>

        {/* Mandantennummer */}
        <div>
          <label className="block text-xs font-medium mb-1" style={{ color: 'rgb(var(--foreground-muted))' }}>
            Mandantennummer (5-stellig)
          </label>
          <input
            type="text"
            maxLength={5}
            pattern="\d{5}"
            placeholder="00001"
            value={settings.datev_mandant_nr ?? ''}
            onChange={(e) => setSettings((s) => ({ ...s, datev_mandant_nr: e.target.value || null }))}
            className="w-full rounded-lg border px-3 py-2 text-sm"
            style={{
              backgroundColor: 'rgb(var(--background))',
              borderColor: 'rgb(var(--border))',
              color: 'rgb(var(--foreground))',
            }}
          />
        </div>
      </div>

      {/* Steuerberater-E-Mail */}
      <div>
        <label className="block text-xs font-medium mb-1" style={{ color: 'rgb(var(--foreground-muted))' }}>
          Steuerberater-E-Mail (optional)
        </label>
        <input
          type="email"
          placeholder="steuerberater@kanzlei.de"
          value={settings.steuerberater_email ?? ''}
          onChange={(e) => setSettings((s) => ({ ...s, steuerberater_email: e.target.value || null }))}
          className="w-full rounded-lg border px-3 py-2 text-sm"
          style={{
            backgroundColor: 'rgb(var(--background))',
            borderColor: 'rgb(var(--border))',
            color: 'rgb(var(--foreground))',
          }}
        />
        <p className="text-xs mt-1" style={{ color: 'rgb(var(--foreground-muted))' }}>
          Wird für "An Steuerberater senden" in den Berichten benötigt.
        </p>
      </div>

      {error && (
        <p className="text-xs" style={{ color: 'rgb(var(--danger, 239 68 68))' }}>{error}</p>
      )}

      <button
        onClick={handleSave}
        disabled={saving}
        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        style={{ backgroundColor: 'rgb(var(--primary))', color: '#ffffff' }}
      >
        {saving ? 'Speichern…' : saved ? '✓ Gespeichert' : 'Speichern'}
      </button>
    </div>
  )
}
```

**2c.** Add the DATEV tab to the tabs list and render `<DatevKonfigurationTab />` in the tab panel. Follow the exact same pattern as the existing tabs in the file (TabsList + TabsTrigger + TabsContent).

### Step 3: Verify TypeScript compiles

```bash
cd /Users/sadanakb/rechnungskern/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: No errors

### Step 4: Commit

```bash
cd /Users/sadanakb/rechnungskern
git add frontend/lib/api.ts frontend/app/\(dashboard\)/settings/page.tsx
git commit -m "feat: add DATEV-Konfiguration tab to settings page"
```

---

## Task 6: Frontend Berichte — Enhanced DATEVExportSection

**Files:**
- Modify: `frontend/app/(dashboard)/berichte/page.tsx`
- Modify: `frontend/lib/api.ts` (add new exportDatevZip function)

### Step 1: Add exportDatevZip to api.ts

Open `frontend/lib/api.ts`. Find the existing `exportDatev` function (around line 521). Add **after** it:

```typescript
export async function exportDatevZip(fromMonth: string, toMonth: string): Promise<void> {
  const params = new URLSearchParams({ from_month: fromMonth, to_month: toMonth })
  const res = await api.get(`/api/datev/export?${params}`, { responseType: 'blob' })
  const url = URL.createObjectURL(new Blob([res.data], { type: 'application/zip' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `DATEV_${fromMonth}_${toMonth}.zip`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function getDatevCategorizedCount(fromMonth: string, toMonth: string): Promise<number> {
  // Re-use the monthly summary API or a simple invoices stats call to get count
  // Simplest: try the export and count, but for UI purposes, just show a hint
  // This is a best-effort count — just call the list endpoint with filters
  try {
    const res = await api.get('/api/invoices', {
      params: { limit: 1, skip: 0 }
    })
    return res.data.total || 0
  } catch {
    return 0
  }
}
```

### Step 2: Replace DATEVExportSection in berichte/page.tsx

Open `frontend/app/(dashboard)/berichte/page.tsx`.

Find `function DATEVExportSection()` (line ~404) and replace the entire function with:

```typescript
function DATEVExportSection() {
  const [fromMonth, setFromMonth] = useState(() => {
    const now = new Date()
    const y = now.getFullYear()
    const m = String(now.getMonth() + 1).padStart(2, '0')
    return `${y}-${m}`
  })
  const [toMonth, setToMonth] = useState(() => {
    const now = new Date()
    const y = now.getFullYear()
    const m = String(now.getMonth() + 1).padStart(2, '0')
    return `${y}-${m}`
  })
  const [loading, setLoading] = useState(false)
  const [emailing, setEmailing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [emailSuccess, setEmailSuccess] = useState(false)

  const handleExport = async () => {
    setLoading(true)
    setError(null)
    try {
      await exportDatevZip(fromMonth, toMonth)
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'Export fehlgeschlagen.'
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  const handleSendEmail = async () => {
    setEmailing(true)
    setError(null)
    setEmailSuccess(false)
    try {
      await sendDatevEmail(fromMonth, toMonth)
      setEmailSuccess(true)
      setTimeout(() => setEmailSuccess(false), 3000)
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'E-Mail fehlgeschlagen.'
      setError(detail)
    } finally {
      setEmailing(false)
    }
  }

  return (
    <SectionCard title="DATEV-Export" icon={Download}>
      <p className="text-sm mb-4" style={{ color: 'rgb(var(--foreground-muted))' }}>
        DATEV EXTF Buchungsstapel (ZIP) — nur kategorisierte Rechnungen
      </p>

      <div className="flex flex-wrap gap-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'rgb(var(--foreground-muted))' }}>Von:</span>
          <input
            type="month"
            value={fromMonth}
            onChange={(e) => setFromMonth(e.target.value)}
            className="rounded-lg border px-2 py-1 text-sm"
            style={{
              backgroundColor: 'rgb(var(--background))',
              borderColor: 'rgb(var(--border))',
              color: 'rgb(var(--foreground))',
            }}
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'rgb(var(--foreground-muted))' }}>Bis:</span>
          <input
            type="month"
            value={toMonth}
            onChange={(e) => setToMonth(e.target.value)}
            className="rounded-lg border px-2 py-1 text-sm"
            style={{
              backgroundColor: 'rgb(var(--background))',
              borderColor: 'rgb(var(--border))',
              color: 'rgb(var(--foreground))',
            }}
          />
        </div>
      </div>

      {error && (
        <p className="text-xs mb-3" style={{ color: 'rgb(var(--danger, 239 68 68))' }}>
          {error}
        </p>
      )}
      {emailSuccess && (
        <p className="text-xs mb-3" style={{ color: 'rgb(var(--success, 34 197 94))' }}>
          ✓ E-Mail an Steuerberater wird versendet
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          onClick={handleExport}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          style={{ backgroundColor: 'rgb(var(--primary))', color: '#ffffff' }}
        >
          <Download size={14} />
          {loading ? 'Exportiere…' : 'ZIP Exportieren'}
        </button>

        <button
          onClick={handleSendEmail}
          disabled={emailing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          style={{
            backgroundColor: 'transparent',
            borderWidth: 1,
            borderStyle: 'solid',
            borderColor: 'rgb(var(--border))',
            color: 'rgb(var(--foreground))',
          }}
        >
          <Mail size={14} />
          {emailing ? 'Sende…' : 'An Steuerberater senden'}
        </button>
      </div>
    </SectionCard>
  )
}
```

Also add the `Mail` icon to the lucide-react import and the `sendDatevEmail` + `exportDatevZip` to the api imports at the top of the file.

### Step 3: Verify TypeScript compiles

```bash
cd /Users/sadanakb/rechnungskern/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: No TypeScript errors

### Step 4: Commit

```bash
cd /Users/sadanakb/rechnungskern
git add frontend/app/\(dashboard\)/berichte/page.tsx frontend/lib/api.ts
git commit -m "feat: enhance DATEV export UI with month range, ZIP download, send-email button"
```

---

## Task 7: Final Verification + Changelog v1.0.0 + Merge

**Files:**
- Modify: `frontend/app/(marketing)/changelog/page.tsx`
- Modify: `frontend/components/layout/SidebarNav.tsx`
- Modify: `.claude/CHECKPOINT.md`

### Step 1: Run full backend test suite

```bash
cd /Users/sadanakb/rechnungskern/backend
python -m pytest --tb=short -q 2>&1 | tail -10
```

Expected: All tests pass (446+ including new Phase 10 tests), 0 failures.

### Step 2: Run frontend build

```bash
cd /Users/sadanakb/rechnungskern/frontend
npx next build 2>&1 | tail -15
```

Expected: Build succeeds, 0 TypeScript errors. Route count ≥ 114.

### Step 3: Add v1.0.0 changelog entry

Open `frontend/app/(marketing)/changelog/page.tsx`. Find the `releases` array. Add at the **top** (before the existing entries):

```typescript
{
  version: '1.0.0',
  date: '28. Februar 2026',
  type: 'major' as const,
  title: 'DATEV-Export — Buchungsstapel v700',
  description: 'Vollständiger DATEV EXTF Buchungsstapel-Export (ZIP) mit Beraternummer/Mandantennummer, SKR03-Kontenfilterung und Steuerberater-E-Mail-Benachrichtigung.',
  changes: [
    { type: 'new', text: 'DATEV EXTF v700 ZIP-Export mit Buchungsstapel.csv + Stammdaten.csv' },
    { type: 'new', text: 'Nur kategorisierte Rechnungen (Phase 9 SKR03) werden exportiert' },
    { type: 'new', text: 'Beraternummer + Mandantennummer in EXTF-Header eingebettet' },
    { type: 'new', text: 'DATEV-Konfiguration in Einstellungen (Beraternummer, Mandantennummer, Steuerberater-E-Mail)' },
    { type: 'new', text: '"An Steuerberater senden" Button — E-Mail-Benachrichtigung für Steuerberater' },
    { type: 'improved', text: 'Berichte: Monatsbereich-Picker ersetzt Quartal-Auswahl im DATEV-Export' },
  ],
},
```

### Step 4: Update version in SidebarNav.tsx

Open `frontend/components/layout/SidebarNav.tsx`. Find the version badge (around line 144):

Change:
```
5.0.0
```
To:
```
6.0.0
```

### Step 5: Commit changelog + version

```bash
cd /Users/sadanakb/rechnungskern
git add frontend/app/\(marketing\)/changelog/page.tsx frontend/components/layout/SidebarNav.tsx
git commit -m "feat: add v1.0.0 changelog entry and bump version to 6.0.0"
```

### Step 6: Merge to master

```bash
cd /Users/sadanakb/rechnungskern
git checkout master
git merge feature/phase10-datev-export --no-ff -m "feat: merge Phase 10 — DATEV-Export (EXTF v700 ZIP, SKR03-Filter, Steuerberater-E-Mail)"
```

### Step 7: Update CHECKPOINT.md

Open `.claude/CHECKPOINT.md`. Replace entire contents with:

```markdown
# Checkpoint — 2026-02-28

## Ziel
RechnungsKern — production-ready German e-invoicing SaaS, alle Phasen 1-10 abgeschlossen.

## Erledigt
- [x] Phase 1: Marktreife (Multi-Tenant Auth, Landing Page, Stripe, PWA, MDX Blog)
- [x] Phase 2: Features + SEO (Mahnwesen, Cmd+K, TanStack Table, pSEO 10 Branchen × 16 Bundesländer)
- [x] Phase 3: Launch-Readiness (Error Boundaries, Security Headers, Alembic, Feature Gating, Glossar)
- [x] Phase 4: Completeness & Polish (Profil, Passwort-Reset, E-Mail-Verifizierung, Stripe Billing, Teams)
- [x] Phase 5: Integrations & Growth (Webhooks, API-Keys, Audit-Log, Templates, Bulk-Ops, Reports, CI/CD)
- [x] Phase 6: UX Hardening (Invoice Detail, ZUGFeRD Export, Notifications, Onboarding, PWA, Print, Filter)
- [x] Phase 7: Business Logic (Payment Status, Contacts, Sequences, Rate Limiting, CSV Import, Stats, Overdue)
- [x] Phase 8: Production Excellence + Kundenportal (ARQ, Webhook Retry, S3 Storage, Share Links, Portal, Email)
- [x] Phase 9: KI-Suite + Echtzeit (GPT-4o-mini, WebSocket, Chat-Assistent, SKR03-Kategorisierung, Monatszusammenfassung)
- [x] Phase 10: DATEV-Export (EXTF v700 ZIP, SKR03-Filter, Beraternummer/Mandantennummer, Steuerberater-E-Mail)

## Entscheidungen
- Auth: get_current_user returns dict; _resolve_org_id() via OrganizationMember join
- Route-Ordering: Named routes vor /{invoice_id}
- CSS: rgb(var(--primary)) usw. — nie hardcoded Colors im Dashboard
- ARQ: Graceful degradation — arq_pool = None wenn Redis nicht verfügbar, sync fallback
- KI: GPT-4o-mini Primary (Standard), Claude Haiku (Complex/Chat), Ollama (Dev-Fallback)
- WebSocket: /ws?token=<jwt>, ConnectionManager Singleton in app/ws.py
- DATEV: Nur kategorisierte Rechnungen (skr03_account IS NOT NULL), EXTF v700 ZIP
- DATEV-Settings: datev_berater_nr, datev_mandant_nr, steuerberater_email auf Organization-Model

## Build/Test-Status
- Backend: 446+ Tests bestanden, 0 Fehler
- Frontend: 114+ Seiten gebaut, 0 TypeScript-Fehler
- Master: latest — Phase 10 gemergt

## Naechster Schritt
Phase 11 planen falls gewünscht. Mögliche Themen:
- Push Notifications (Firebase Web Push)
- GDPR Data Controls (Export, Löschung, Consent)
- OAuth Integration Marketplace (Zapier, n8n)
- Advanced Analytics (Prognosen, ML)
```

```bash
git add .claude/CHECKPOINT.md
git commit -m "docs: update CHECKPOINT.md — Phase 10 complete"
```

---

## Verification Checklist

After all tasks:

- [ ] `python -m pytest --tb=short -q` → 0 failures, 446+ passed
- [ ] `npx next build` → 0 TypeScript errors, route count ≥ 114
- [ ] `GET /api/datev/export?from_month=2024-01&to_month=2024-12` returns ZIP with 2 CSV files
- [ ] EXTF header line 1 contains configured Beraternummer
- [ ] Uncategorized invoices absent from Buchungsstapel
- [ ] Settings page shows DATEV-Konfiguration tab with 3 fields
- [ ] Berichte page has month range pickers + 2 buttons (ZIP Export + Steuerberater senden)
- [ ] Merge to master complete
