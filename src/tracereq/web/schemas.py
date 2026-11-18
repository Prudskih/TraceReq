"""Явные выходные контракты HTTP API."""

from datetime import UTC, datetime
from email.utils import format_datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer

from tracereq.domain.entities import RequirementDetails
from tracereq.domain.enums import LinkType, Priority, RequirementStatus, RequirementType


class OutputModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectOutput(OutputModel):
    id: int
    name: str
    description: str
    created_at: datetime | None

    @field_serializer('created_at')
    def serialize_date(self, value: datetime | None) -> str | None:
        return format_datetime(value.replace(tzinfo=UTC), usegmt=True) if value else None


class RequirementOutput(OutputModel):
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


class LinkOutput(OutputModel):
    id: int
    source_requirement_id: int
    target_requirement_id: int
    link_type: LinkType


class RequirementDetailsOutput(RequirementOutput):
    outgoing_links: list[LinkOutput]
    incoming_links: list[LinkOutput]

    @classmethod
    def from_details(cls, details: RequirementDetails) -> 'RequirementDetailsOutput':
        return cls(
            **RequirementOutput.model_validate(details.requirement).model_dump(),
            outgoing_links=[LinkOutput.model_validate(link) for link in details.outgoing_links],
            incoming_links=[LinkOutput.model_validate(link) for link in details.incoming_links],
        )


class HistoryOutput(OutputModel):
    id: int
    requirement_id: int
    changed_by: str | None
    changed_at: datetime | None
    change_type: str | None
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None


class ImportOutput(BaseModel):
    created_count: int
    requirements: list[RequirementOutput]


class MatrixOutput(BaseModel):
    requirements: list[RequirementOutput]
    matrix: dict[int, dict[int, str]]


class MessageOutput(BaseModel):
    message: str


class ErrorOutput(BaseModel):
    error: str
