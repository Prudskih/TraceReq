"""Подготовка данных трассировки и передача их файловому адаптеру."""

from tracereq.application.ports import ReportExporter, UnitOfWork
from tracereq.domain.entities import TraceabilityReport
from tracereq.domain.errors import NotFound


class ReportService:
    def __init__(self, uow: UnitOfWork, exporter: ReportExporter) -> None:
        self._uow = uow
        self._exporter = exporter

    def report(self, project_id: int) -> TraceabilityReport:
        if self._uow.projects.get(project_id) is None:
            raise NotFound('Project not found')
        return TraceabilityReport(
            self._uow.requirements.list(project_id),
            self._uow.links.list_for_project(project_id),
        )

    def export_requirements(self, project_id: int) -> bytes:
        return self._exporter.export_requirements(self.report(project_id))

    def export_matrix(self, project_id: int) -> bytes:
        return self._exporter.export_matrix(self.report(project_id))
