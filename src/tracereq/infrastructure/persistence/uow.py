"""Одна SQLAlchemy-сессия на запрос; commit выполняется только сценарием."""

from types import TracebackType
from typing import Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from tracereq.application.ports import (
    HistoryRepository,
    LinkRepository,
    ProjectRepository,
    RequirementRepository,
)
from tracereq.domain.errors import Conflict
from tracereq.infrastructure.persistence.history import SqlAlchemyHistoryRepository
from tracereq.infrastructure.persistence.links import SqlAlchemyLinkRepository
from tracereq.infrastructure.persistence.projects import SqlAlchemyProjectRepository
from tracereq.infrastructure.persistence.requirements import SqlAlchemyRequirementRepository


class SqlAlchemyUnitOfWork:
    projects: ProjectRepository
    requirements: RequirementRepository
    links: LinkRepository
    history: HistoryRepository

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.projects = SqlAlchemyProjectRepository(self._session)
        self.requirements = SqlAlchemyRequirementRepository(self._session)
        self.links = SqlAlchemyLinkRepository(self._session)
        self.history = SqlAlchemyHistoryRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            self.rollback()
        finally:
            self._session.close()
        if isinstance(exc, IntegrityError):
            raise Conflict('Операция нарушает уникальность или связи данных') from exc

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as exc:
            self.rollback()
            raise Conflict('Операция нарушает уникальность или связи данных') from exc

    def rollback(self) -> None:
        self._session.rollback()
