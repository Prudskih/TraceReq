"""API маршруты"""

import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from config import Config
from database import get_db
from models.project import Project
from models.requirement import Requirement, RequirementType, RequirementStatus, Priority
from models.link import Link, LinkType
from services.docx_import_service import DocxImportService
from services.export_service import ExportService

import logic


api = APIRouter()


@api.post('/projects', status_code=201)
def create_project(session: Session = Depends(get_db), data: Optional[dict] = Body(default=None)):
    data = data or {}
    name = (data.get('name') or "").strip()
    description = (data.get('description') or "").strip()

    if not name:
        return JSONResponse(content={'error': 'name required'}, status_code=400)

    project = Project(name=name, description=description)
    session.add(project)
    session.commit()
    return JSONResponse(content=project.to_dict(), status_code=201)


@api.get('/projects')
def get_projects(session: Session = Depends(get_db)):
    projects = session.query(Project).order_by(Project.id.asc()).all()
    return [project.to_dict() for project in projects]


@api.put('/projects/{project_id}')
def update_project(project_id: int, session: Session = Depends(get_db), data: Optional[dict] = Body(default=None)):
    data = data or {}
    project = session.get(Project, project_id)
    if not project:
        return JSONResponse(content={'error': 'Project not found'}, status_code=404)

    name = (data.get('name') or "").strip()
    description = (data.get('description') or "").strip()

    if name:
        project.name = name
    project.description = description
    session.commit()
    return project.to_dict()


@api.delete('/projects/{project_id}')
def delete_project(project_id: int, session: Session = Depends(get_db)):
    project = session.get(Project, project_id)
    if not project:
        return JSONResponse(content={'error': 'Project not found'}, status_code=404)

    req_ids = session.query(Requirement.id).filter(Requirement.project_id == project_id)
    session.query(Link).filter(
        (Link.source_requirement_id.in_(req_ids))
        | (Link.target_requirement_id.in_(req_ids))
    ).delete(synchronize_session=False)
    session.query(Requirement).filter(Requirement.project_id == project_id).delete(synchronize_session=False)
    session.delete(project)
    session.commit()
    return {'message': 'Project deleted successfully'}


@api.get('/projects/{project_id}/requirements')
def get_requirements(project_id: int, session: Session = Depends(get_db)):
    """Все требования со связями."""
    return logic.get_all_requirements_with_links(session, project_id)


@api.get('/projects/{project_id}/requirements/{requirement_id}')
def get_requirement(project_id: int, requirement_id: int, session: Session = Depends(get_db)):
    req = logic.get_requirement_with_links(session, project_id, requirement_id)
    if req:
        return req
    return JSONResponse(content={'error': 'Requirement not found'}, status_code=404)

@api.post('/projects/{project_id}/requirements/import/docx', status_code=201)
def import_requirements_from_docx(project_id: int, session: Session = Depends(get_db), file: Optional[UploadFile] = File(default=None)):
    """Импорт требований из .docx файла."""
    uploaded_file = file

    if not uploaded_file:
        return JSONResponse(content={'error': 'Требуется файл'}, status_code=400)

    filename = (uploaded_file.filename or '').strip()
    if not filename:
        return JSONResponse(content={'error': 'Имя файла не задано'}, status_code=400)

    if not filename.lower().endswith('.docx'):
        return JSONResponse(content={'error': 'Поддерживается только формат .docx'}, status_code=400)

    file_bytes = uploaded_file.file.read()
    if not file_bytes:
        return JSONResponse(content={'error': 'Файл пустой'}, status_code=400)

    project = session.get(Project, project_id)
    if not project:
        return JSONResponse(content={'error': 'Project not found'}, status_code=404)

    aliases = Config.REQUIREMENT_TYPE_ALIASES
    parser = DocxImportService(aliases=aliases)

    try:
        parsed_requirements = parser.parse(file_bytes)

        created = []
        for parsed_requirement in parsed_requirements:
            payload = parsed_requirement.to_dict()
            requirement_data = {
                'title': payload['title'],
                'description': payload['description'],
                'requirement_type': RequirementType(payload['requirement_type']),
            }
            req = logic.create_requirement(
                session,
                project_id,
                requirement_data,
            )
            created.append(req.to_dict())

        return JSONResponse(content={'created_count': len(created), 'requirements': created}, status_code=201)
    except Exception as e:
        session.rollback()
        return JSONResponse(content={'error': str(e)}, status_code=400)




@api.post('/projects/{project_id}/requirements', status_code=201)
def create_requirement(project_id: int, session: Session = Depends(get_db), data: Optional[dict] = Body(default=None)):
    """Создание требования."""
    data = data or {}

    try:
        requirement_data = {
            'title': data.get('title'),
            'description': data.get('description', ''),
            'requirement_type': RequirementType(data.get('requirement_type')),
            'status': RequirementStatus(data.get('status', 'Черновик')),
            'priority': Priority(data.get('priority', 'Средний')),
            'source': data.get('source', ''),
            'author': data.get('author', '')
        }

        req = logic.create_requirement(session, project_id, requirement_data, author=data.get('author'))
        return JSONResponse(content=req.to_dict(), status_code=201)
    except Exception as e:
        session.rollback()
        return JSONResponse(content={'error': str(e)}, status_code=400)


