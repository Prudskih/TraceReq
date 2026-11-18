from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from tracereq.domain.entities import Project
from tracereq.domain.errors import NotFound
from tracereq.infrastructure.persistence.mapping import project_entity
from tracereq.infrastructure.persistence.models import ProjectRow


class SqlAlchemyProjectRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, project_id: int) -> Project | None:
        row = self._session.get(ProjectRow, project_id)
        return project_entity(row) if row is not None else None

    def list(self) -> list[Project]:
        rows = self._session.scalars(select(ProjectRow).order_by(ProjectRow.id))
        return [project_entity(row) for row in rows]

    def add(self, name: str, description: str) -> Project:
        row = ProjectRow(name=name, description=description)
        self._session.add(row)
        self._session.flush()
        return project_entity(row)

    def update(self, project_id: int, fields: dict[str, Any]) -> Project:
        row = self._session.get(ProjectRow, project_id)
        if row is None:
            raise NotFound('Project not found')
        for name, value in fields.items():
            setattr(row, name, value)
        self._session.flush()
        return project_entity(row)

    def delete(self, project_id: int) -> None:
        self._session.execute(delete(ProjectRow).where(ProjectRow.id == project_id))
