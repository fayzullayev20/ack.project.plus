from sqlalchemy.orm import Session

from app.models.help_request import HelpRequest
from app.models import Task, Project
from app.schemas.help_request import HelpRequestSortField, SortOrder


class HelpRequestRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, obj: HelpRequest):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_all(self):
        return self.db.query(HelpRequest).all()

    def get_by_id(self, id: int):
        return self.db.query(HelpRequest).filter(HelpRequest.id == id).first()

    def update(self, obj: HelpRequest):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def filter_help_requests(self, params):
        stmt = self.db.query(HelpRequest)

        if params.ids:
            stmt = stmt.filter(
                HelpRequest.id.in_(params.ids)
            )

        if params.task_ids:
            stmt = stmt.filter(
                HelpRequest.task_id.in_(params.task_ids)
            )

        if params.requested_by:
            stmt = stmt.filter(
                HelpRequest.requested_by == params.requested_by
            )

        if params.requester_ids:
            stmt = stmt.filter(
                HelpRequest.requested_by.in_(params.requester_ids)
            )

        if params.manager_id:
            stmt = (
                stmt.join(Task, Task.id == HelpRequest.task_id)
                .join(Project, Project.id == Task.project_id)
                .filter(Project.manager_id == params.manager_id)
            )

        if params.status:
            stmt = stmt.filter(
                HelpRequest.status.in_(params.status)
            )

        if params.created_from:
            stmt = stmt.filter(
                HelpRequest.created_at >= params.created_from
            )

        if params.created_to:
            stmt = stmt.filter(
                HelpRequest.created_at <= params.created_to
            )

        SORT_FIELDS = {
            HelpRequestSortField.id: HelpRequest.id,
            HelpRequestSortField.status: HelpRequest.status,
            HelpRequestSortField.created_at: HelpRequest.created_at,
        }

        column = SORT_FIELDS[params.sort_by]

        stmt = stmt.order_by(
            column.asc()
            if params.order == SortOrder.asc
            else column.desc()
        )

        stmt = stmt.offset(
            (params.page - 1) * params.limit
        ).limit(params.limit)

        return stmt.all()
