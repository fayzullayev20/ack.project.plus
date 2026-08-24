from typing import Annotated

from fastapi import APIRouter, Depends, Body, UploadFile, File, Path
from sqlalchemy.orm import Session

from app.schemas.report import (
    CreateDailyReport,
    ReportResponse,
    ReportDetailResponse,
    UpdateReportRequest,
    MonthlyReportItem,
    MonthlyReportResponse,
    MonthlyReportSubmitResponse,
    DailyReportQueryParams,
    MonthlyReportQueryParams,
)
from app.core.deps import get_db, get_worker, get_user
from app.models import User
from app.services.report_service import ReportService


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/daily", response_model=ReportResponse, status_code=201)
def create_daily_report_view(
    data: Annotated[CreateDailyReport, Body()],
    db: Annotated[Session, Depends(get_db)],
    worker: Annotated[User, Depends(get_worker)],
):
    service = ReportService(db)

    return service.create_daily_report(
        user=worker,
        data=data,
    )


@router.get(
    "/daily",
    response_model=list[ReportResponse],
)
def get_reports_view(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
    params: Annotated[DailyReportQueryParams, Depends()],
):
    service = ReportService(db)
    return service.get_reports(user=user, params=params)


@router.get("/daily/{id}", response_model=ReportDetailResponse)
def get_report_view(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = ReportService(db)
    return service.get_report(id, user)


@router.patch(
    "/daily/{id}",
    response_model=ReportResponse,
)
def update_report_view(
    id: Annotated[int, Path()],
    data: Annotated[UpdateReportRequest, Body()],
    db: Annotated[Session, Depends(get_db)],
    worker: Annotated[User, Depends(get_worker)],
):
    service = ReportService(db)
    return service.update_report(report_id=id, data=data, user=worker)


@router.post(
    "/monthly/generate",
    response_model=MonthlyReportResponse,
)
def monthly_report_view(
    year: Annotated[int, Body()],
    month: Annotated[int, Body()],
    project_id: Annotated[int, Body()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = ReportService(db)

    return service.generate_monthly_report(
        user=user,
        year=year,
        month=month,
        project_id=project_id,
    )


@router.post(
    "/monthly/submit",
    response_model=MonthlyReportSubmitResponse,
)
def submit_monthly_report_view(
    year: Annotated[int, Body()],
    month: Annotated[int, Body()],
    project_id: Annotated[int, Body()],
    db: Annotated[Session, Depends(get_db)],
    worker: Annotated[User, Depends(get_worker)],
):
    service = ReportService(db)

    return service.submit_monthly_report(
        user=worker,
        year=year,
        month=month,
        project_id=project_id,
    )


@router.get("/monthly", response_model=list[MonthlyReportSubmitResponse])
def get_monthly_reports_view(
    db: Annotated[Session, Depends(get_db)], 
    user: Annotated[User, Depends(get_user)],
    params: Annotated[MonthlyReportQueryParams, Depends()]
):
    service = ReportService(db)

    return service.get_monthly_reports(user=user, params=params)


@router.get("/monthly/{id}", response_model=MonthlyReportSubmitResponse)
def get_monthly_report_view(
    id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = ReportService(db)

    return service.get_monthly_report_by_id(submission_id=id, user=user)
