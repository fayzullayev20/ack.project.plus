from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repository.auditlog_repo import AuditLogRepo
from app.models.user import User, UserRole
from app.schemas.auditlog import AuditLogQueryParams


class AuditLogService:
    def __init__(self, db: Session):
        self.repo = AuditLogRepo(db)

    def get_all(self, current_user: User, params: AuditLogQueryParams):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can view audit logs",
            )

        return self.repo.get_all(params=params)

    def get_by_id(self, log_id: int, current_user: User):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can view audit logs",
            )

        log = self.repo.get_by_id(log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found",
            )

        return log
