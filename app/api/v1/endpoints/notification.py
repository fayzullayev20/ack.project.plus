from typing import Annotated, List

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_user
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    UnreadCountResponse,
    MessageResponse,
    NotificationCreate
)
from app.models.user import User


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = NotificationService(db)
    return service.get_notifications(current_user)


@router.patch("/{notification_id}/read", response_model=MessageResponse)
def mark_as_read(
    notification_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = NotificationService(db)
    service.mark_as_read(notification_id, current_user)
    return {"message": "Notification marked as read"}


@router.patch("/read-all", response_model=MessageResponse)
def mark_all_as_read(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = NotificationService(db)
    return service.mark_all_as_read(current_user)


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = NotificationService(db)
    return service.get_unread_count(current_user)


@router.post("", response_model=NotificationResponse)
def create_notification(
    payload: NotificationCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = NotificationService(db)
    return service.create_notification(
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
    )