import re
from datetime import datetime
from typing import Optional

from fastapi import Query
from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    EmailStr,
    ConfigDict,
)
from enum import Enum

from app.models.user import UserRole
from app.schemas.skills import SkillResponse
from app.schemas.user_profile import UserProfile
from app.schemas.project import ProjectResponse
from app.schemas.task import TaskResponse, TaskAssignmentResponse


USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")


class CreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: None | EmailStr = None
    role: UserRole = UserRole.WORKER
    skill_ids: list[int] = Field(default_factory=list)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()

        if not v:
            raise ValueError("Username cannot be empty")

        if not USERNAME_REGEX.match(v):
            raise ValueError(
                "Username must contain only letters, numbers, and underscores"
            )

        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        v = v.strip()

        if not v:
            raise ValueError("Password cannot be empty")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        return v

    @model_validator(mode="after")
    def validate_confirm_password(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

        return self


class UserResponseDetail(BaseModel):
    id: int = Field(gt=0)
    username: str
    email: EmailStr | None

    profile: UserProfile | None
    skills: list[SkillResponse] | None = []

    managed_projects: list[ProjectResponse] | None = []
    task_assignments: list[TaskAssignmentResponse] | None = []
    assigned_tasks: list[TaskAssignmentResponse] | None = []

    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int = Field(gt=0)
    username: str
    email: EmailStr | None
    role: UserRole
    skills: list[SkillResponse] | None = []
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateUserData(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    skill_ids: Optional[list[int]] = None

    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    confirm_password: Optional[str] = Field(default=None, min_length=8, max_length=128)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.password or self.confirm_password:
            if self.password != self.confirm_password:
                raise ValueError("passwords do not match")

        return self

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()

        if not v:
            raise ValueError("Username cannot be empty")

        if not USERNAME_REGEX.match(v):
            raise ValueError(
                "Username must contain only letters, numbers, and underscores"
            )

        return v


class UsersListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class UserSortField(str, Enum):
    created_at = "created_at"
    username = "username"
    email = "email"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    worker = "worker"


class UserQueryParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        search: str | None = Query(None),
        role: UserRole | None = Query(None),
        is_active: bool | None = Query(None),
        sort_by: UserSortField = Query(UserSortField.created_at),
        order: SortOrder = Query(SortOrder.desc),
        skill_ids: list[int] = Query(default_factory=list),
    ):
        self.page = page
        self.limit = limit
        self.search = search
        self.role = role
        self.is_active = is_active
        self.sort_by = sort_by
        self.order = order
        self.skill_ids = skill_ids