from sqlalchemy.orm import Session

from app.models import Task, TaskAssignment, DailyReport, User, MonthlyReportSubmission
from app.schemas.report import DailyReportSortField, SortOrder, MonthlyReportSortField


class ReportRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, project_id: int, task_id: int, text: str) -> DailyReport:
        report = DailyReport(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            text=text,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def filter_reports(self, params):
        stmt = self.db.query(DailyReport)

        if params.search:
            stmt = stmt.filter(
                DailyReport.text.ilike(f"%{params.search}%")
            )

        if params.ids:
            stmt = stmt.filter(DailyReport.id.in_(params.ids))

        if params.user_id:
            stmt = stmt.filter(
                DailyReport.user_id == params.user_id
            )

        if params.project_ids:
            stmt = stmt.filter(
                DailyReport.project_id.in_(params.project_ids)
            )

        if params.task_id:
            stmt = stmt.filter(
                DailyReport.task_id == params.task_id
            )

        if params.report_date:
            stmt = stmt.filter(
                DailyReport.report_date == params.report_date
            )

        if params.report_date_from:
            stmt = stmt.filter(
                DailyReport.report_date >= params.report_date_from
            )

        if params.report_date_to:
            stmt = stmt.filter(
                DailyReport.report_date <= params.report_date_to
            )

        if params.created_from:
            stmt = stmt.filter(
                DailyReport.created_at >= params.created_from
            )

        if params.created_to:
            stmt = stmt.filter(
                DailyReport.created_at <= params.created_to
            )

        SORT_FIELDS = {
            DailyReportSortField.id: DailyReport.id,
            DailyReportSortField.report_date: DailyReport.report_date,
            DailyReportSortField.created_at: DailyReport.created_at,
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

    def create_submission(self, **data):
        obj = MonthlyReportSubmission(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_submission(self, obj, data: dict):
        for k, v in data.items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_report_by_user(self, user_id: int) -> list[DailyReport]:
        return self.db.query(DailyReport).filter(DailyReport.user_id == user_id).all()

    def exists(self, user_id, project_id, report_date):
        return (
            self.db.query(DailyReport.id)
            .filter(
                DailyReport.user_id == user_id,
                DailyReport.project_id == project_id,
                DailyReport.report_date == report_date,
            )
            .first()
            is not None
        )

    def get_all(self):
        return self.db.query(DailyReport).all()

    def get_by_projects(self, project_ids: list[int]):
        return (
            self.db.query(DailyReport)
            .filter(DailyReport.project_id.in_(project_ids))
            .order_by(DailyReport.report_date.desc())
            .all()
        )

    def get_by_id(self, id: int):
        return self.db.query(DailyReport).filter(DailyReport.id == id).first()

    def update(self, report, data: dict):
        for key, value in data.items():
            setattr(report, key, value)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_reports_by_project_and_date_range(self, project_id: int, start_date, end_date):
        return (
            self.db.query(DailyReport)
            .filter(
                DailyReport.project_id == project_id,
                DailyReport.report_date >= start_date,
                DailyReport.report_date < end_date,
            )
            .order_by(DailyReport.report_date.asc())
            .all()
        )

    def get_by_user_project_range(self, user_id: int, project_id: int, start, end):
        return (
            self.db.query(DailyReport)
            .filter(
                DailyReport.user_id == user_id,
                DailyReport.project_id == project_id,
                DailyReport.report_date >= start,
                DailyReport.report_date < end,
            )
            .all()
        )

    def create_monthly_submission(self, user_id: int, project_id: int, year: int, month: int, total_reports: int):
        submission = MonthlyReportSubmission(
            user_id=user_id,
            project_id=project_id,
            year=year,
            month=month,
            total_reports=total_reports,
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission
    


    def get_submission(self, user_id: int, project_id: int, year: int, month: int):
        return (
            self.db.query(MonthlyReportSubmission)
            .filter(
                MonthlyReportSubmission.user_id == user_id,
                MonthlyReportSubmission.project_id == project_id,
                MonthlyReportSubmission.year == year,
                MonthlyReportSubmission.month == month,
            )
            .first()
        )

    def get_all_monthly_reports(self):
        return (
            self.db.query(MonthlyReportSubmission)
            .order_by(MonthlyReportSubmission.submitted_at.desc())
            .all()
        )

    def get_monthly_report_by_projects(self, project_ids):
        if not project_ids:
            return []
        return (
            self.db.query(MonthlyReportSubmission)
            .filter(MonthlyReportSubmission.project_id.in_(project_ids))
            .order_by(
                MonthlyReportSubmission.year.desc(),
                MonthlyReportSubmission.month.desc(),
            )
            .all()
        )

    # Alias — eski nom bilan chaqirilsa ham ishlaydi
    def get_by_projects_monthly(self, project_ids):
        return self.get_monthly_report_by_projects(project_ids)

    def get_monthly_reports_by_user(self, user_id):
        return (
            self.db.query(MonthlyReportSubmission)
            .filter(MonthlyReportSubmission.user_id == user_id)
            .order_by(
                MonthlyReportSubmission.year.desc(),
                MonthlyReportSubmission.month.desc(),
            )
            .all()
        )

    def get_monthly_report_by_id(self, monthly_report_id: int) -> MonthlyReportSubmission:
        return (
            self.db.query(MonthlyReportSubmission)
            .filter(MonthlyReportSubmission.id == monthly_report_id)
            .first()
        )
    
    def filter_monthly_reports(self, params):
        stmt = self.db.query(MonthlyReportSubmission)

        if params.ids:
            stmt = stmt.filter(
                MonthlyReportSubmission.id.in_(params.ids)
            )

        if params.user_id:
            stmt = stmt.filter(
                MonthlyReportSubmission.user_id == params.user_id
            )

        if params.project_ids:
            stmt = stmt.filter(
                MonthlyReportSubmission.project_id.in_(params.project_ids)
            )

        if params.status:
            stmt = stmt.filter(
                MonthlyReportSubmission.status.in_(params.status)
            )

        if params.year:
            stmt = stmt.filter(
                MonthlyReportSubmission.year == params.year
            )


        if params.month:
            stmt = stmt.filter(
                MonthlyReportSubmission.month == params.month
            )

        if params.submitted_from:
            stmt = stmt.filter(
                MonthlyReportSubmission.submitted_at >= params.submitted_from
            )

        if params.submitted_to:
            stmt = stmt.filter(
                MonthlyReportSubmission.submitted_at <= params.submitted_to
            )

        SORT_FIELDS = {
            MonthlyReportSortField.id: MonthlyReportSubmission.id,
            MonthlyReportSortField.year: MonthlyReportSubmission.year,
            MonthlyReportSortField.month: MonthlyReportSubmission.month,
            MonthlyReportSortField.total_reports: MonthlyReportSubmission.total_reports,
            MonthlyReportSortField.status: MonthlyReportSubmission.status,
            MonthlyReportSortField.submitted_at: MonthlyReportSubmission.submitted_at,
            MonthlyReportSortField.updated_at: MonthlyReportSubmission.updated_at,
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