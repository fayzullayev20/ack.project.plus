from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from fastapi import Query
from enum import Enum

from app.models.help_request import HelpRequestStatus


class HelpRequestCreate(BaseModel):
    task_id: int = Field(..., gt=0)


class HelpRequestResponse(BaseModel):
    id: int = Field(..., gt=0)
    task_id: int = Field(..., gt=0)
    requested_by: int = Field(..., gt=0)
    status: HelpRequestStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str



class HelpRequestSortField(str, Enum):
    id = "id"
    status = "status"
    created_at = "created_at"

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class HelpRequestQueryParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        ids: list[int] = Query(default_factory=list),
        task_ids: list[int] = Query(default_factory=list),
        requested_by: int | None = Query(None),
        requester_ids: list[int] = Query(default_factory=list),
        manager_id: int | None = Query(None),
        status: list[HelpRequestStatus] = Query(default_factory=list),
        created_from: datetime | None = Query(None),
        created_to: datetime | None = Query(None),
        sort_by: HelpRequestSortField = Query(
            HelpRequestSortField.created_at
        ),
        order: SortOrder = Query(SortOrder.desc),
    ):
        self.page = page
        self.limit = limit
        self.ids = ids
        self.task_ids = task_ids
        self.requested_by = requested_by
        self.requester_ids = requester_ids
        self.manager_id = manager_id
        self.status = status
        self.created_from = created_from
        self.created_to = created_to
        self.sort_by = sort_by
        self.order = order