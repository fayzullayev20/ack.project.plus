from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.schemas.task import CreateTask, TaskQueryParams, UpdateTask, AssignWorkerRequest
from app.repository.task_repo import TaskRepo
from app.repository.project_repo import ProjectRepo
from app.repository.auditlog_repo import AuditLogRepo
from app.models.auditlog import AuditAction
from app.services.notification_service import NotificationService


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.task_repo = TaskRepo(db)
        self.project_repo = ProjectRepo(db)
        self.log_repo = AuditLogRepo(db)
        self.notification_service = NotificationService(db)

    def create_task(self, data: CreateTask, project_id: int, current_user: User):
        project = self.project_repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role != UserRole.MANAGER:
            raise HTTPException(403, "Only manager can create task")

        if project.manager_id != current_user.id:
            raise HTTPException(403, "Not your project")

        if data.deadline and data.deadline < datetime.now(timezone.utc):
            raise HTTPException(400, "Deadline cannot be in the past")

        task = self.task_repo.create(
            project_id=project_id,
            title=data.title,
            description=data.description,
            deadline=data.deadline,
        )

        self.log_repo.create_log(
            current_user.id,
            AuditAction.CREATE,
            "task",
            task.id,
        )

        return task

    def update_task(self, task_id: int, data: UpdateTask, manager: User):
        task = self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(404, "Task not found")

        if manager.role != UserRole.MANAGER:
            raise HTTPException(403, "Only manager can update task")

        if task.project.manager_id != manager.id:
            raise HTTPException(403, "Not allowed")

        update_data = data.model_dump(exclude_unset=True)

        if "status" in update_data:
            new_status = update_data["status"]

            if not task.status.can_transition(new_status):
                raise HTTPException(
                    400,
                    f"Invalid status transition: {task.status} → {new_status}",
                )

        task = self.task_repo.update(task, update_data)

        self.log_repo.create_log(
            manager.id,
            AuditAction.UPDATE,
            "task",
            task.id,
        )

        return task

    def update_task_status(self, task_id: int, data, user: User):
        task = self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(404, "Task not found")

        is_assigned = self.task_repo.get_assignment(task_id, user.id) is not None
        is_manager = user.role == UserRole.MANAGER and task.project.manager_id == user.id
        is_admin = user.role == UserRole.ADMIN

        if not (is_assigned or is_manager or is_admin):
            raise HTTPException(403, "You do not have permission to update this task status")

        if task.status.is_final():
            raise HTTPException(400, "Task already completed or canceled")

        new_status = data.status

        if not task.status.can_transition(new_status):
            raise HTTPException(
                400,
                f"Invalid status transition: {task.status} → {new_status}",
            )

        old_status = task.status
        task.status = new_status

        self.task_repo.add_status_history(
            task_id=task.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=user.id,
        )

        task = self.task_repo.update(task, {"status": new_status})

        self.log_repo.create_log(
            user.id,
            AuditAction.UPDATE,
            "task",
            task.id,
        )

        # Manager ga notification — worker task statusini o'zgartirdi
        if task.project and task.project.manager_id:
            self.notification_service.create_notification(
                user_id=task.project.manager_id,
                title="Task Status Updated",
                message=f"Task '{task.title}' status: {old_status} → {new_status}",
            )

        return task

    def assign_worker(self, task_id: int, data: AssignWorkerRequest, manager: User):
        task = self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(404, "Task not found")

        if manager.role != UserRole.MANAGER:
            raise HTTPException(403, "Only manager can assign worker")

        if task.project.manager_id != manager.id:
            raise HTTPException(403, "Not allowed")

        if self.task_repo.get_assignment(task_id, data.user_id):
            raise HTTPException(400, "User already assigned")

        if task.status.is_final():
            raise HTTPException(400, "Cannot assign worker to final task")

        self.task_repo.assign_user(
            task_id=task_id,
            user_id=data.user_id,
            role_on_task=data.role_on_task,
            assigned_by=manager.id,
        )

        self.log_repo.create_log(
            manager.id,
            AuditAction.ASSIGN,
            "task",
            task.id,
        )

        # Worker ga notification — unga task biriktirildi
        self.notification_service.create_notification(
            user_id=data.user_id,
            title="New Task Assigned",
            message=f"You have been assigned to task: '{task.title}'",
        )

        return task

    def unassign_worker(self, task_id: int, user_id: int, manager: User):
        task = self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(404, "Task not found")

        if manager.role != UserRole.MANAGER:
            raise HTTPException(403, "Only manager can unassign worker")

        if task.project.manager_id != manager.id:
            raise HTTPException(403, "Not allowed")

        if task.status.is_final():
            raise HTTPException(400, "Cannot modify final task")

        if not self.task_repo.get_assignment(task_id, user_id):
            raise HTTPException(400, "User is not assigned to this task")

        self.task_repo.unassign_user(task_id, user_id)

        self.log_repo.create_log(
            manager.id,
            AuditAction.UNASSIGN,
            "task",
            task.id,
        )

        # Worker ga notification — taskdan olib tashlandi
        self.notification_service.create_notification(
            user_id=user_id,
            title="Task Unassigned",
            message=f"You have been removed from task: '{task.title}'",
        )

        return task

    def get_task_assignments(self, task_id: int, user: User):
        task = self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(404, "Task not found")

        if user.role == UserRole.MANAGER and task.project.manager_id != user.id:
            raise HTTPException(403, "Not allowed")
        elif user.role == UserRole.WORKER:
            if not self.project_repo.is_project_member(task.project_id, user.id):
                raise HTTPException(403, "Not allowed")

        return self.task_repo.get_assignments(task_id)

    def get_tasks(self, user: User, params: TaskQueryParams):
        if user.role == UserRole.ADMIN:
            return self.task_repo.get_all_tasks(params=params)

        if user.role == UserRole.MANAGER:
            params.manager_id = user.id
            return self.task_repo.filter_tasks(params)

        if user.role == UserRole.WORKER:
            params.worker_ids = [user.id]
            return self.task_repo.filter_tasks(params)  

        return []

    def get_task(self, task_id: int, user: User):
        task = self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(404, "Task not found")

        if user.role == UserRole.ADMIN:
            return task

        if user.role == UserRole.MANAGER:
            if task.project.manager_id != user.id:
                raise HTTPException(403, "Not allowed")
            return task

        if user.role == UserRole.WORKER:
            if not self.task_repo.get_assignment(task.id, user.id):
                raise HTTPException(403, "Not allowed")
            return task

    def get_task_history(self, task_id: int, user: User):
        task = self.task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(404, "Task not found")

        if user.role == UserRole.ADMIN:
            return self.task_repo.get_status_history(task_id)

        if user.role == UserRole.MANAGER:
            if task.project.manager_id != user.id:
                raise HTTPException(403, "Not allowed")
            return self.task_repo.get_status_history(task_id)

        if user.role == UserRole.WORKER:
            if not self.task_repo.get_assignment(task_id, user.id):
                raise HTTPException(403, "Not allowed")
            return self.task_repo.get_status_history(task_id)