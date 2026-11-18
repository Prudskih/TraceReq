"""Сценарии управления проектами."""

from tracereq.application.commands import CreateProject, UpdateProject
from tracereq.application.ports import UnitOfWork
from tracereq.domain.entities import Project
from tracereq.domain.errors import NotFound


class ProjectService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def get(self, project_id: int) -> Project:
        project = self._uow.projects.get(project_id)
        if project is None:
            raise NotFound('Project not found')
        return project

    def list(self) -> list[Project]:
        return self._uow.projects.list()

    def create(self, command: CreateProject) -> Project:
        project = self._uow.projects.add(command.name, command.description.strip())
        self._uow.commit()
        return project

    def update(self, project_id: int, command: UpdateProject) -> Project:
        self.get(project_id)
        fields = command.model_dump(exclude_unset=True)
        if 'description' in fields:
            fields['description'] = fields['description'].strip()
        project = self._uow.projects.update(project_id, fields)
        self._uow.commit()
        return project

    def delete(self, project_id: int) -> None:
        self.get(project_id)
        ids = [item.id for item in self._uow.requirements.list(project_id)]
        self._uow.links.delete_for_requirements(ids)
        self._uow.history.delete_for_requirements(ids)
        self._uow.requirements.delete_for_project(project_id)
        self._uow.projects.delete(project_id)
        self._uow.commit()
