from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repository.help_request_repo import HelpRequestRepo
from app.models.help_request import HelpRequest, HelpRequestStatus
from app.models.user import User, UserRole
from app.models.task import Task
from app.services.notification_service import NotificationService
from app.schemas.help_request import HelpRequestQueryParams


class HelpRequestService:
    def __init__(self, db: Session):
        self.repo = HelpRequestRepo(db)
        self.db = db

    def create(self, task_id: int, current_user: User):

        if current_user.role != UserRole.WORKER:
            raise HTTPException(403, "Only worker can request help")

        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(404, "Task not found")

        help_request = HelpRequest(
            task_id=task_id,
            requested_by=current_user.id,
        )

        help_request = self.repo.create(help_request)

        if task.project and task.project.manager_id:
            NotificationService(self.db).create_notification(
                user_id=task.project.manager_id,
                title="Help Request",
                message=f"Help requested for task: {task.title}",
            )

        return help_request

    def get_all(self, current_user: User, params: HelpRequestQueryParams):
        if current_user.role == UserRole.ADMIN:
            pass

        elif current_user.role == UserRole.MANAGER:
            params.manager_id = current_user.id

        elif current_user.role == UserRole.WORKER:
            params.requested_by = current_user.id

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return self.repo.filter_help_requests(params)

    def get_by_id(self, request_id: int, current_user: User):

        help_request = self.repo.get_by_id(request_id)

        if not help_request:
            raise HTTPException(404, "Request not found")

        if current_user.role == UserRole.ADMIN:
            return help_request

        if current_user.role == UserRole.MANAGER:
            if help_request.task.project.manager_id != current_user.id:
                raise HTTPException(403, "Access denied")
            return help_request

        if current_user.role == UserRole.WORKER:
            if help_request.requested_by != current_user.id:
                raise HTTPException(403, "Access denied")
            return help_request

        raise HTTPException(403, "Access denied")

    def assign(self, request_id: int, current_user: User):

        help_request = self.repo.get_by_id(request_id)

        if not help_request:
            raise HTTPException(404, "Request not found")

        if current_user.role != UserRole.MANAGER:
            raise HTTPException(403, "Only manager")

        task = help_request.task
        if task.project.manager_id != current_user.id:
            raise HTTPException(403, "Not your project")

        help_request.status = HelpRequestStatus.ACCEPTED

        help_request = self.repo.update(help_request)

        NotificationService(self.db).create_notification(
            user_id=help_request.requested_by,
            title="Help Request Accepted",
            message="Your help request has been accepted",
        )

        return help_request

    def resolve(self, request_id: int, current_user: User):

        help_request = self.repo.get_by_id(request_id)

        if not help_request:
            raise HTTPException(404, "Request not found")

        if current_user.role != UserRole.MANAGER:
            raise HTTPException(403, "Only manager")

        task = help_request.task
        if task.project.manager_id != current_user.id:
            raise HTTPException(403, "Not your project")

        help_request.status = HelpRequestStatus.RESOLVED

        help_request = self.repo.update(help_request)

        NotificationService(self.db).create_notification(
            user_id=help_request.requested_by,
            title="Help Request Resolved",
            message="Your help request has been resolved",
        )

        return help_request
