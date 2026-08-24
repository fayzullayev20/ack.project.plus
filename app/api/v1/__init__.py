from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as user_router
from app.api.v1.endpoints.profile import router as profile_router
from app.api.v1.endpoints.project import router as project_router
from app.api.v1.endpoints.task import router as task_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.files import router as files_router
from app.api.v1.endpoints.notification import router as notification_router
from app.api.v1.endpoints.help_request import router as help_request_router
from app.api.v1.endpoints.analytics import dashboard_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.audit_logs import router as audit_logs_router
from app.api.v1.endpoints.skills import router as skills_router

router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(profile_router)
router.include_router(project_router)
router.include_router(task_router)
router.include_router(reports_router)
router.include_router(files_router)
router.include_router(notification_router)
router.include_router(help_request_router)
router.include_router(dashboard_router)
router.include_router(analytics_router)
router.include_router(audit_logs_router)
router.include_router(skills_router)