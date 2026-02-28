"""Push Notification Router — Phase 11."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth_jwt import get_current_user
from app.database import get_db
from app.models import Organization, OrganizationMember, PushSubscription

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_org(current_user: dict, db: Session) -> Organization:
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == int(current_user["user_id"])
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    return org


class SubscribeRequest(BaseModel):
    fcm_token: str
    device_label: Optional[str] = None


@router.post("/subscribe")
def subscribe(
    body: SubscribeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register an FCM token for push notifications. Idempotent."""
    org = _resolve_org(current_user, db)
    user_id = int(current_user["user_id"])

    # Idempotent: update label if token exists
    existing = db.query(PushSubscription).filter(
        PushSubscription.fcm_token == body.fcm_token,
        PushSubscription.user_id == user_id,
    ).first()

    if existing:
        if body.device_label:
            existing.device_label = body.device_label
        db.commit()
    else:
        sub = PushSubscription(
            user_id=user_id,
            organization_id=org.id,
            fcm_token=body.fcm_token,
            device_label=body.device_label,
        )
        db.add(sub)
        db.commit()

    return {"subscribed": True, "fcm_token": body.fcm_token}


@router.delete("/unsubscribe", status_code=204)
def unsubscribe(
    fcm_token: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove an FCM token. Returns 204."""
    user_id = int(current_user["user_id"])
    db.query(PushSubscription).filter(
        PushSubscription.fcm_token == fcm_token,
        PushSubscription.user_id == user_id,
    ).delete()
    db.commit()
    return Response(status_code=204)


@router.get("/status")
def status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if current user has any active push subscriptions."""
    user_id = int(current_user["user_id"])
    count = db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id
    ).count()
    return {"subscribed": count > 0, "subscription_count": count}
