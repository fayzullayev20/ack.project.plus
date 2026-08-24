from typing import Annotated, List

from fastapi import APIRouter, Depends, status, Path, Body
from sqlalchemy.orm import Session

from app.core.deps import (
    get_admin,
    get_db,
    get_user,
    get_manager,
    get_admin_or_manager,
    get_worker,
)
from app.models import User
from app.schemas.task import (
    CreateTask,
    TaskResponse,
    TaskDetailResponse,
    UpdateTask,
    UpdateTaskStatus,
    AssignWorkerRequest,
    UnassignWorkerRequest,
    TaskAssignmentResponse,
    TaskStatusHistoryResponse,
    TaskQueryParams,
    TaskLIstResponse
)
from app.services.task_service import TaskService


router = APIRouter(tags=["Tasks"])


@router.post(
    "/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201
)
def create_task_view(
    project_id: Annotated[int, Path()],
    data: Annotated[CreateTask, Body()],
    db: Annotated[Session, Depends(get_db)],
    manager: Annotated[User, Depends(get_manager)],
):
    service = TaskService(db)
    task = service.create_task(data, project_id, manager)

    return task


@router.get("/tasks", response_model=TaskLIstResponse)
def get_tasks_view(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
    params: Annotated[TaskQueryParams, Depends()],
):
    service = TaskService(db)
    tasks = service.get_tasks(user, params)

    return tasks


@router.get("/tasks/{id}", response_model=TaskDetailResponse)
def get_task_view(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = TaskService(db)
    task = service.get_task(id, user)

    return task


@router.patch("/tasks/{id}", response_model=TaskResponse)
def update_task_view(
    id: Annotated[int, Path()],
    data: Annotated[UpdateTask, Body()],
    db: Annotated[Session, Depends(get_db)],
    manager: Annotated[User, Depends(get_manager)],
):
    service = TaskService(db)
    updated_task = service.update_task(id, data, manager)

    return updated_task


@router.patch("/tasks/{id}/status", response_model=TaskResponse)
def task_status_view(
    id: Annotated[int, Path()],
    data: Annotated[UpdateTaskStatus, Body()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = TaskService(db)
    return service.update_task_status(task_id=id, data=data, user=user)


@router.post(
    "/tasks/{id}/assign",
    response_model=TaskDetailResponse,
    status_code=201,
)
def assign_worker_view(
    id: Annotated[int, Path()],
    data: Annotated[AssignWorkerRequest, Body()],
    db: Annotated[Session, Depends(get_db)],
    manager: Annotated[User, Depends(get_manager)],
):
    service = TaskService(db)
    return service.assign_worker(
        task_id=id,
        data=data,
        manager=manager,
    )


@router.delete("/tasks/{id}/unassign", response_model=TaskDetailResponse)
def unassign_worker_view(
    id: Annotated[int, Path()],
    data: Annotated[UnassignWorkerRequest, Body()],
    db: Annotated[Session, Depends(get_db)],
    manager: Annotated[User, Depends(get_manager)],
):
    service = TaskService(db)
    return service.unassign_worker(task_id=id, user_id=data.user_id, manager=manager)


@router.get("/tasks/{id}/assignments", response_model=list[TaskAssignmentResponse])
def get_assignments(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = TaskService(db)
    return service.get_task_assignments(
        task_id=id,
        user=user,
    )


@router.get("/tasks/{id}/history", response_model=list[TaskStatusHistoryResponse])
def get_task_history(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = TaskService(db)
    return service.get_task_history(task_id=id, user=user)


@router.get("/my/tasks", response_model=TaskLIstResponse)
def get_my_tasks(
    db: Annotated[Session, Depends(get_db)],
    worker: Annotated[User, Depends(get_worker)],
    params: Annotated[TaskQueryParams, Depends()],
):
    service = TaskService(db)
    return service.get_tasks(user=worker, params=params)


@router.get("/manager/tasks", response_model=TaskLIstResponse)
def get_manager_tasks(
    db: Annotated[Session, Depends(get_db)],
    manager: Annotated[User, Depends(get_manager)],
    params: Annotated[TaskQueryParams, Depends()],
):
    service = TaskService(db)
    return service.get_tasks(user=manager, params=params)
