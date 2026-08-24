from typing import Annotated, List

from fastapi import APIRouter, status, Depends, Body, UploadFile, File, Form, Path
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.models import user
from app.schemas.files import UploadResponse, FileResponseSchema, SignedUrlResponse
from app.core.deps import get_db, get_user
from app.services.file_service import FileService
from app.models.user import User


router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=UploadResponse)
def upload_file(
    report_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_user),
):
    service = FileService(db)
    return service.upload_files(file, user, report_id)


@router.get("/{id}")
def get_file(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = FileService(db)
    file = service.get_file(id, user)

    return FileResponse(
        path=file.path,
        filename=file.original_name,
        media_type=file.content_type,
        content_disposition_type="inline"
    )


@router.delete("/{id}")
def delete_file_view(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = FileService(db)
    return service.delete_file(id, user)


@router.get("/{id}/download")
def download_file_view(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = FileService(db)
    file = service.get_file(id, user)

    return FileResponse(
        path=file.path,
        filename=file.original_name,
        media_type=file.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file.original_name}"'
        },
    )


@router.get("/{id}/signed-url", response_model=SignedUrlResponse)
def get_signed_url(
    id: Annotated[int, Path()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_user)],
):
    service = FileService(db)
    return service.generate_signed_url(id, user)
