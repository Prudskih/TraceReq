"""Требования и их история изменяются в одной транзакции."""

import logging

from tracereq.application.commands import CreateRequirement, UpdateRequirement
from tracereq.application.ports import UnitOfWork
from tracereq.domain.entities import HistoryEntry, Link, Requirement, RequirementDetails
from tracereq.domain.errors import NotFound

logger = logging.getLogger(__name__)


class RequirementService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def get(self, project_id: int, requirement_id: int) -> Requirement:
        requirement = self._uow.requirements.get(project_id, requirement_id)
        if requirement is None:
            raise NotFound('Requirement not found')
        return requirement

    def list_with_links(self, project_id: int) -> list[RequirementDetails]:
        if self._uow.projects.get(project_id) is None:
            raise NotFound('Project not found')
        requirements = self._uow.requirements.list(project_id)
        outgoing: dict[int, list[Link]] = {}
        incoming: dict[int, list[Link]] = {}
        for link in self._uow.links.list_for_project(project_id):
            outgoing.setdefault(link.source_requirement_id, []).append(link)
            incoming.setdefault(link.target_requirement_id, []).append(link)
        return [
            RequirementDetails(item, outgoing.get(item.id, []), incoming.get(item.id, []))
            for item in requirements
        ]

    def details(self, project_id: int, requirement_id: int) -> RequirementDetails:
        requirement = self.get(project_id, requirement_id)
        links = self._uow.links.list_for_project(project_id)
        return RequirementDetails(
            requirement,
            [link for link in links if link.source_requirement_id == requirement_id],
            [link for link in links if link.target_requirement_id == requirement_id],
        )

    def create(self, project_id: int, command: CreateRequirement) -> Requirement:
        if self._uow.projects.get(project_id) is None:
            raise NotFound('Project not found')
        requirement = self._uow.requirements.add(project_id, command.model_dump())
        self._uow.history.add(
            requirement.id,
            'CREATE',
            None,
            requirement.snapshot(),
            command.author or None,
        )
        self._uow.commit()
        return requirement

    def update(
        self,
        project_id: int,
        requirement_id: int,
        command: UpdateRequirement,
    ) -> Requirement:
        previous = self.get(project_id, requirement_id)
        fields = command.model_dump(exclude_unset=True, exclude={'changed_by'})
        requirement = self._uow.requirements.update(project_id, requirement_id, fields)
        self._uow.history.add(
            requirement_id,
            'UPDATE',
            previous.snapshot(),
            requirement.snapshot(),
            command.changed_by,
        )
        self._uow.commit()
        return requirement

    def delete(self, project_id: int, requirement_id: int, deleted_by: str | None) -> None:
        self.get(project_id, requirement_id)
        self._uow.links.delete_for_requirements([requirement_id])
        self._uow.history.delete_for_requirements([requirement_id])
        self._uow.requirements.delete(requirement_id)
        # Existing schema requires a live parent for every history record.
        # A durable deletion audit needs a separate schema decision.
        self._uow.commit()
        logger.info('Deleted requirement %s; actor=%r', requirement_id, deleted_by)

    def history(self, project_id: int, requirement_id: int) -> list[HistoryEntry]:
        self.get(project_id, requirement_id)
        return self._uow.history.list(requirement_id)
