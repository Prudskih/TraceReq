"""Репозиторий для работы со связями между требованиями"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models.link import Link, LinkType


class LinkRepository:
    """Репозиторий для работы со связями"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create(self, source_id: int, target_id: int, link_type: LinkType) -> Link:
        """Создание связи между требованиями"""
        link = Link(
            source_requirement_id=source_id,
            target_requirement_id=target_id,
            link_type=link_type
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link
    
    def get_by_id(self, link_id: int) -> Optional[Link]:
        """Получение связи по ID"""
        return self.db.query(Link).filter(Link.id == link_id).first()
    
    def get_all(self) -> List[Link]:
        """Получение всех связей"""
        return self.db.query(Link).all()
    
    def get_by_source(self, source_id: int) -> List[Link]:
        """Получение всех исходящих связей требования"""
        return self.db.query(Link).filter(Link.source_requirement_id == source_id).all()
    
    def get_by_target(self, target_id: int) -> List[Link]:
        """Получение всех входящих связей требования"""
        return self.db.query(Link).filter(Link.target_requirement_id == target_id).all()
    
    def get_by_requirement(self, requirement_id: int) -> List[Link]:
        """Получение всех связей требования (входящих и исходящих)"""
        return self.db.query(Link).filter(
            (Link.source_requirement_id == requirement_id) |
            (Link.target_requirement_id == requirement_id)
        ).all()
    
    def delete(self, link_id: int) -> bool:
        """Удаление связи"""
        link = self.get_by_id(link_id)
        if link:
            self.db.delete(link)
            self.db.commit()
            return True
        return False
    
    def delete_by_requirement(self, requirement_id: int) -> int:
        """Удаление всех связей требования"""
        deleted = self.db.query(Link).filter(
            (Link.source_requirement_id == requirement_id) |
            (Link.target_requirement_id == requirement_id)
        ).delete()
        self.db.commit()
        return deleted
