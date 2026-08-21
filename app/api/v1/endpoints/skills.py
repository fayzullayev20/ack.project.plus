from typing import Annotated

from fastapi import APIRouter, Depends, Body, Path
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_admin, get_user
from app.models import User
from app.schemas.skills import SkillResponse, SkillUpdate, SkillCreate
from app.services.skills_service import SkillService


router = APIRouter(prefix="/skills", tags=["Skills"])


@router.post("/", response_model=SkillResponse, status_code=201)
def create_skill_view(
    data: Annotated[SkillCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_admin)],
):
    service = SkillService(db)
    skill = service.create_skill(name=data.name, admin=admin)

    return skill


@router.get("/", response_model=list[SkillResponse])
def list_skills_view(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = SkillService(db)
    skills = service.list_skills()
    return skills


@router.get("/{id}", response_model=SkillResponse)
def get_skill_view(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = SkillService(db)
    skill = service.get_skill_by_id(id)

    return skill


@router.patch("/{id}", response_model=SkillResponse)
def update_skill_view(
    id: Annotated[int, Path()],
    data: Annotated[SkillUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_admin)],
):
    service = SkillService(db)
    skill = service.update_skill(id=id, name=data.name, admin=admin)

    return skill


@router.delete("/{id}", status_code=204)
def delete_skill_view(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(get_admin)],
):
    service = SkillService(db)
    service.delete_skill(id=id, admin=admin)


@router.get("/my", response_model=list[SkillResponse])
def get_my_skills_view(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = SkillService(db)
    skills = service.get_user_skills(user)

    return skills
