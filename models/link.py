"""Модель связи между требованиями"""
from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import db


class LinkType(str, Enum):
    """Типы связей между требованиями"""
    IMPLEMENTS = "Реализует"
    DEPENDS_ON = "Зависит от"
    CONTRADICTS = "Противоречит"


class Link(db.Model):
    """Модель связи между требованиями"""
    __tablename__ = 'links'
    
    id = Column(Integer, primary_key=True)
    source_requirement_id = Column(Integer, ForeignKey('requirements.id'), nullable=False)
    target_requirement_id = Column(Integer, ForeignKey('requirements.id'), nullable=False)
    link_type = Column(SQLEnum(LinkType), nullable=False)
    
    source_requirement = relationship(
        'Requirement',
        foreign_keys=[source_requirement_id],
        back_populates='outgoing_links'
    )
    target_requirement = relationship(
        'Requirement',
        foreign_keys=[target_requirement_id],
        back_populates='incoming_links'
    )
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'source_requirement_id': self.source_requirement_id,
            'target_requirement_id': self.target_requirement_id,
            'link_type': self.link_type.value,
        }
    
    def __repr__(self):
        return f'<Link {self.source_requirement_id} -> {self.target_requirement_id} ({self.link_type.value})>'
