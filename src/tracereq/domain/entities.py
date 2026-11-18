"""Независимые от ORM снимки сущностей и результаты операций."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from tracereq.domain.enums import LinkType, Priority, RequirementStatus, RequirementType


@dataclass(frozen=True, slots=True)
class Project:
    id: int
    name: str
    description: str
    created_at: datetime | None


@dataclass(frozen=True, slots=True)
class Requirement:
    id: int
    project_id: int
    title: str
    description: str
    requirement_type: RequirementType
    status: RequirementStatus
    priority: Priority
    source: str
    author: str
    created_at: datetime | None
    updated_at: datetime | None

    def snapshot(self) -> dict[str, Any]:
        """Совместимый с существующим JSON-журналом снимок требования."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'requirement_type': self.requirement_type.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'source': self.source,
            'author': self.author,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass(frozen=True, slots=True)
class Link:
    id: int
    source_requirement_id: int
    target_requirement_id: int
    link_type: LinkType


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    id: int
    requirement_id: int
    changed_by: str | None
    changed_at: datetime | None
    change_type: str | None
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class RequirementDraft:
    title: str
    requirement_type: RequirementType
    description: str = ''


@dataclass(frozen=True, slots=True)
class RequirementDetails:
    requirement: Requirement
    outgoing_links: list[Link]
    incoming_links: list[Link]


@dataclass(frozen=True, slots=True)
class TraceabilityReport:
    requirements: list[Requirement]
    links: list[Link]

    def matrix(self) -> dict[int, dict[int, str]]:
        result: dict[int, dict[int, str]] = {}
        for link in self.links:
            result.setdefault(link.source_requirement_id, {})[link.target_requirement_id] = (
                link.link_type.value
            )
        return result
