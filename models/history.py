from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import db


class RequirementHistory(db.Model):
    """Модель истории изменений требования"""
    __tablename__ = 'requirement_history'
    
    id = Column(Integer, primary_key=True)
    requirement_id = Column(Integer, ForeignKey('requirements.id'), nullable=False)
    changed_by = Column(String(200))
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_type = Column(String(50))  # CREATE, UPDATE, DELETE
    old_values = Column(JSON)  # Старые значения полей
    new_values = Column(JSON)  # Новые значения полей
    
    requirement = relationship('Requirement', back_populates='history')
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'change_type': self.change_type,
            'old_values': self.old_values,
            'new_values': self.new_values,
        }
    
    def __repr__(self):
        return f'<RequirementHistory {self.id}: {self.change_type} at {self.changed_at}>'
