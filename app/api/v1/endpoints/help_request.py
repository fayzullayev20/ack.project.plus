from typing import Annotated, List

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_user
from app.services.help_request_service import HelpRequestService
from app.schemas.help_request import HelpRequestCreate, HelpRequestResponse, HelpRequestQueryParams
from app.models.user import User


router = APIRouter(prefix="/help-requests", tags=["Help Requests"])


@router.post("/", response_model=HelpRequestResponse)
def create_help_request(
    data: HelpRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    return HelpRequestService(db).create(data.task_id, current_user)


@router.get("/", response_model=List[HelpRequestResponse])
def get_help_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
    params: Annotated[HelpRequestQueryParams, Depends()]
):
    return HelpRequestService(db).get_all(current_user, params)


@router.get("/{request_id}", response_model=HelpRequestResponse)
def get_help_request(
    request_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    return HelpRequestService(db).get_by_id(request_id, current_user)


@router.patch("/{request_id}/assign")
def assign_help_request(
    request_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    HelpRequestService(db).assign(request_id, current_user)
    return {"message": "Help request accepted"}


@router.patch("/{request_id}/resolve")
def resolve_help_request(
    request_id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_user)],
):
    HelpRequestService(db).resolve(request_id, current_user)
    return {"message": "Help request resolved"}
