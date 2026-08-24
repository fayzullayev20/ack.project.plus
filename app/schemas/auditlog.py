from datetime import datetime
from enum import Enum
import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict
from fastapi import Query

from app.models.auditlog import AuditAction


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: Optional[int]
    actor_user_name: Optional[str]
    action: AuditAction
    entity_type: str
    entity_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class SortOrder(str, enum.Enum):
    asc = "asc"
    desc = "desc"

class AuditSortField(str, enum.Enum):
    id = "id"
    action = "action"
    entity_type = "entity_type"
    entity_id = "entity_id"
    created_at = "created_at"


class AuditLogQueryParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        actor_user_id: int | None = Query(None),
        action: list[AuditAction] = Query(default_factory=list),
        entity_type: str | None = Query(None),
        entity_id: int | None = Query(None),
        created_from: datetime | None = Query(None),
        created_to: datetime | None = Query(None),
        ids: list[int] = Query(default_factory=list),
        sort_by: AuditSortField = Query(AuditSortField.created_at),
        order: SortOrder = Query(SortOrder.desc),
    ):
        self.page = page
        self.limit = limit
        self.actor_user_id = actor_user_id
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.created_from = created_from
        self.created_to = created_to
        self.ids = ids
        self.sort_by = sort_by
        self.order = order