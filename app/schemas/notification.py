from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    title: str | None
    message: str | None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    count: int


class MessageResponse(BaseModel):
    message: str


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str