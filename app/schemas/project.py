from datetime import date

import enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr
from fastapi import Query

from app.models.project import ProjectStatus
from app.models.user import UserRole
from app.models.task import TaskStatus


class ProjectMemberResponse(BaseModel):
    user_id: int
    role: str

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    deadline: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int = Field(gt=0)
    username: str
    email: EmailStr | None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    id: Optional[int]
    name: Optional[str]
    description: Optional[str]
    manager_id: Optional[int]
    status: ProjectStatus
    deadline: Optional[datetime]
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ProjectsResponse(BaseModel):
    items: list[ProjectResponse] = []
    total: int
    page: int
    limit: int
    total_pages: int


class ProjectDetailResponse(BaseModel):
    id: Optional[int]
    name: Optional[str]
    description: Optional[str]
    manager: UserResponse
    status: ProjectStatus
    deadline: Optional[datetime]
    created_at: Optional[datetime]
    tasks: list[TaskResponse] = []
    members: list[ProjectMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    deadline: date
    manager_id: int


class AddProjectMemberRequest(BaseModel):
    user_id: int


class UpdateProjectStatusRequest(BaseModel):
    status: ProjectStatus


class AssignManagerRequest(BaseModel):
    manager_id: int


class ProjectMemberResponse(BaseModel):
    user_id: int
    role: str

    class Config:
        from_attributes = True


class ProjectProgressResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    progress: float


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    deadline: date | None = None


class SortOrder(str, enum.Enum):
    asc = "asc"
    desc = "desc"

class ProjectSortField(str, enum.Enum):
    id = "id"
    name = "name"
    status = "status"
    deadline = "deadline"
    created_at = "created_at"

class ProjectQueryParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        status: list[ProjectStatus] = Query(default_factory=list),
        manager_id: int | None = Query(None),
        created_from: datetime | None = Query(None),
        created_to: datetime | None = Query(None),
        deadline_from: datetime | None = Query(None),
        deadline_to: datetime | None = Query(None),
        ids: list[int] = Query(default_factory=list),
        expired: bool | None = Query(None),
        sort_by: ProjectSortField = Query(ProjectSortField.created_at),
        order: SortOrder = Query(SortOrder.desc),
    ):
        self.page = page
        self.limit = limit
        self.search = search
        self.status = status
        self.manager_id = manager_id
        self.created_from = created_from
        self.created_to = created_to
        self.deadline_from = deadline_from
        self.deadline_to = deadline_to
        self.ids = ids
        self.expired = expired
        self.sort_by = sort_by
        self.order = order