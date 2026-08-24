from typing import Annotated, List

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_admin
from app.models.user import User
from app.schemas.auditlog import AuditLogListResponse, AuditLogResponse, AuditLogQueryParams
from app.services.auditlog_service import AuditLogService


router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/", response_model=AuditLogListResponse, status_code=200)
def get_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_admin)],
    params: Annotated[AuditLogQueryParams, Depends()],
):
    service = AuditLogService(db)
    return service.get_all(current_user, params)


@router.get("/{log_id}", response_model=AuditLogResponse, status_code=200)
def get_audit_log(
    log_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_admin)],
):
    service = AuditLogService(db)
    return service.get_by_id(log_id, current_user)
