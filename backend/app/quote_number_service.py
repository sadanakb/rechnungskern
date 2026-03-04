"""
Service for generating sequential, configurable quote numbers.
Mirrors the invoice_number_service pattern for quotes (Angebote).
"""
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models import QuoteNumberSequence
import uuid


def generate_next_quote_number(db: Session, org_id: int) -> str:
    """Atomically generate the next quote number for an org.

    Uses SELECT ... FOR UPDATE to prevent concurrent duplicates.
    Falls back to a UUID-based format if no sequence is configured.
    """
    seq = db.query(QuoteNumberSequence).filter(
        QuoteNumberSequence.organization_id == org_id
    ).with_for_update().first()

    if not seq:
        # No sequence configured — use default format
        return f"ANB-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    current_year = datetime.now().year

    # Reset counter if new year and reset_yearly is True
    if seq.reset_yearly and seq.last_reset_year != current_year:
        seq.current_counter = 0
        seq.last_reset_year = current_year

    seq.current_counter += 1
    db.flush()  # Write the increment before committing

    # Format: {prefix}{sep}{year}{sep}{counter:0{padding}}
    year_str = str(current_year)
    counter_str = str(seq.current_counter).zfill(seq.padding)

    parts = [seq.prefix, year_str, counter_str]
    return seq.separator.join(parts)
