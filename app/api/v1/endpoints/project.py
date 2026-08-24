from typing import Annotated, List

from fastapi import APIRouter, Depends, status, Path, Body
from sqlalchemy.orm import Session

from app.core.deps import get_admin, get_db, get_user
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectsResponse,
    ProjectResponse,
    UpdateProjectStatusRequest,
    AssignManagerRequest,
    ProjectMemberResponse,
    AddProjectMemberRequest,
    ProjectProgressResponse,
    UpdateProjectRequest,
    ProjectDetailResponse,
    ProjectQueryParams,
)
from app.services.project_service import ProjectService
from app.models.user import User


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_admin)],
):
    service = ProjectService(db)

    project = service.create_project(
        name=data.name,
        description=data.description,
        deadline=data.deadline,
        manager_id=data.manager_id,
        current_user_role=current_user.role,
    )

    return project


@router.get("/", response_model=ProjectsResponse, status_code=status.HTTP_200_OK)
def get_projects(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
    params: Annotated[ProjectQueryParams, Depends()],
):
    service = ProjectService(db)

    projects = service.get_projects(current_user, params)

    return projects


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    project = service.get_project_detail(project_id, current_user)

    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: Annotated[int, Path()],
    data: UpdateProjectRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    project = service.update_project(
        project_id=project_id,
        data=data,
        current_user=current_user,
    )

    return project


@router.patch("/{project_id}/status")
def update_project_status(
    project_id: Annotated[int, Path()],
    data: Annotated[UpdateProjectStatusRequest, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    project = service.update_project_status(
        project_id=project_id, new_status=data.status, current_user=current_user
    )

    return project


@router.patch("/{project_id}/assign-manager")
def assign_manager(
    project_id: Annotated[int, Path()],
    data: AssignManagerRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    project = service.assign_manager(
        project_id=project_id, manager_id=data.manager_id, current_user=current_user
    )

    return project


@router.post("/{project_id}/accept")
def accept_project(
    project_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    project = service.accept_project(project_id=project_id, current_user=current_user)

    return project


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def get_members(
    project_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    members = service.get_project_members(project_id, current_user)

    return members


@router.post("/{project_id}/members", status_code=201)
def add_member(
    project_id: Annotated[int, Path()],
    data: AddProjectMemberRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    service.add_member(
        project_id=project_id, user_id=data.user_id, current_user=current_user
    )

    return {"message": "Member added"}


@router.delete("/{project_id}/members/{user_id}", status_code=204)
def delete_member(
    project_id: Annotated[int, Path()],
    user_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    service.delete_member(
        project_id=project_id, user_id=user_id, current_user=current_user
    )

    return None


@router.get("/{project_id}/progress", response_model=ProjectProgressResponse)
def get_progress(
    project_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    service = ProjectService(db)

    return service.get_project_progress(project_id, current_user)
