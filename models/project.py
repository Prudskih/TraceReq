import datetime
from email.utils import format_datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from database import Base

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String(200),nullable=False,unique=True)
    description = Column(String(1000),nullable=False, default='')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
            'created_at': format_datetime(self.created_at.replace(tzinfo=datetime.timezone.utc), usegmt=True) if self.created_at else None,
        }
