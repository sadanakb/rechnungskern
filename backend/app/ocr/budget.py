"""Budget-Limiter für OCR-Scans pro Plan und Monat."""
from datetime import datetime
from sqlalchemy import func

OCR_LIMITS = {
    "free": 5,
    "starter": 100,
    "professional": 500,
}


def check_ocr_budget(org_id: str, plan: str, db) -> tuple[bool, int, int]:
    """Prüfe ob die Org noch OCR-Budget hat.

    Returns: (is_allowed, scans_used_this_month, monthly_limit)
    """
    from app.models import Invoice

    limit = OCR_LIMITS.get(plan, 5)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    used = db.query(func.count(Invoice.id)).filter(
        Invoice.organization_id == org_id,
        Invoice.source_type == "ocr",
        Invoice.created_at >= month_start
    ).scalar() or 0

    return used < limit, used, limit
