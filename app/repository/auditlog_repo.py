import math

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.auditlog import AuditLog, AuditAction


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

    def get_all(self):
        return self.db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()

    def get_by_id(self, log_id: int):
        return self.db.query(AuditLog).filter(AuditLog.id == log_id).first()
