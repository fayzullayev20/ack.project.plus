import os
import time
import uuid
import hmac
import hashlib

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.repository.file_repo import FileRepo
from app.models import User, File
from app.core.config import settings
from app.models.user import UserRole
from app.repository.report_repo import ReportRepo


class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.file_repo = FileRepo(db)
        self.report_repo = ReportRepo(db)

    def upload_files(
        self,
        file: UploadFile,
        user: User,
        report_id: int,
    ):
        if user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.WORKER]:
            raise HTTPException(status_code=403, detail="Not allowed")
        
        if not self.report_repo.get_by_id(report_id):
            raise HTTPException(status_code=404, detail="Report not found")

        db_file = self.file_repo.save_file(file, user)

        attachment = self.file_repo.make_attachment(
            report_id=report_id,
            file_id=db_file.id
        )

        return {
            "file_id": db_file.id,
            "attachment_id": attachment.id,
            "original_name": db_file.original_name,
            "stored_name": db_file.stored_name,
            "file_type": db_file.file_type,
            "size": db_file.size,
        }

    def get_file(self, file_id: int, user: User) -> File:
        if user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.WORKER]:
            raise HTTPException(status_code=403, detail="Not allowed")

        file = self.file_repo.get_file_by_id(file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        if not file.path or not os.path.exists(file.path):
            raise HTTPException(status_code=404, detail="File missing on disk")

        return file

    def delete_file(self, file_id, user):
        file = self.file_repo.get_file_by_id(file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        if file.uploaded_by != user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

        if file.path and os.path.exists(file.path):
            os.remove(file.path)

        self.file_repo.delete_file(file)

        return {"message": "deleted", "file_id": file_id}

    def generate_signed_url(self, file_id: int, user: User):
        file = self.file_repo.get_file_by_id(file_id)

        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        if user.role == "worker" and file.uploaded_by != user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

        expires_in = settings.EXPIRE_MINUTES
        expires_at = int(time.time()) + expires_in

        payload = f"{file_id}:{expires_at}"

        signature = hmac.new(
            settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        url = f"/files/{file_id}/download-signed?exp={expires_at}&sig={signature}"

        return {
            "url": url,
            "expires_in": expires_in,
        }
