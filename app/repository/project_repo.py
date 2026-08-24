from ast import stmt
import math

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.models.project_members import ProjectMember
from app.models.task import Task, TaskStatus
from app.schemas.project import ProjectQueryParams, ProjectSortField


class ProjectRepo:
    def __init__(self, db: Session):
        self.db = db

    def filter_projects_by_params(self, params: ProjectQueryParams, stmt: select = None):
        if stmt is None:
            stmt = select(Project)

        if params.search:
            stmt = stmt.where(
                or_(
                    Project.name.ilike(f"%{params.search}%"),
                    Project.description.ilike(f"%{params.search}%"),
                )
            )

        if params.status:
            stmt = stmt.where(Project.status.in_(params.status))

        if params.manager_id:
            stmt = stmt.where(Project.manager_id == params.manager_id)

        if params.ids:
            stmt = stmt.where(Project.id.in_(params.ids))

        if params.created_from:
            stmt = stmt.where(Project.created_at >= params.created_from)

        if params.created_to:
            stmt = stmt.where(Project.created_at <= params.created_to)

        if params.deadline_from:
            stmt = stmt.where(Project.deadline >= params.deadline_from)

        if params.deadline_to:
            stmt = stmt.where(Project.deadline <= params.deadline_to)

        if params.expired is not None:
            if params.expired:
                stmt = stmt.where(Project.deadline < func.now())
            else:
                stmt = stmt.where(Project.deadline >= func.now())

        SORT_FIELDS = {
            ProjectSortField.id: Project.id,
            ProjectSortField.name: Project.name,
            ProjectSortField.status: Project.status,
            ProjectSortField.deadline: Project.deadline,
            ProjectSortField.created_at: Project.created_at,
        }

        column = SORT_FIELDS.get(params.sort_by, Project.id)

        stmt = stmt.order_by(column.asc() if params.order == "asc" else column.desc())

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = self.db.scalar(count_stmt)

        stmt = stmt.offset((params.page - 1) * params.limit).limit(params.limit)
        items = self.db.execute(stmt).scalars().all()

        return {
            "items": items,
            "total": total,
            "page": params.page,
            "limit": params.limit,
            "total_pages": math.ceil(total / params.limit) if total else 1,
        }


    def get_user_by_id(self, id: int):
        return self.db.query(User).filter(User.id == id).first()

    def create_project(self, project: Project):
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_all_projects(self, params: ProjectQueryParams):
        return self.filter_projects_by_params(params)

    def get_projects_by_manager(self, manager_id: int, params: ProjectQueryParams):
        stmt = select(Project).where(Project.manager_id == manager_id)

        return self.filter_projects_by_params(params, stmt=stmt)

    def get_projects_by_user(self, user_id: int, params: ProjectQueryParams):
        stmt = select(Project).where(Project.members.any(ProjectMember.user_id == user_id))

        return self.filter_projects_by_params(params, stmt=stmt)

        
    def get_project_by_id(self, project_id: int):
        return (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.status != ProjectStatus.ARCHIVED)
            .first()
        )

    def is_project_member(self, project_id: int, user_id: int) -> bool:
        return (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
            .first()
            is not None
        )

    def add_member(self, project_id: int, user_id: int):
        member = ProjectMember(project_id=project_id, user_id=user_id, role="worker")

        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return member

    def is_member(self, project_id: int, user_id: int):
        return (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
            .first()
        )

    def update_project(self, project):
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project_members(self, project_id: int):
        return (
            self.db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id)
            .all()
        )

    def delete_member(self, project_id: int, user_id: int):
        member = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
            .first()
        )

        if not member:
            return None

        self.db.delete(member)
        self.db.commit()

        return member

    def get_project_tasks_stats(self, project_id: int):
        total = (
            self.db.query(func.count(Task.id))
            .filter(Task.project_id == project_id)
            .scalar()
        )

        completed = (
            self.db.query(func.count(Task.id))
            .filter(Task.project_id == project_id, Task.status == TaskStatus.DONE)
            .scalar()
        )

        return total or 0, completed or 0

    def get_user_project_ids(self, user_id: int) -> list[int]:
        return [
            m.project_id
            for m in self.db.query(ProjectMember.project_id)
            .filter(ProjectMember.user_id == user_id)
            .all()
        ]

    def get_manager_project_ids(self, manager_id: int) -> list[int]:
        return [
            p.id
            for p in self.db.query(Project.id)
            .filter(Project.manager_id == manager_id)
            .all()
        ]
