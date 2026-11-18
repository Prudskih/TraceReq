"""XLSX-адаптер получает снимки данных, не ORM-объекты и не HTTP-запросы."""

from collections.abc import Sequence
from io import BytesIO

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from tracereq.domain.entities import TraceabilityReport


def append_row(sheet: Worksheet, values: Sequence[str | int]) -> None:
    sheet.append(list(values))
    # User text beginning with '=' must remain text rather than an Excel formula.
    for cell in sheet[sheet.max_row]:
        if isinstance(cell.value, str):
            cell.data_type = 's'


def workbook_bytes(workbook: Workbook) -> bytes:
    try:
        with BytesIO() as output:
            workbook.save(output)
            return output.getvalue()
    finally:
        workbook.close()


class XlsxExporter:
    def export_requirements(self, report: TraceabilityReport) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        assert isinstance(sheet, Worksheet)
        sheet.title = 'Requirements'
        append_row(sheet, ['id', 'title', 'type', 'status', 'priority', 'source', 'author'])
        for item in report.requirements:
            append_row(
                sheet,
                [
                    item.id,
                    item.title,
                    item.requirement_type.value,
                    item.status.value,
                    item.priority.value,
                    item.source,
                    item.author,
                ],
            )
        links_sheet = workbook.create_sheet('Links')
        append_row(links_sheet, ['id', 'source_id', 'target_id', 'link_type'])
        for link in report.links:
            append_row(
                links_sheet,
                [
                    link.id,
                    link.source_requirement_id,
                    link.target_requirement_id,
                    link.link_type.value,
                ],
            )
        return workbook_bytes(workbook)

    def export_matrix(self, report: TraceabilityReport) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        assert isinstance(sheet, Worksheet)
        sheet.title = 'Matrix'
        ids = [item.id for item in report.requirements]
        matrix = report.matrix()
        append_row(sheet, [''] + [f'#{identifier}' for identifier in ids])
        for source_id in ids:
            append_row(
                sheet,
                [f'#{source_id}']
                + [
                    '-' if source_id == target_id else matrix.get(source_id, {}).get(target_id, '')
                    for target_id in ids
                ],
            )
        return workbook_bytes(workbook)
