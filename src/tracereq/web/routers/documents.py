from typing import Annotated, Any

from fastapi import APIRouter, File, Request, Response, UploadFile

from tracereq.domain.errors import InvalidInput
from tracereq.web.dependencies import Importer, Reports
from tracereq.web.schemas import ImportOutput, MatrixOutput, RequirementOutput

router = APIRouter(prefix='/projects/{project_id}', tags=['Documents'])
XLSX_MEDIA_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
XLSX_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {'content': {XLSX_MEDIA_TYPE: {'schema': {'type': 'string', 'format': 'binary'}}}}
}


@router.post('/requirements/import/docx', response_model=ImportOutput, status_code=201)
def import_docx(
    project_id: int,
    request: Request,
    service: Importer,
    file: Annotated[UploadFile | None, File()] = None,
) -> ImportOutput:
    if file is None:
        raise InvalidInput('Требуется файл')
    filename = (file.filename or '').strip()
    if not filename:
        raise InvalidInput('Имя файла не задано')
    if not filename.lower().endswith('.docx'):
        raise InvalidInput('Поддерживается только формат .docx')
    limit = request.app.state.settings.max_upload_bytes
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise InvalidInput('Превышен допустимый размер файла')
    requirements = service.import_docx(project_id, content)
    return ImportOutput(
        created_count=len(requirements),
        requirements=[RequirementOutput.model_validate(item) for item in requirements],
    )


@router.get('/matrix', response_model=MatrixOutput)
def get_matrix(project_id: int, service: Reports) -> MatrixOutput:
    report = service.report(project_id)
    return MatrixOutput(
        requirements=[RequirementOutput.model_validate(item) for item in report.requirements],
        matrix=report.matrix(),
    )


@router.get('/export', response_class=Response, responses=XLSX_RESPONSE)
def export_requirements(project_id: int, service: Reports) -> Response:
    return Response(
        content=service.export_requirements(project_id),
        media_type=XLSX_MEDIA_TYPE,
        headers={'Content-Disposition': 'attachment; filename="requirements_trace.xlsx"'},
    )


@router.get('/export/matrix', response_class=Response, responses=XLSX_RESPONSE)
def export_matrix(project_id: int, service: Reports) -> Response:
    return Response(
        content=service.export_matrix(project_id),
        media_type=XLSX_MEDIA_TYPE,
        headers={'Content-Disposition': 'attachment; filename="requirements_matrix.xlsx"'},
    )
