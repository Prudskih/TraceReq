"""ORM-отображение существующих таблиц. Создание/миграция схемы здесь отсутствует."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from tracereq.domain.enums import LinkType, Priority, RequirementStatus, RequirementType


def utc_now() -> datetime:
    # Existing columns store naive UTC timestamps.
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default='')
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class RequirementRow(Base):
    __tablename__ = 'requirements'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    requirement_type: Mapped[RequirementType] = mapped_column(Enum(RequirementType), nullable=False)
    status: Mapped[RequirementStatus | None] = mapped_column(
        Enum(RequirementStatus),
        default=RequirementStatus.DRAFT,
    )
    priority: Mapped[Priority | None] = mapped_column(Enum(Priority), default=Priority.MEDIUM)
    source: Mapped[str | None] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class LinkRow(Base):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_requirement_id: Mapped[int] = mapped_column(
        ForeignKey('requirements.id'), nullable=False
    )
    target_requirement_id: Mapped[int] = mapped_column(
        ForeignKey('requirements.id'), nullable=False
    )
    link_type: Mapped[LinkType] = mapped_column(Enum(LinkType), nullable=False)


class HistoryRow(Base):
    __tablename__ = 'requirement_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey('requirements.id'), nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(200))
    changed_at: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)
    change_type: Mapped[str | None] = mapped_column(String(50))
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSON)
