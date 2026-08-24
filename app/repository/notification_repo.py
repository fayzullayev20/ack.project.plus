from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.notification import Notification


class NotificationRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_user_notifications(self, user_id: int) -> list[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

    def get_notification_by_id(self, notification_id: int) -> Notification | None:
        return (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

    def create_notification(
        self, user_id: int, title: str, message: str
    ) -> Notification:
        notification = Notification(user_id=user_id, title=title, message=message)
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_as_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_as_read(self, user_id: int) -> None:
        self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({"is_read": True})
        self.db.commit()

    def get_unread_count(self, user_id: int) -> int:
        return (
            self.db.query(func.count(Notification.id))
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .scalar()
        )