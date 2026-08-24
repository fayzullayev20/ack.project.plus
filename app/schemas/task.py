from datetime import datetime
import enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, FutureDatetime
from fastapi import Query

from app.models.task import TaskStatus
from app.schemas.project import ProjectResponse


class CreateTask(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    deadline: FutureDatetime

    model_config = ConfigDict(extra="forbid")


class UpdateTask(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    deadline: Optional[FutureDatetime] = None
    status: Optional[TaskStatus] = None

    model_config = ConfigDict(extra="forbid")


class TaskResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    deadline: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskLIstResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    limit: int
    total_pages: int



class TaskAssignmentResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    assigned_by: Optional[int] = None
    role_on_task: Optional[str] = Field(default=None, max_length=50)
    assigned_at: datetime

    task: Optional[TaskResponse] = None

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(BaseModel):
    id: int

    project: ProjectResponse
    assignments: list[TaskAssignmentResponse] = []

    title: str
    description: Optional[str] = None
    status: TaskStatus
    deadline: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateTaskStatus(BaseModel):
    status: TaskStatus


class AssignWorkerRequest(BaseModel):
    user_id: int
    role_on_task: Optional[str] = None


class UnassignWorkerRequest(BaseModel):
    user_id: int


class TaskStatusHistoryResponse(BaseModel):
    id: int
    task_id: int
    old_status: TaskStatus
    new_status: TaskStatus
    changed_by: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskSortField(str, enum.Enum):
    id = "id"
    project_id = "project_id"
    title = "title"
    status = "status"
    deadline = "deadline"
    created_at = "created_at"


class SortOrder(str, enum.Enum):
    asc = "asc"
    desc = "desc"

class TaskQueryParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        project_id: int | None = Query(None),
        manager_id: int | None = Query(None),
        worker_ids: list[int] = Query(default_factory=list),
        status: list[TaskStatus] = Query(default_factory=list),
        ids: list[int] = Query(default_factory=list),
        created_from: datetime | None = Query(None),
        created_to: datetime | None = Query(None),
        deadline_from: datetime | None = Query(None),
        deadline_to: datetime | None = Query(None),
        expired: bool | None = Query(None),
        sort_by: TaskSortField = Query(TaskSortField.created_at),
        order: SortOrder = Query(SortOrder.desc)
    ):
        self.page = page
        self.limit = limit
        self.search = search
        self.project_id = project_id
        self.manager_id = manager_id
        self.worker_ids = worker_ids
        self.status = status
        self.ids = ids
        self.created_from = created_from
        self.created_to = created_to
        self.deadline_from = deadline_from
        self.deadline_to = deadline_to
        self.expired = expired
        self.sort_by = sort_by
        self.order = order
