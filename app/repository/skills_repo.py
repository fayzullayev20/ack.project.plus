from sqlalchemy.orm import Session

from app.models.skills import Skill


class SkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_skill(self, name: str) -> Skill:
        skill = Skill(name=name)
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill
    
    def get_by_name(self, name: str) -> Skill | None:
        return self.db.query(Skill).filter(Skill.name == name).first()
    
    def get_all_skills(self) -> list[Skill]:
        return self.db.query(Skill).all()
    
    def get_by_id(self, id: int) -> Skill | None:
        return self.db.query(Skill).filter(Skill.id == id).first()
    
    def update_skill(self, id: int, name: str) -> Skill:
        skill = self.get_by_id(id)
        
        skill.name = name
        self.db.commit()
        self.db.refresh(skill)
        return skill
    
    def delete_skill(self, id: int):
        skill = self.get_by_id(id)
        self.db.delete(skill)
        self.db.commit()