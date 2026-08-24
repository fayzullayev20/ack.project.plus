from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class Skill(Base):
    __tablename__ = "skills"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String, unique=True)

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_skills",
        lazy="selectin",
        back_populates="skills"
    )


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id = mapped_column(ForeignKey("users.id"), primary_key=True)
    skill_id = mapped_column(ForeignKey("skills.id"), primary_key=True)