"""ORM-объекты не выходят за границу слоя хранения."""

from tracereq.domain.entities import HistoryEntry, Link, Project, Requirement
from tracereq.domain.enums import Priority, RequirementStatus
from tracereq.infrastructure.persistence.models import (
    HistoryRow,
    LinkRow,
    ProjectRow,
    RequirementRow,
)


def project_entity(row: ProjectRow) -> Project:
    return Project(row.id, row.name, row.description, row.created_at)


def requirement_entity(row: RequirementRow) -> Requirement:
    return Requirement(
        id=row.id,
        project_id=row.project_id,
        title=row.title,
        description=row.description or '',
        requirement_type=row.requirement_type,
        status=row.status or RequirementStatus.DRAFT,
        priority=row.priority or Priority.MEDIUM,
        source=row.source or '',
        author=row.author or '',
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def link_entity(row: LinkRow) -> Link:
    return Link(row.id, row.source_requirement_id, row.target_requirement_id, row.link_type)


def history_entity(row: HistoryRow) -> HistoryEntry:
    return HistoryEntry(
        row.id,
        row.requirement_id,
        row.changed_by,
        row.changed_at,
        row.change_type,
        row.old_values,
        row.new_values,
    )
