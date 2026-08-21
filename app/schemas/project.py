from datetime import date

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, EmailStr

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
