from typing import List, Optional
from sqlalchemy.orm import Session
from models.requirement import Requirement, RequirementType


class RequirementRepository:
    """Репозиторий для работы с требованиями"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create(self, requirement_data: dict) -> Requirement:
        """Создание нового требования"""
        requirement = Requirement(**requirement_data)
        self.db.add(requirement)
        self.db.commit()
        self.db.refresh(requirement)
        return requirement
    
    def get_by_id(self, requirement_id: int) -> Optional[Requirement]:
        """Получение требования по ID"""
        return self.db.query(Requirement).filter(Requirement.id == requirement_id).first()
    
    def get_all(self) -> List[Requirement]:
        """Получение всех требований"""
        return self.db.query(Requirement).order_by(Requirement.created_at.desc()).all()
    
    def update(self, requirement_id: int, requirement_data: dict) -> Optional[Requirement]:
        """Обновление требования"""
        requirement = self.get_by_id(requirement_id)
        if requirement:
            for key, value in requirement_data.items():
                setattr(requirement, key, value)
            self.db.commit()
            self.db.refresh(requirement)
        return requirement
    
    def delete(self, requirement_id: int) -> bool:
        """Удаление требования"""
        requirement = self.get_by_id(requirement_id)
        if requirement:
            self.db.delete(requirement)
            self.db.commit()
            return True
        return False
    
    def get_by_type(self, requirement_type: RequirementType) -> List[Requirement]:
        """Получение требований по типу"""
        return self.db.query(Requirement).filter(
            Requirement.requirement_type == requirement_type
        ).all()
