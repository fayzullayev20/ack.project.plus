from datetime import date, datetime, timedelta, timezone
from collections import defaultdict
from fastapi import HTTPException, status

from app.repository.report_repo import ReportRepo
from app.repository.task_repo import TaskRepo
from app.repository.project_repo import ProjectRepo
from app.models import User, UserRole, MonthlyReportStatus
from app.schemas.report import CreateDailyReport
from app.services.notification_service import NotificationService


class ReportService:
    def __init__(self, db):
        self.db = db
        self.repo = ReportRepo(db)
        self.task_repo = TaskRepo(db)
        self.project_repo = ProjectRepo(db)
        self.notification_service = NotificationService(db)

    @staticmethod
    def _get_month_range(year: int, month: int) -> tuple[date, date]:
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")

        start_date = date(year, month, 1)

        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        return start_date, end_date

    def create_daily_report(self, user: User, data: CreateDailyReport):
        task = self.task_repo.get_by_id(data.task_id)

        if not task or task.project_id != data.project_id:
            raise HTTPException(400, "Invalid task for this project")

        if not self.project_repo.is_project_member(data.project_id, user.id):
            raise HTTPException(403, "You are not assigned to this project")

        if not self.task_repo.get_assignment(data.task_id, user.id):
            raise HTTPException(403, "You are not assigned to this task")

        if self.repo.exists(user.id, data.project_id, data.report_date):
            raise HTTPException(400, "Report already exists for this day")

        report = self.repo.create(
            user_id=user.id,
            project_id=data.project_id,
            task_id=data.task_id,
            text=data.text,
        )

        # Manager ga notification — worker kunlik hisobot topshirdi
        if task.project and task.project.manager_id:
            self.notification_service.create_notification(
                user_id=task.project.manager_id,
                title="New Daily Report",
                message=f"{user.username} submitted a report for task: '{task.title}'",
            )

        return report

    def update_report(self, report_id: int, data, user):
        report = self.repo.get_by_id(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        if report.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only report owner can update",
            )

        # FIX 1: timezone-aware datetime ishlatish
        now = datetime.now(timezone.utc)
        report_created = report.created_at
        if report_created.tzinfo is None:
            report_created = report_created.replace(tzinfo=timezone.utc)

        if report_created < now - timedelta(hours=24):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report can only be edited within 24 hours",
            )

        update_data = {}

        if data.text is not None:
            update_data["text"] = data.text

        return self.repo.update(report, update_data)

    def get_reports(self, user, params):
        if user.role == UserRole.ADMIN:
            pass

        elif user.role == UserRole.MANAGER:
            project_ids = self.project_repo.get_manager_project_ids(user.id)

            if not project_ids:
                return []

            params.project_ids = project_ids

        elif user.role == UserRole.WORKER:
            params.user_id = user.id

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return self.repo.filter_reports(params)

    def get_report(self, report_id: int, user):
        report = self.repo.get_by_id(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        if user.role == UserRole.ADMIN:
            return report

        # FIX 2: Manager projects.manager_id orqali tekshiriladi
        if user.role == UserRole.MANAGER:
            project = self.project_repo.get_project_by_id(report.project_id)
            if not project or project.manager_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            return report

        if user.role == UserRole.WORKER:
            if report.user_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            return report

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    def generate_monthly_report(self, user, year: int, month: int, project_id: int):
        if user.role == UserRole.ADMIN:
            pass

        elif user.role == UserRole.MANAGER:
            project = self.project_repo.get_project_by_id(project_id)
            if not project or project.manager_id != user.id:
                raise HTTPException(403, "Access denied")

        elif user.role == UserRole.WORKER:
            if not self.project_repo.is_project_member(project_id, user.id):
                raise HTTPException(403, "Access denied")

        else:
            raise HTTPException(403, "Access denied")

        start_date, end_date = self._get_month_range(year, month)

        reports = self.repo.get_reports_by_project_and_date_range(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )

        if user.role == UserRole.WORKER:
            reports = [r for r in reports if r.user_id == user.id]

        return {
            "user_id": user.id,
            "project_id": project_id,
            "year": year,
            "month": month,
            "total_reports": len(reports),
            "reports": [
                {
                    "report_id": r.id,
                    "report_date": r.report_date,
                    "text": r.text,
                }
                for r in reports
            ],
        }

    def submit_monthly_report(self, user, year: int, month: int, project_id: int):
        if not self.project_repo.is_member(project_id, user.id):
            raise HTTPException(403, "Access denied")

        start_date, end_date = self._get_month_range(year, month)

        reports = self.repo.get_reports_by_project_and_date_range(
            project_id,
            start_date,
            end_date,
        )

        reports = [r for r in reports if r.user_id == user.id]

        if not reports:
            raise HTTPException(400, "No reports to submit")

        existing = self.repo.get_submission(user.id, project_id, year, month)

        # FIX 3: updated_at qo'shildi — NOT NULL constraint
        now = datetime.now(timezone.utc)

        data = {
            "user_id": user.id,
            "project_id": project_id,
            "year": year,
            "month": month,
            "total_reports": len(reports),
            "status": MonthlyReportStatus.SUBMITTED,
            "updated_at": now,
        }

        if existing:
            submission = self.repo.update_submission(existing, data)
        else:
            submission = self.repo.create_submission(**data)

        submission.reports = reports

        self.db.commit()
        self.db.refresh(submission)

        # Manager ga notification — worker oylik hisobot topshirdi
        project = self.project_repo.get_project_by_id(project_id)
        if project and project.manager_id:
            self.notification_service.create_notification(
                user_id=project.manager_id,
                title="Monthly Report Submitted",
                message=f"{user.username} submitted monthly report for {year}/{month:02d}",
            )

        return submission

    def get_monthly_reports(self, user, params):
        if user.role == UserRole.ADMIN:
            pass

        elif user.role == UserRole.MANAGER:
            project_ids = self.project_repo.get_user_project_ids(user.id)

            if not project_ids:
                return []

            params.project_ids = project_ids

        elif user.role == UserRole.WORKER:
            params.user_id = user.id

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        submissions = self.repo.filter_monthly_reports(params)

        return self._attach_reports(submissions)

    def get_monthly_report_by_id(self, submission_id: int, user: User):
        monthly_report = self.repo.get_monthly_report_by_id(submission_id)

        if not monthly_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Monthly report not found",
            )

        if user.role == UserRole.ADMIN:
            return self._attach_reports([monthly_report])[0]

        if user.role == UserRole.MANAGER:
            project = self.project_repo.get_project_by_id(monthly_report.project_id)
            if not project or project.manager_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            return self._attach_reports([monthly_report])[0]

        if user.role == UserRole.WORKER:
            if monthly_report.user_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            return self._attach_reports([monthly_report])[0]

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    def _attach_reports(self, submissions):
        reports = self.repo.get_reports_for_submissions(submissions)

        grouped = defaultdict(list)

        for report in reports:
            key = (
                report.user_id,
                report.project_id,
                report.report_date.year,
                report.report_date.month,
            )

            grouped[key].append(report)

        for submission in submissions:
            key = (
                submission.user_id,
                submission.project_id,
                submission.year,
                submission.month,
            )

            submission.reports = grouped.get(key, [])

        return submissions