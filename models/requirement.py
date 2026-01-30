"""Модель требования"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import db


class RequirementType(str, Enum):
    """Типы требований"""
    BUSINESS = "Бизнес-требование"
    FUNCTIONAL = "Функциональное требование"
    NON_FUNCTIONAL = "Нефункциональное требование"
    USER = "Пользовательское требование"
    INTERFACE = "Требование к интерфейсу"


class RequirementStatus(str, Enum):
    """Статусы требований"""
    DRAFT = "Черновик"
    IN_PROGRESS = "В работе"
    REVIEW = "На проверке"
    APPROVED = "Утверждено"
    REJECTED = "Отклонено"


class Priority(str, Enum):
    """Приоритеты требований"""
    LOW = "Низкий"
    MEDIUM = "Средний"
    HIGH = "Высокий"
    CRITICAL = "Критический"


class Requirement(db.Model):
    """Модель требования"""
    __tablename__ = 'requirements'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    requirement_type = Column(SQLEnum(RequirementType), nullable=False)
    status = Column(SQLEnum(RequirementStatus), default=RequirementStatus.DRAFT)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    source = Column(String(500))
    author = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    outgoing_links = relationship(
        'Link',
        foreign_keys='Link.source_requirement_id',
        back_populates='source_requirement',
        cascade='all, delete-orphan'
    )
    incoming_links = relationship(
        'Link',
        foreign_keys='Link.target_requirement_id',
        back_populates='target_requirement',
        cascade='all, delete-orphan'
    )
    history = relationship(
        'RequirementHistory',
        back_populates='requirement',
        cascade='all, delete-orphan',
        order_by='RequirementHistory.changed_at.desc()'
    )
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'requirement_type': self.requirement_type.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'source': self.source or '',
            'author': self.author or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<Requirement {self.id}: {self.title}>'
