from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)

class SkillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)


class SkillResponse(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }