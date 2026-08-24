from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from math import ceil

from app.models import User, UserProfile, RefreshToken
from app.models.skills import Skill
from app.schemas.user import CreateUser, UpdateUserData, UserSortField, UserQueryParams
from app.schemas.user_profile import UpdateProfile


class UserRepo:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, data: CreateUser) -> User:
        user = User(
            username=data.username,
            email=data.email,
               role=data.role,
            password_hash=data.password,
        )

        skills = []

        if data.skill_ids:
            skills = self.db.query(Skill).filter(Skill.id.in_(data.skill_ids)).all()

        user.skills = skills

        self.db.add(user)
        self.db.flush()

        profile = UserProfile(user_id=user.id)
        self.db.add(profile)

        self.db.commit()
        self.db.refresh(user)

        return user

    def update_user(self, id: int, data: UpdateUserData) -> User:
        user = self.get_user_by_id(id)

        skills = []
        if data.skill_ids is not None:
            skills = self.db.query(Skill).filter(Skill.id.in_(data.skill_ids)).all()

        if data.username:
            user.username = data.username
        if data.email:
            user.email = data.email
        if data.role:
            user.role = data.role
        if data.password:
            user.password_hash = data.password

        user.skills = skills

        self.db.commit()

        return user

    def update_profile(self, data: UpdateProfile, user: User):
        profile = (
            self.db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        )

        if not profile:
            profile = UserProfile(user_id=user.id)
            self.db.add(profile)

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(profile, field, value)

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def activate_user(self, user: User):
        user.is_active = True

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def deactivate_user(self, user: User):
        print(user.is_active)
        user.is_active = False
        print(user.is_active)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_all_users(
        self,
        params: UserQueryParams,
    ) -> list[User]:
        
        query = self.db.query(User)

        if params.skill_ids:
            query = query.join(User.skills).filter(Skill.id.in_(params.skill_ids))

        if params.is_active is not None:
            query = query.filter(User.is_active == params.is_active)

        if params.role:
            query = query.filter(User.role == params.role)

        if params.search:
            search_term = f"%{params.search}%"

            query = query.filter(
                (User.username.ilike(search_term)) |
                (User.email.ilike(search_term))
            )

        sortable_fields = {
            UserSortField.created_at: User.created_at,
            UserSortField.username: User.username,
            UserSortField.email: User.email,
        }

        sort_column = sortable_fields.get(params.sort_by, User.created_at)

        if params.order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
            
        offset = (params.page - 1) * params.limit

        query = query.offset(offset).limit(params.limit)
        
        users = query.all()
        total = query.count()

        return {
            "items": users,
            "total": total,
            "page": params.page,
            "limit": params.limit,
            "total_pages": ceil(total / params.limit),
        }


    def get_user_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, id: int):
        return self.db.query(User).filter(User.id == id).first()

    def create_refresh_token(self, user: User, refresh_token: str, jti: str):
        token = RefreshToken(user_id=user.id, token=refresh_token, jti=jti)

        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)

        return token

    def get_refresh_token_by_jti(self, jti: str):
        return self.db.query(RefreshToken).filter(RefreshToken.jti == jti).first()

    def revoke_refresh_token(self, token: RefreshToken):
        token.is_revoked = True
        self.db.add(token)
        self.db.commit()

    def update_password(self, user: User, new_hash: str):
        user.password_hash = new_hash
        user.is_first_login = False

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_user_by_email(self, email: str) -> User:
        return self.db.query(User).filter(User.email == email).first()
