from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import hash_password
from app.core.deps import get_db


def seed_users(db: Session):
    users_to_create = [
        {
            "email": "admin@example.com",
            "username": "admin",
            "password": "admin123",
            "role": UserRole.ADMIN,
        },
        {
            "email": "manager@example.com",
            "username": "manager",
            "password": "manager123",
            "role": UserRole.MANAGER,
        },
        {
            "email": "worker@example.com",
            "username": "worker",
            "password": "worker123",
            "role": UserRole.WORKER,
        },
    ]

    for user_data in users_to_create:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()

        if existing_user:
            continue

        user = User(
            email=user_data["email"],
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            role=user_data["role"],
            is_active=True,
            is_first_login=True,
        )

        db.add(user)

    db.commit()


seed_users(next(get_db()))