@api.put('/projects/{project_id}/requirements/{requirement_id}')
def update_requirement(project_id: int, requirement_id: int, session: Session = Depends(get_db), data: Optional[dict] = Body(default=None)):
    """Обновление требования."""
    data = data or {}

    try:
        fields = {}

        if 'title' in data:
            fields['title'] = data['title']
        if 'description' in data:
            fields['description'] = data['description']
        if 'requirement_type' in data:
            fields['requirement_type'] = RequirementType(data['requirement_type'])
        if 'status' in data:
            fields['status'] = RequirementStatus(data['status'])
        if 'priority' in data:
            fields['priority'] = Priority(data['priority'])
        if 'source' in data:
            fields['source'] = data['source']
        if 'author' in data:
            fields['author'] = data['author']

        req = logic.update_requirement(session, project_id, requirement_id, fields, changed_by=data.get('changed_by'))
        if req:
            return req.to_dict()
        return JSONResponse(content={'error': 'Requirement not found'}, status_code=404)
    except Exception as e:
        session.rollback()
        return JSONResponse(content={'error': str(e)}, status_code=400)


@api.delete('/projects/{project_id}/requirements/{requirement_id}')
def delete_requirement(project_id: int, requirement_id: int, session: Session = Depends(get_db), data: Optional[dict] = Body(default=None)):
    """Удаление требования."""
    data = data or {}

    if logic.delete_requirement(session, project_id, requirement_id, deleted_by=data.get('deleted_by')):
        return {'message': 'Requirement deleted successfully'}

    return JSONResponse(content={'error': 'Requirement not found'}, status_code=404)


@api.get('/projects/{project_id}/requirements/{requirement_id}/history')
def get_requirement_history(project_id: int, requirement_id: int, session: Session = Depends(get_db)):
    """История изменения требования."""
    req = session.get(Requirement, requirement_id)
    if not req or req.project_id != project_id:
        return JSONResponse(content={'error': 'Requirement not found'}, status_code=404)
    history = logic.get_history(session, requirement_id)
    return [h.to_dict() for h in history]


@api.post('/projects/{project_id}/links', status_code=201)
def create_link(project_id: int, session: Session = Depends(get_db), data: Optional[dict] = Body(default=None)):
    """Создание связи между требованиями."""
    data = data or {}

    try:
        link = logic.create_link(
            session,
            project_id=project_id,
            source_id=data['source_id'],
            target_id=data['target_id'],
            link_type=LinkType(data['link_type'])
        )

        if link:
            return JSONResponse(content=link.to_dict(), status_code=201)
        return JSONResponse(content={'error': 'Invalid link data'}, status_code=400)
    except Exception as e:
        session.rollback()
        return JSONResponse(content={'error': str(e)}, status_code=400)


@api.delete('/links/{link_id}')
def delete_link(link_id: int, session: Session = Depends(get_db)):
    """Удаление связи."""
    if logic.delete_link(session, link_id):
        return {'message': 'Link deleted successfully'}
    return JSONResponse(content={'error': 'Link not found'}, status_code=404)


@api.get('/projects/{project_id}/matrix')
def get_requirements_matrix(project_id: int, session: Session = Depends(get_db)):
    """Матрица пересечений требований."""
    reqs, matrix, _links = logic.build_matrix(session, project_id)
    return {'requirements': [r.to_dict() for r in reqs], 'matrix': matrix}


@api.get('/projects/{project_id}/export')
def export_to_excel(project_id: int, session: Session = Depends(get_db)):
    """Экспорт требований и связей в Excel."""
    reqs, _matrix, links = logic.build_matrix(session, project_id)

    exporter = ExportService()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_file.close()

    try:
        exporter.export_to_excel(reqs, links, temp_file.name)
    except Exception:
        Path(temp_file.name).unlink(missing_ok=True)
        raise

    return FileResponse(
        temp_file.name,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename='requirements_trace.xlsx',
        background=BackgroundTask(Path(temp_file.name).unlink, missing_ok=True)
    )


@api.get('/projects/{project_id}/export/matrix')
def export_matrix_to_excel(project_id: int, session: Session = Depends(get_db)):
    """Экспорт матрицы пересечений в Excel."""
    reqs, _matrix, links = logic.build_matrix(session, project_id)

    exporter = ExportService()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_file.close()

    try:
        exporter.export_matrix_to_excel(reqs, links, temp_file.name)
    except Exception:
        Path(temp_file.name).unlink(missing_ok=True)
        raise

    return FileResponse(
        temp_file.name,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename='requirements_matrix.xlsx',
        background=BackgroundTask(Path(temp_file.name).unlink, missing_ok=True)
    )
