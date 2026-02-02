import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from database import db

class Project(db.Model):
    __tablename__ = 'projects'
    id = Column(db.Integer, primary_key=True)
    name = Column(String(200),nullable=False,unique=True)
    description = Column(String(1000),nullable=False, default='')
    created_at = Column(DateTime, default=datetime.UTC)

    requirements = relationship(
        'Requirement',
        back_populates = "project",
        cascade="all, delete, delete-orphan"
    )

    def to_dict(self):
        return {
            'id':self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
        }
