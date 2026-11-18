"""Связывание HTTP-запроса с прикладными сервисами и адаптерами."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request

from tracereq.application.importing import ImportService
from tracereq.application.links import LinkService
from tracereq.application.ports import UnitOfWork
from tracereq.application.projects import ProjectService
from tracereq.application.reporting import ReportService
from tracereq.application.requirements import RequirementService
from tracereq.infrastructure.persistence.uow import SqlAlchemyUnitOfWork


def get_uow(request: Request) -> Iterator[UnitOfWork]:
    with SqlAlchemyUnitOfWork(request.app.state.session_factory) as uow:
        yield uow


UowDependency = Annotated[UnitOfWork, Depends(get_uow)]


def get_projects(uow: UowDependency) -> ProjectService:
    return ProjectService(uow)


def get_requirements(uow: UowDependency) -> RequirementService:
    return RequirementService(uow)


def get_links(uow: UowDependency) -> LinkService:
    return LinkService(uow)


def get_importer(request: Request, uow: UowDependency) -> ImportService:
    return ImportService(uow, request.app.state.requirement_parser)


def get_reports(request: Request, uow: UowDependency) -> ReportService:
    return ReportService(uow, request.app.state.report_exporter)


Projects = Annotated[ProjectService, Depends(get_projects)]
Requirements = Annotated[RequirementService, Depends(get_requirements)]
Links = Annotated[LinkService, Depends(get_links)]
Importer = Annotated[ImportService, Depends(get_importer)]
Reports = Annotated[ReportService, Depends(get_reports)]
