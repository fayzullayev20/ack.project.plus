from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repository.analytics_repo import AnalyticsRepo
from app.models.user import User, UserRole
from app.models.task import Task
from app.models.project import Project
from app.models.help_request import HelpRequestStatus


class AnalyticsService:
    def __init__(self, db: Session):
        self.repo = AnalyticsRepo(db)

    def get_admin_dashboard(self, current_user: User):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(403, "Only admin can access admin dashboard")

        total_users, active_users       = self.repo.count_users()
        total_projects, active_projects = self.repo.count_projects()
        total_tasks, completed_tasks    = self.repo.count_tasks()
        pending_help_requests           = self.repo.count_pending_help_requests()
        unread_notifications            = self.repo.count_unread_notifications(current_user.id)

        active_workers   = self.repo.count_active_workers()
        workers_reported = self.repo.count_workers_reported_today()

        recent_reports = [
            {
                "report_id":       r.id,
                "worker_id":       r.user_id,
                "worker_username": r.user.username if r.user else None,
                "project_name":    r.project.name if r.project else "",
                "report_date":     r.report_date,
                "has_attachments": len(r.attachments) > 0,
                "text_preview":    r.text[:100] if r.text else None,
            }
            for r in self.repo.get_recent_reports(limit=8)
        ]

        return {
            "total_users":           total_users,
            "active_users":          active_users,
            "total_projects":        total_projects,
            "active_projects":       active_projects,
            "total_tasks":           total_tasks,
            "completed_tasks":       completed_tasks,
            "pending_help_requests": pending_help_requests,
            "unread_notifications":  unread_notifications,
            "project_breakdown": self.repo.get_project_status_breakdown(),
            "task_breakdown":    self.repo.get_task_status_breakdown(),
            "reports": {
                "today":                self.repo.count_reports_today(),
                "this_month":           self.repo.count_reports_this_month(),
                "workers_reported":     workers_reported,
                "workers_not_reported": active_workers - workers_reported,
            },
            "alerts":         self._build_alerts(active_workers, workers_reported),
            "recent_reports": recent_reports,
        }

    def _build_alerts(self, active_workers: int, workers_reported: int) -> list:
        alerts = []

        overdue = self.repo.count_overdue_tasks()
        if overdue:
            alerts.append({
                "type":     "overdue_task",
                "severity": "high",
                "message":  f"{overdue} ta task muddati o'tib ketdi",
                "count":    overdue,
            })

        blocked = self.repo.count_blocked_tasks()
        if blocked:
            alerts.append({
                "type":     "blocked_task",
                "severity": "medium",
                "message":  f"{blocked} ta task bloklangan",
                "count":    blocked,
            })

        no_report = active_workers - workers_reported
        if no_report > 0:
            alerts.append({
                "type":     "no_report",
                "severity": "medium",
                "message":  f"{no_report} ta worker bugun hisobot topshirmadi",
                "count":    no_report,
            })

        soon = self.repo.count_deadline_soon_projects(days=7)
        if soon:
            alerts.append({
                "type":     "deadline_soon",
                "severity": "low",
                "message":  f"{soon} ta loyiha 7 kun ichida tugaydi",
                "count":    soon,
            })

        return alerts

    def get_manager_dashboard(self, current_user: User):
        if current_user.role != UserRole.MANAGER:
            raise HTTPException(403, "Only manager can access manager dashboard")

        manager_id = current_user.id

        # Mavjud
        total_projects   = len(self.repo.get_manager_projects(manager_id))
        active_projects  = sum(
            1 for p in self.repo.get_manager_projects(manager_id)
            if p.status == "active"
        )
        total_workers         = self.repo.count_manager_workers(manager_id)
        total_tasks           = self.repo.count_manager_tasks(manager_id)
        completed_tasks       = self.repo.count_manager_completed_tasks(manager_id)
        pending_help_requests = self.repo.count_pending_help_requests()
        unread_notifications  = self.repo.count_unread_notifications(manager_id)

        # Yangi
        active_workers   = self.repo.count_manager_workers(manager_id)
        workers_reported = self.repo.count_manager_workers_reported_today(manager_id)

        recent_reports = [
            {
                "report_id":       r.id,
                "worker_id":       r.user_id,
                "worker_username": r.user.username if r.user else None,
                "project_name":    r.project.name if r.project else "",
                "report_date":     r.report_date,
                "has_attachments": len(r.attachments) > 0,
                "text_preview":    r.text[:100] if r.text else None,
            }
            for r in self.repo.get_manager_recent_reports(manager_id, limit=8)
        ]

        return {
            # Mavjud
            "total_projects":        total_projects,
            "active_projects":       active_projects,
            "total_workers":         total_workers,
            "total_tasks":           total_tasks,
            "completed_tasks":       completed_tasks,
            "pending_help_requests": pending_help_requests,
            "unread_notifications":  unread_notifications,

            # Yangi
            "project_breakdown": self.repo.get_manager_project_status_breakdown(manager_id),
            "task_breakdown":    self.repo.get_manager_task_status_breakdown(manager_id),
            "reports": {
                "today":                self.repo.count_reports_today(),
                "this_month":           self.repo.count_reports_this_month(),
                "workers_reported":     workers_reported,
                "workers_not_reported": active_workers - workers_reported,
            },
            "alerts":         self._build_manager_alerts(manager_id, active_workers, workers_reported),
            "recent_reports": recent_reports,
        }

    def _build_manager_alerts(self, manager_id: int, active_workers: int, workers_reported: int) -> list:
        alerts = []

        overdue = self.repo.count_manager_overdue_tasks(manager_id)
        if overdue:
            alerts.append({
                "type":     "overdue_task",
                "severity": "high",
                "message":  f"{overdue} ta task muddati o'tib ketdi",
                "count":    overdue,
            })

        blocked = self.repo.count_manager_blocked_tasks(manager_id)
        if blocked:
            alerts.append({
                "type":     "blocked_task",
                "severity": "medium",
                "message":  f"{blocked} ta task bloklangan",
                "count":    blocked,
            })

        no_report = active_workers - workers_reported
        if no_report > 0:
            alerts.append({
                "type":     "no_report",
                "severity": "medium",
                "message":  f"{no_report} ta worker bugun hisobot topshirmadi",
                "count":    no_report,
            })

        soon = self.repo.count_manager_deadline_soon_projects(manager_id, days=7)
        if soon:
            alerts.append({
                "type":     "deadline_soon",
                "severity": "low",
                "message":  f"{soon} ta loyiha 7 kun ichida tugaydi",
                "count":    soon,
            })

        return alerts

    def get_worker_dashboard(self, current_user: User):
        if current_user.role != UserRole.WORKER:
            raise HTTPException(403, "Only worker can access worker dashboard")

        user_id = current_user.id

        total_assigned_tasks  = self.repo.count_tasks_for_user(user_id)
        active_tasks          = self.repo.count_active_tasks_for_user(user_id)
        completed_tasks       = self.repo.count_completed_tasks_for_user(user_id)
        blocked_tasks         = self.repo.count_blocked_tasks_for_user(user_id)
        overdue_tasks         = self.repo.count_overdue_tasks_for_user(user_id)
        unread_notifications  = self.repo.count_unread_notifications(user_id)
        pending_help_requests = self.repo.count_worker_pending_help_requests(user_id)

        reported_today = self.repo.worker_reported_today(user_id)

        recent_reports = [
            {
                "report_id":       r.id,
                "worker_id":       r.user_id,
                "worker_username": current_user.username,
                "project_name":    r.project.name if r.project else "",
                "report_date":     r.report_date,
                "has_attachments": len(r.attachments) > 0,
                "text_preview":    r.text[:100] if r.text else None,
            }
            for r in self.repo.get_worker_recent_reports(user_id, limit=8)
        ]

        return {
            "total_assigned_tasks":  total_assigned_tasks,
            "active_tasks":          active_tasks,
            "completed_tasks":       completed_tasks,
            "blocked_tasks":         blocked_tasks,
            "overdue_tasks":         overdue_tasks,
            "pending_help_requests": pending_help_requests,
            "unread_notifications":  unread_notifications,

            "task_breakdown": self.repo.get_worker_task_status_breakdown(user_id),
            "reports": {
                "reported_today": reported_today,
                "this_month":     self.repo.count_reports_this_month(),
            },
            "alerts":         self._build_worker_alerts(user_id, overdue_tasks, blocked_tasks),
            "recent_reports": recent_reports,
        }

    def _build_worker_alerts(self, user_id: int, overdue_tasks: int, blocked_tasks: int) -> list:
        alerts = []

        if overdue_tasks:
            alerts.append({
                "type":     "overdue_task",
                "severity": "high",
                "message":  f"{overdue_tasks} ta taskingiz muddati o'tib ketdi",
                "count":    overdue_tasks,
            })

        if blocked_tasks:
            alerts.append({
                "type":     "blocked_task",
                "severity": "medium",
                "message":  f"{blocked_tasks} ta taskingiz bloklangan",
                "count":    blocked_tasks,
            })

        if not self.repo.worker_reported_today(user_id):
            alerts.append({
                "type":     "no_report",
                "severity": "medium",
                "message":  "Bugun hisobot topshirilmadi",
                "count":    1,
            })

        return alerts

    def get_workload(self, current_user: User):
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(403, "Access denied")

        rows = self.repo.get_workload_rows()
        result = []
        for row in rows:
            result.append(
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "assigned_tasks": int(row.assigned_tasks or 0),
                    "active_tasks": int(row.active_tasks or 0),
                    "completed_tasks": int(row.completed_tasks or 0),
                    "blocked_tasks": int(row.blocked_tasks or 0),
                    "overdue_tasks": int(row.overdue_tasks or 0),
                }
            )
        return result

    def get_deadlines(self, current_user: User):
        if current_user.role == UserRole.ADMIN:
            rows = self.repo.get_deadline_rows()
        elif current_user.role == UserRole.MANAGER:
            rows = self.repo.get_deadline_rows()
        elif current_user.role == UserRole.WORKER:
            rows = self.repo.get_deadline_rows(user_id=current_user.id)
        else:
            raise HTTPException(403, "Access denied")

        now = datetime.utcnow()
        result = []
        for row in rows:
            result.append(
                {
                    "entity_type": "task",
                    "entity_id": row.entity_id,
                    "title": row.title,
                    "deadline": row.deadline,
                    "status": row.status.value
                    if hasattr(row.status, "value")
                    else str(row.status),
                    "is_overdue": row.deadline < now if row.deadline else False,
                }
            )
        return result

    def get_reports(self, current_user: User):
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(403, "Access denied")

        return {
            "total_daily_reports": self.repo.count_reports_total(),
            "reports_today": self.repo.count_reports_today(),
            "reports_this_month": self.repo.count_reports_this_month(),
            "unique_reporters": self.repo.count_unique_reporters(),
        }

    def get_project_progress(self, current_user: User):
        if current_user.role == UserRole.ADMIN:
            rows = self.repo.get_project_progress_rows()
        elif current_user.role == UserRole.MANAGER:
            rows = self.repo.get_project_progress_rows(manager_id=current_user.id)
        else:
            raise HTTPException(403, "Access denied")

        result = []
        for row in rows:
            total = int(row.total_tasks or 0)
            completed = int(row.completed_tasks or 0)
            progress = 0.0
            if total > 0:
                progress = (completed / total) * 100

            result.append(
                {
                    "project_id": row.project_id,
                    "project_name": row.project_name,
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "progress": round(progress, 2),
                }
            )
        return result
