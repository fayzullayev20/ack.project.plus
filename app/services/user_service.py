import uuid

from fastapi import HTTPException, status, UploadFile
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.repository.user_repo import UserRepo
from app.repository.project_repo import ProjectRepo
from app.repository.task_repo import TaskRepo
from app.repository.report_repo import ReportRepo
from app.repository.file_repo import FileRepo
from app.repository.skills_repo import SkillRepository
from app.schemas.auth import UserLoginResponse, ChangePasswordRequest
from app.schemas.user import CreateUser, UpdateUserData
from app.schemas.user_profile import UpdateProfile
from app.core.security import (
    generate_token,
    generate_refresh_token,
    verify_refresh_token,
    verify_password,
    hash_password,
)
from app.models import User
from app.models.user import UserRole

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_SIZE = 2 * 1024 * 1024  # 2MB


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepo(db)
        self.project_repo = ProjectRepo(db)
        self.task_repo = TaskRepo(db)
        self.report_repo = ReportRepo(db)
        self.file_repo = FileRepo(db)
        self.skill_repo = SkillRepository(db)

    def create_user(self, data: CreateUser) -> User:
        user = self.user_repo.get_user_by_username(data.username)

        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="username already exist"
            )
        user = self.user_repo.get_user_by_email(data.email)

        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="email already exist"
            )
        
        if data.skill_ids:
            for skill_id in data.skill_ids:
                skill = self.skill_repo.get_by_id(skill_id)
                if not skill:
                    raise HTTPException(status_code=400, detail=f"Skill with id {skill_id} not found")

        data.password = hash_password(data.password)

        return self.user_repo.create_user(data)

    def update_user(self, id: int, data: UpdateUserData, user: User) -> User:
        if user.id != id and user.role == "worker":
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Method not allowed",
            )

        if data.username:
            if self.user_repo.get_user_by_username(data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="username already exist",
                )
        if data.email:
            if self.user_repo.get_user_by_email(data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="email already exist",
                )
        if data.password:
            data.password = hash_password(data.password)

        if data.skill_ids is not None:
            for skill_id in data.skill_ids:
                skill = self.skill_repo.get_by_id(skill_id)
                if not skill:
                    raise HTTPException(status_code=400, detail=f"Skill with id {skill_id} not found")

        return self.user_repo.update_user(id, data)

    def update_avatar(self, user: User, file: UploadFile):
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(400, "Invalid file type")

        content = file.file.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(400, "File too large")

        file.file.seek(0)

        file_obj = self.file_repo.save_file(file, user)

        data = UpdateProfile(avatar_file_id=file_obj.id)

        return self.user_repo.update_profile(data=data, user=user)

    def reset_password(self, id: int, data: ChangePasswordRequest):
        user = self.get_user_by_id(id)

        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Old password incorrect")

        if verify_password(data.new_password, user.password_hash):
            raise HTTPException(
                status_code=400, detail="New password must be different"
            )

        new_hash = hash_password(data.new_password)

        self.user_repo.update_password(user, new_hash)

    def activate_user(self, id: int):
        user = self.get_user_by_id(id)

        return self.user_repo.activate_user(user)

    def deactivate_user(self, id: int):
        user = self.get_user_by_id(id)

        return self.user_repo.deactivate_user(user)

    def authenticate_user(self, credentials: HTTPBasicCredentials):
        user = self.user_repo.get_user_by_username(credentials.username)

        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        access_token = generate_token({"sub": str(user.id)})

        refresh_jti = str(uuid.uuid4())
        refresh_token_str = generate_refresh_token(
            {"sub": str(user.id), "jti": refresh_jti}
        )

        self.user_repo.create_refresh_token(
            user=user, refresh_token=refresh_token_str, jti=refresh_jti
        )

        return UserLoginResponse(
            access_token=access_token, refresh_token=refresh_token_str
        )

    def refresh_access_token(self, refresh_token: str) -> UserLoginResponse:
        payload = verify_refresh_token(refresh_token)

        user_id = int(payload["sub"])
        jti = payload["jti"]

        user = self.user_repo.get_user_by_id(user_id)
        db_token = self.user_repo.get_refresh_token_by_jti(jti)

        if not user or not db_token or db_token.is_revoked:
            raise HTTPException(401, "Invalid token")

        new_access = generate_token({"sub": str(user.id)})

        return UserLoginResponse(access_token=new_access, refresh_token=refresh_token)

    def logout(self, refresh_token: str):
        payload = verify_refresh_token(refresh_token)

        jti = payload.get("jti")

        db_token = self.user_repo.get_refresh_token_by_jti(jti)

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        self.user_repo.revoke_refresh_token(db_token)

    def change_password_current_user(
        self, user: User, old_password: str, new_password: str
    ):
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Old password incorrect")

        if verify_password(new_password, user.password_hash):
            raise HTTPException(
                status_code=400, detail="New password must be different"
            )

        new_hash = hash_password(new_password)

        self.user_repo.update_password(user, new_hash)

    def get_user_by_id(self, id: int) -> User:
        user = self.user_repo.get_user_by_id(id)

        if not user:
            raise HTTPException(status_code=404, detail="user not found")

        return user

    def get_user_projects(self, id: int):
        user = self.get_user_by_id(id)

        if user.role == UserRole.ADMIN:
            return self.project_repo.get_all_projects()

        elif user.role == UserRole.MANAGER:
            return self.project_repo.get_projects_by_manager(user.id)

        elif user.role == UserRole.WORKER:
            return self.project_repo.get_projects_by_user(user.id)

    def get_user_tasks(self, id: int):
        user = self.get_user_by_id(id)

        return self.task_repo.get_tasks_by_user(user.id)

    def get_user_reports(self, id: int):
        user = self.get_user_by_id(id)

        return self.report_repo.get_report_by_user(user.id)
