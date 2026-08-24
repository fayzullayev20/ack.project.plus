from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.skills import Skill
from app.models.user import User, UserRole
from app.repository.skills_repo import SkillRepository as SkillRepo



class SkillService:
    def __init__(self, db: Session):
        self.db = db
        self.skill_repo = SkillRepo(db)

    def create_skill(self, name: str, admin: User) -> Skill:
        existing_skill = self.skill_repo.get_by_name(name)
        if existing_skill:
            raise HTTPException(status_code=400, detail="Skill with this name already exists")

        return self.skill_repo.create_skill(name)
    
    def list_skills(self) -> list[Skill]:
        return self.skill_repo.get_all_skills()
    
    def get_skill_by_id(self, id: int) -> Skill:
        skill = self.skill_repo.get_by_id(id)
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        return skill
    
    def update_skill(self, id: int, name: str, admin: User) -> Skill:
        skill = self.skill_repo.get_by_id(id)
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        existing_skill = self.skill_repo.get_by_name(name)
        if existing_skill and existing_skill.id != id:
            raise HTTPException(status_code=400, detail="Another skill with this name already exists")

        return self.skill_repo.update_skill(id, name)
    
    def delete_skill(self, id: int, admin: User):
        skill = self.skill_repo.get_by_id(id)
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        self.skill_repo.delete_skill(id)

    
    def get_my_skills(self, user: User) -> list[Skill]:
        return user.skills