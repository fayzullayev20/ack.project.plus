import math

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.auditlog import AuditLog, AuditAction
from app.schemas.user import SortOrder
from app.schemas.auditlog import AuditLogListResponse, AuditLogQueryParams


class AuditLogRepo:
    def __init__(self, db: Session):
        self.db = db

    def create_log(
        self, user_id: int, action: AuditAction | str, entity_type: str, entity_id: int
    ):
        audit = AuditLog(
            actor_user_id=user_id,
            action=action.value if isinstance(action, AuditAction) else action,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)

        return audit

    def get_all(self, params: AuditLogQueryParams):
        query = self.db.query(AuditLog)

        if params.actor_user_id is not None:
            query = query.filter(AuditLog.actor_user_id == params.actor_user_id)

        if params.action:
            query = query.filter(AuditLog.action.in_(params.action))

        if params.entity_type is not None:
            query = query.filter(AuditLog.entity_type == params.entity_type)

        if params.entity_id is not None:
            query = query.filter(AuditLog.entity_id == params.entity_id)

        if params.created_from is not None:
            query = query.filter(AuditLog.created_at >= params.created_from)

        if params.created_to is not None:
            query = query.filter(AuditLog.created_at <= params.created_to)

        if params.ids:
            query = query.filter(AuditLog.id.in_(params.ids))

        SORT_FIELDS = {
            "id": AuditLog.id,
            "action": AuditLog.action,
            "entity_type": AuditLog.entity_type,
            "entity_id": AuditLog.entity_id,
            "created_at": AuditLog.created_at,
        }
        column = SORT_FIELDS.get(params.sort_by.value, AuditLog.created_at)

        total = query.count()

        items = (
            query
            .order_by(column.asc() if params.order == SortOrder.asc else column.desc())
            .offset((params.page - 1) * params.limit)
            .limit(params.limit)
            .all()
        )

        return AuditLogListResponse(
            items=items,
            total=total,
            page=params.page,
            limit=params.limit,
            total_pages=math.ceil(total / params.limit) if total else 1,
        )

    def get_by_id(self, log_id: int):
        return self.db.query(AuditLog).filter(AuditLog.id == log_id).first()
