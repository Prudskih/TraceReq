from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from tracereq.domain.entities import Requirement
from tracereq.domain.errors import NotFound
from tracereq.infrastructure.persistence.mapping import requirement_entity
from tracereq.infrastructure.persistence.models import RequirementRow


class SqlAlchemyRequirementRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, project_id: int, requirement_id: int) -> Requirement | None:
        row = self._session.scalar(
            select(RequirementRow).where(
                RequirementRow.id == requirement_id,
                RequirementRow.project_id == project_id,
            )
        )
        return requirement_entity(row) if row is not None else None

    def list(self, project_id: int) -> list[Requirement]:
        rows = self._session.scalars(
            select(RequirementRow)
            .where(
                RequirementRow.project_id == project_id,
            )
            .order_by(RequirementRow.id)
        )
        return [requirement_entity(row) for row in rows]

    def add(self, project_id: int, fields: dict[str, Any]) -> Requirement:
        row = RequirementRow(project_id=project_id, **fields)
        self._session.add(row)
        self._session.flush()
        return requirement_entity(row)

    def update(self, project_id: int, requirement_id: int, fields: dict[str, Any]) -> Requirement:
        row = self._session.scalar(
            select(RequirementRow).where(
                RequirementRow.id == requirement_id,
                RequirementRow.project_id == project_id,
            )
        )
        if row is None:
            raise NotFound('Requirement not found')
        for name, value in fields.items():
            setattr(row, name, value)
        self._session.flush()
        return requirement_entity(row)

    def delete(self, requirement_id: int) -> None:
        self._session.execute(delete(RequirementRow).where(RequirementRow.id == requirement_id))

    def delete_for_project(self, project_id: int) -> None:
        self._session.execute(delete(RequirementRow).where(RequirementRow.project_id == project_id))
