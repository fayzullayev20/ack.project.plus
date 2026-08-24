from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repository.project_repo import ProjectRepo
from app.repository.auditlog_repo import AuditLogRepo
from app.models.project import Project
from app.models.user import User, UserRole
from app.models.project import ProjectStatus
from app.models.auditlog import AuditAction
from app.schemas.project import ProjectQueryParams


ALLOWED_TRANSITIONS = {
    ProjectStatus.DRAFT: [ProjectStatus.ASSIGNED],
    ProjectStatus.ASSIGNED: [
        ProjectStatus.ACTIVE,
        ProjectStatus.ON_HOLD,
        ProjectStatus.ARCHIVED,
    ],
    ProjectStatus.ACTIVE: [
        ProjectStatus.ON_HOLD,
        ProjectStatus.COMPLETED,
        ProjectStatus.ARCHIVED,
    ],
    ProjectStatus.ON_HOLD: [
        ProjectStatus.ACTIVE,
        ProjectStatus.ARCHIVED,
    ],
    ProjectStatus.COMPLETED: [
        ProjectStatus.ARCHIVED,
    ],
    ProjectStatus.ARCHIVED: [],
}


class ProjectService:
    def __init__(self, db: Session):
        self.repo = ProjectRepo(db)
        self.log_repo = AuditLogRepo(db)

    def create_project(
        self,
        name: str,
        description: str | None,
        deadline,
        manager_id: int,
        current_user_role: str,
    ):
        if current_user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can create project",
            )

        manager = self.repo.get_user_by_id(manager_id)
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found",
            )

        if manager.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user must have manager role",
            )

        project = Project(
            name=name,
            description=description,
            deadline=deadline,
            manager_id=manager_id,
            status=ProjectStatus.ASSIGNED,
        )

        project = self.repo.create_project(project)

        self.log_repo.create_log(manager_id, AuditAction.CREATE, "project", project.id)

        return project

    def get_projects(self, user: User, params: ProjectQueryParams):

        if user.role == UserRole.ADMIN:
            return self.repo.get_all_projects(params)

        elif user.role == UserRole.MANAGER:
            return self.repo.get_projects_by_manager(user.id, params)

        elif user.role == UserRole.WORKER:
            return self.repo.get_projects_by_user(user.id, params)

        return []

    def get_project_detail(self, project_id: int, user):

        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if user.role == UserRole.ADMIN:
            return project

        if user.role == UserRole.MANAGER:
            if project.manager_id != user.id:
                raise HTTPException(403, "Access denied")
            return project

        if user.role == UserRole.WORKER:
            is_member = self.repo.is_project_member(project_id, user.id)

            if not is_member:
                raise HTTPException(403, "Access denied")

            return project

        raise HTTPException(403, "Access denied")

    def get_project_members(self, project_id: int, current_user):

        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role == UserRole.ADMIN:
            pass

        elif current_user.role == UserRole.MANAGER:
            if project.manager_id != current_user.id:
                raise HTTPException(403, "Access denied")

        elif current_user.role == UserRole.WORKER:
            is_member = self.repo.is_member(project_id, current_user.id)
            if not is_member:
                raise HTTPException(403, "Access denied")

        else:
            raise HTTPException(403, "Access denied")

        return self.repo.get_project_members(project_id)

    def add_member(self, project_id: int, user_id: int, current_user):

        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role == UserRole.ADMIN:
            pass

        elif current_user.role == UserRole.MANAGER:
            if project.manager_id != current_user.id:
                raise HTTPException(403, "Access denied")

        else:
            raise HTTPException(403, "Only admin or manager")

        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(404, "User not found")

        if user.role != UserRole.WORKER:
            raise HTTPException(400, "Only worker can be added")

        if self.repo.is_member(project_id, user_id):
            raise HTTPException(400, "Already member")

        member = self.repo.add_member(project_id, user_id)

        self.log_repo.create_log(
            current_user.id,
            AuditAction.ASSIGN,
            "project_member",
            project_id,
        )

        return member

    def update_project_status(self, project_id: int, new_status, current_user):

        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role == UserRole.ADMIN:
            pass

        elif current_user.role == UserRole.MANAGER:
            if project.manager_id != current_user.id:
                raise HTTPException(403, "Access denied")

        else:
            raise HTTPException(403, "Only admin or manager")

        current_status = project.status

        if new_status not in ALLOWED_TRANSITIONS[current_status]:
            raise HTTPException(
                400, f"Invalid transition: {current_status} -> {new_status}"
            )

        project.status = new_status

        project = self.repo.update_project(project)

        self.log_repo.create_log(
            current_user.id, AuditAction.UPDATE, "project", project.id
        )

        return project

    def assign_manager(self, project_id: int, manager_id: int, current_user):

        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(403, "Only admin can assign manager")

        manager = self.repo.get_user_by_id(manager_id)

        if not manager:
            raise HTTPException(404, "User not found")

        if manager.role != UserRole.MANAGER:
            raise HTTPException(400, "User is not manager")

        project.manager_id = manager_id

        project = self.repo.update_project(project)

        self.log_repo.create_log(
            current_user.id, AuditAction.ASSIGN, "project", project.id
        )

        return project

    def accept_project(self, project_id: int, current_user):

        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role != UserRole.MANAGER:
            raise HTTPException(403, "Only manager can accept project")

        if project.manager_id != current_user.id:
            raise HTTPException(403, "Access denied")

        if project.status != ProjectStatus.ASSIGNED:
            raise HTTPException(400, "Project already accepted or invalid state")

        project.status = ProjectStatus.ACTIVE

        project = self.repo.update_project(project)

        self.log_repo.create_log(
            current_user.id,
            AuditAction.UPDATE,
            "project",
            project.id,
        )

        return project

    def delete_member(self, project_id: int, user_id: int, current_user):

        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role == UserRole.ADMIN:
            pass

        elif current_user.role == UserRole.MANAGER:
            if project.manager_id != current_user.id:
                raise HTTPException(403, "Access denied")

        else:
            raise HTTPException(403, "Only admin or manager")

        if project.manager_id == user_id:
            raise HTTPException(400, "Cannot remove project manager")

        member = self.repo.delete_member(project_id, user_id)

        if not member:
            raise HTTPException(404, "Member not found")

        self.log_repo.create_log(
            current_user.id,
            AuditAction.UNASSIGN,
            "project_member",
            project_id,
        )

        return True

    def get_project_progress(self, project_id: int, current_user):

        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role == UserRole.ADMIN:
            pass

        elif current_user.role == UserRole.MANAGER:
            if project.manager_id != current_user.id:
                raise HTTPException(403, "Access denied")

        elif current_user.role == UserRole.WORKER:
            is_member = self.repo.is_member(project_id, current_user.id)
            if not is_member:
                raise HTTPException(403, "Access denied")

        else:
            raise HTTPException(403, "Access denied")

        total, completed = self.repo.get_project_tasks_stats(project_id)

        progress = 0.0
        if total > 0:
            progress = (completed / total) * 100

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "progress": round(progress, 2),
        }

    def update_project(self, project_id: int, data, current_user):
        project = self.repo.get_project_by_id(project_id)

        if not project:
            raise HTTPException(404, "Project not found")

        if current_user.role == UserRole.ADMIN:
            pass

        elif current_user.role == UserRole.MANAGER:
            if project.manager_id != current_user.id:
                raise HTTPException(403, "Access denied")

        else:
            raise HTTPException(403, "Only admin or manager")

        if data.name is not None:
            project.name = data.name

        if data.description is not None:
            project.description = data.description

        if data.deadline is not None:
            project.deadline = data.deadline

        project = self.repo.update_project(project)

        self.log_repo.create_log(
            current_user.id,
            AuditAction.UPDATE,
            "project",
            project.id,
        )

        return project
