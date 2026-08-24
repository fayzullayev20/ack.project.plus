from datetime import datetime
from typing import Optional, List
import enum

from sqlalchemy import String, Integer, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    WORKER = "worker"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.WORKER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_first_login: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False
    )
    managed_projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="manager"
    )
    task_assignments: Mapped[List["TaskAssignment"]] = relationship(
        "TaskAssignment", foreign_keys="TaskAssignment.user_id", back_populates="user"
    )
    assigned_tasks: Mapped[List["TaskAssignment"]] = relationship(
        "TaskAssignment",
        foreign_keys="TaskAssignment.assigned_by",
        back_populates="assigner",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary="user_skills",
        lazy="selectin"
    )