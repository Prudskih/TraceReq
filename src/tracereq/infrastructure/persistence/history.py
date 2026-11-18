from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from tracereq.domain.entities import HistoryEntry
from tracereq.infrastructure.persistence.mapping import history_entity
from tracereq.infrastructure.persistence.models import HistoryRow


class SqlAlchemyHistoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(self, requirement_id: int) -> list[HistoryEntry]:
        rows = self._session.scalars(
            select(HistoryRow)
            .where(
                HistoryRow.requirement_id == requirement_id,
            )
            .order_by(HistoryRow.changed_at.desc(), HistoryRow.id.desc())
        )
        return [history_entity(row) for row in rows]

    def add(
        self,
        requirement_id: int,
        change_type: str,
        old_values: dict[str, Any] | None,
        new_values: dict[str, Any] | None,
        changed_by: str | None,
    ) -> None:
        self._session.add(
            HistoryRow(
                requirement_id=requirement_id,
                change_type=change_type,
                old_values=old_values,
                new_values=new_values,
                changed_by=changed_by,
            )
        )

    def delete_for_requirements(self, requirement_ids: Sequence[int]) -> None:
        if requirement_ids:
            self._session.execute(
                delete(HistoryRow).where(
                    HistoryRow.requirement_id.in_(requirement_ids),
                )
            )
