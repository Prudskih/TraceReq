from collections.abc import Sequence

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from tracereq.domain.entities import Link
from tracereq.domain.enums import LinkType
from tracereq.infrastructure.persistence.mapping import link_entity
from tracereq.infrastructure.persistence.models import LinkRow, RequirementRow


class SqlAlchemyLinkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, link_id: int) -> Link | None:
        row = self._session.get(LinkRow, link_id)
        return link_entity(row) if row is not None else None

    def list_for_project(self, project_id: int) -> list[Link]:
        ids = select(RequirementRow.id).where(RequirementRow.project_id == project_id)
        rows = self._session.scalars(
            select(LinkRow)
            .where(
                LinkRow.source_requirement_id.in_(ids),
                LinkRow.target_requirement_id.in_(ids),
            )
            .order_by(LinkRow.id)
        )
        return [link_entity(row) for row in rows]

    def add(self, source_id: int, target_id: int, link_type: LinkType) -> Link:
        row = LinkRow(
            source_requirement_id=source_id,
            target_requirement_id=target_id,
            link_type=link_type,
        )
        self._session.add(row)
        self._session.flush()
        return link_entity(row)

    def delete(self, link_id: int) -> None:
        self._session.execute(delete(LinkRow).where(LinkRow.id == link_id))

    def delete_for_requirements(self, requirement_ids: Sequence[int]) -> None:
        if requirement_ids:
            self._session.execute(
                delete(LinkRow).where(
                    or_(
                        LinkRow.source_requirement_id.in_(requirement_ids),
                        LinkRow.target_requirement_id.in_(requirement_ids),
                    )
                )
            )
