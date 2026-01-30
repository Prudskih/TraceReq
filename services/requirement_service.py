"""Сервис для работы с требованиями"""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from repositories.requirement_repository import RequirementRepository
from repositories.link_repository import LinkRepository
from models.requirement import Requirement, RequirementType, RequirementStatus, Priority
from models.link import LinkType, Link
from models.history import RequirementHistory


class RequirementService:
    """Сервис для работы с требованиями"""
    
    def __init__(self, db_session: Session):
        self.requirement_repo = RequirementRepository(db_session)
        self.link_repo = LinkRepository(db_session)
        self.db = db_session
    
    def create_requirement(self, requirement_data: dict, author: str = None) -> Requirement:
        """Создание требования с сохранением истории"""
        if author:
            requirement_data['author'] = author
        
        requirement = self.requirement_repo.create(requirement_data)
        
        # Сохранение истории создания
        self._save_history(
            requirement.id,
            'CREATE',
            None,
            requirement.to_dict(),
            author
        )
        
        return requirement
    
    def update_requirement(
        self,
        requirement_id: int,
        requirement_data: dict,
        changed_by: str = None
    ) -> Optional[Requirement]:
        """Обновление требования с сохранением истории"""
        old_requirement = self.requirement_repo.get_by_id(requirement_id)
        if not old_requirement:
            return None
        
        old_values = old_requirement.to_dict()
        
        requirement = self.requirement_repo.update(requirement_id, requirement_data)
        if requirement:
            new_values = requirement.to_dict()
            
            # Сохранение истории изменения
            self._save_history(
                requirement_id,
                'UPDATE',
                old_values,
                new_values,
                changed_by
            )
        
        return requirement
    
    def delete_requirement(self, requirement_id: int, deleted_by: str = None) -> bool:
        """Удаление требования с сохранением истории"""
        requirement = self.requirement_repo.get_by_id(requirement_id)
        if not requirement:
            return False
        
        old_values = requirement.to_dict()
        
        # Удаление всех связей
        self.link_repo.delete_by_requirement(requirement_id)
        
        # Удаление требования
        result = self.requirement_repo.delete(requirement_id)
        
        if result:
            # Сохранение истории удаления
            self._save_history(
                requirement_id,
                'DELETE',
                old_values,
                None,
                deleted_by
            )
        
        return result
    
    def get_requirement(self, requirement_id: int) -> Optional[Requirement]:
        """Получение требования"""
        return self.requirement_repo.get_by_id(requirement_id)
    
    def get_all_requirements(self) -> List[Requirement]:
        """Получение всех требований"""
        return self.requirement_repo.get_all()
    
    def create_link(
        self,
        source_id: int,
        target_id: int,
        link_type: LinkType,
        created_by: str = None
    ) -> Optional[Link]:
        """Создание связи между требованиями"""
        # Проверка существования требований
        source = self.requirement_repo.get_by_id(source_id)
        target = self.requirement_repo.get_by_id(target_id)
        
        if not source or not target:
            return None
        
        # Проверка на самосвязь
        if source_id == target_id:
            return None
        
        return self.link_repo.create(source_id, target_id, link_type)
    
    def get_requirement_with_links(self, requirement_id: int) -> Optional[Dict]:
        """Получение требования со всеми связями"""
        requirement = self.requirement_repo.get_by_id(requirement_id)
        if not requirement:
            return None
        
        result = requirement.to_dict()
        
        # Получение связей
        outgoing_links = self.link_repo.get_by_source(requirement_id)
        incoming_links = self.link_repo.get_by_target(requirement_id)
        
        result['outgoing_links'] = [link.to_dict() for link in outgoing_links]
        result['incoming_links'] = [link.to_dict() for link in incoming_links]
        
        return result
    
    def get_requirement_history(self, requirement_id: int) -> List[RequirementHistory]:
        """Получение истории изменений требования"""
        return self.db.query(RequirementHistory).filter(
            RequirementHistory.requirement_id == requirement_id
        ).order_by(RequirementHistory.changed_at.desc()).all()
    
    def _save_history(
        self,
        requirement_id: int,
        change_type: str,
        old_values: Optional[Dict],
        new_values: Optional[Dict],
        changed_by: Optional[str]
    ):
        """Сохранение истории изменения"""
        history = RequirementHistory(
            requirement_id=requirement_id,
            change_type=change_type,
            old_values=old_values,
            new_values=new_values,
            changed_by=changed_by,
            changed_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()
