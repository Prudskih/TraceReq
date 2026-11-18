"""Типизированные входные данные сценариев; не зависят от FastAPI."""

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from tracereq.domain.enums import LinkType, Priority, RequirementStatus, RequirementType

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Actor = Annotated[str, StringConstraints(max_length=200)]


class Command(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class CreateProject(Command):
    name: Name
    description: str = Field(default='', max_length=1000)


class UpdateProject(Command):
    name: Name | None = None
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode='after')
    def reject_explicit_null(self) -> Self:
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f'{field} cannot be null')
        return self


class CreateRequirement(Command):
    title: Title
    requirement_type: RequirementType
    description: str = ''
    status: RequirementStatus = RequirementStatus.DRAFT
    priority: Priority = Priority.MEDIUM
    source: str = Field(default='', max_length=500)
    author: Actor = ''


class UpdateRequirement(Command):
    title: Title | None = None
    description: str | None = None
    requirement_type: RequirementType | None = None
    status: RequirementStatus | None = None
    priority: Priority | None = None
    source: str | None = Field(default=None, max_length=500)
    author: Actor | None = None
    changed_by: Actor | None = None

    @model_validator(mode='after')
    def reject_explicit_null(self) -> Self:
        for field in self.model_fields_set - {'changed_by'}:
            if getattr(self, field) is None:
                raise ValueError(f'{field} cannot be null')
        return self


class DeleteRequirement(Command):
    deleted_by: Actor | None = None


class CreateLink(Command):
    source_id: int = Field(gt=0)
    target_id: int = Field(gt=0)
    link_type: LinkType
