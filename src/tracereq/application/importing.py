"""Пакетный импорт: все требования и записи истории фиксируются вместе."""

from pydantic import ValidationError

from tracereq.application.commands import CreateRequirement
from tracereq.application.ports import RequirementParser, UnitOfWork
from tracereq.domain.entities import Requirement
from tracereq.domain.errors import InvalidInput, NotFound


class ImportService:
    def __init__(self, uow: UnitOfWork, parser: RequirementParser) -> None:
        self._uow = uow
        self._parser = parser

    def import_docx(self, project_id: int, content: bytes) -> list[Requirement]:
        if self._uow.projects.get(project_id) is None:
            raise NotFound('Project not found')
        if not content:
            raise InvalidInput('Файл пустой')
        drafts = self._parser.parse(content)
        try:
            commands = [
                CreateRequirement(
                    title=draft.title,
                    description=draft.description,
                    requirement_type=draft.requirement_type,
                )
                for draft in drafts
            ]
        except ValidationError as exc:
            raise InvalidInput('Документ содержит некорректные требования') from exc
        created = []
        for command in commands:
            requirement = self._uow.requirements.add(project_id, command.model_dump())
            self._uow.history.add(requirement.id, 'CREATE', None, requirement.snapshot(), None)
            created.append(requirement)
        self._uow.commit()
        return created
