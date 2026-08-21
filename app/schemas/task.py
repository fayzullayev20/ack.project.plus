from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, FutureDatetime

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
