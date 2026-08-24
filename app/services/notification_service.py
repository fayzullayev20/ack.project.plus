from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repository.notification_repo import NotificationRepo
from app.models.notification import Notification
from app.models.user import User


class NotificationService:
    def __init__(self, db: Session):
        self.repo = NotificationRepo(db)

    def get_notifications(self, current_user: User) -> list[Notification]:
        return self.repo.get_user_notifications(current_user.id)

    def create_notification(
        self, user_id: int, title: str, message: str
    ) -> Notification:
        return self.repo.create_notification(
            user_id=user_id, title=title, message=message
        )

    def mark_as_read(
        self, notification_id: int, current_user: User
    ) -> Notification:
        notification = self.repo.get_notification_by_id(notification_id)

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return self.repo.mark_as_read(notification)

    def mark_all_as_read(self, current_user: User) -> dict:
        self.repo.mark_all_as_read(current_user.id)
        return {"message": "All notifications marked as read"}

    def get_unread_count(self, current_user: User) -> dict:
        count = self.repo.get_unread_count(current_user.id)
        return {"count": count}