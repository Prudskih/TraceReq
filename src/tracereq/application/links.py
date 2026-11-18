"""Правила создания связей между требованиями одного проекта."""

from tracereq.application.commands import CreateLink
from tracereq.application.ports import UnitOfWork
from tracereq.domain.entities import Link
from tracereq.domain.errors import InvalidInput, NotFound


class LinkService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def create(self, project_id: int, command: CreateLink) -> Link:
        if self._uow.projects.get(project_id) is None:
            raise NotFound('Project not found')
        if command.source_id == command.target_id:
            raise InvalidInput('A requirement cannot link to itself')
        for requirement_id in (command.source_id, command.target_id):
            if self._uow.requirements.get(project_id, requirement_id) is None:
                raise InvalidInput('Both requirements must belong to this project')
        link = self._uow.links.add(command.source_id, command.target_id, command.link_type)
        self._uow.commit()
        return link

    def delete(self, link_id: int) -> None:
        if self._uow.links.get(link_id) is None:
            raise NotFound('Link not found')
        self._uow.links.delete(link_id)
        self._uow.commit()
