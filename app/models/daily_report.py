from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    Text,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[Optional[str]] = mapped_column(Text)
    report_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "project_id",
            "report_date",
            name="uq_user_project_date_report",
        ),
    )

    attachments: Mapped[List["ReportAttachment"]] = relationship(
        "ReportAttachment",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User")
    task: Mapped[Optional["Task"]] = relationship("Task")
    project: Mapped["Project"] = relationship("Project")

    @property
    def file_ids(self) -> List[int]:
        return [a.file_id for a in self.attachments]

    @property
    def file_id(self) -> Optional[int]:
        return self.attachments[0].file_id if self.attachments else None

    @property
    def files(self):
        return [a.file for a in self.attachments]
