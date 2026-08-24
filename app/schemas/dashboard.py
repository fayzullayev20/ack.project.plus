from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class AlertItem(BaseModel):
    type: str
    severity: str
    message: str
    count: int


class RecentReportItem(BaseModel):
    report_id:       int
    worker_id:       int
    worker_username: str | None
    project_name:    str
    report_date:     date
    has_attachments: bool
    text_preview:    str | None


class RoleCountItem(BaseModel):
    role: str
    count: int


class DashboardAdminResponse(BaseModel):
    total_users:           int
    active_users:          int
    total_projects:        int
    active_projects:       int
    total_tasks:           int
    completed_tasks:       int
    pending_help_requests: int
    unread_notifications:  int
    project_breakdown:     dict
    task_breakdown:        dict
    reports:               dict
    alerts:                list[AlertItem]
    recent_reports:        list[RecentReportItem]


class DashboardManagerResponse(BaseModel):
    total_projects:        int
    active_projects:       int
    total_workers:         int
    total_tasks:           int
    completed_tasks:       int
    pending_help_requests: int
    unread_notifications:  int
    project_breakdown:     dict
    task_breakdown:        dict
    reports:               dict
    alerts:                list[AlertItem]
    recent_reports:        list[RecentReportItem]


class DashboardWorkerResponse(BaseModel):
    total_assigned_tasks:  int
    active_tasks:          int
    completed_tasks:       int
    blocked_tasks:         int
    overdue_tasks:         int
    pending_help_requests: int
    unread_notifications:  int
    task_breakdown:        dict
    reports:               dict
    alerts:                list[AlertItem]
    recent_reports:        list[RecentReportItem]


class WorkloadItemResponse(BaseModel):
    user_id:         int
    username:        str | None
    assigned_tasks:  int
    active_tasks:    int
    completed_tasks: int
    blocked_tasks:   int
    overdue_tasks:   int


class DeadlineItemResponse(BaseModel):
    entity_type: str
    entity_id:   int
    title:       str | None
    deadline:    datetime | None
    status:      str | None
    is_overdue:  bool


class ReportAnalyticsResponse(BaseModel):
    total_daily_reports: int
    reports_today:       int
    reports_this_month:  int
    unique_reporters:    int


class ProjectProgressItemResponse(BaseModel):
    project_id:      int
    project_name:    str
    total_tasks:     int
    completed_tasks: int
    progress:        float