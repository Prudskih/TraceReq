from fastapi import APIRouter

from tracereq.application.commands import CreateProject, UpdateProject
from tracereq.domain.entities import Project
from tracereq.web.dependencies import Projects
from tracereq.web.schemas import MessageOutput, ProjectOutput

router = APIRouter(prefix='/projects', tags=['Projects'])


@router.get('', response_model=list[ProjectOutput])
def list_projects(service: Projects) -> list[Project]:
    return service.list()


@router.post('', response_model=ProjectOutput, status_code=201)
def create_project(command: CreateProject, service: Projects) -> Project:
    return service.create(command)


@router.put('/{project_id}', response_model=ProjectOutput)
def update_project(project_id: int, command: UpdateProject, service: Projects) -> Project:
    return service.update(project_id, command)


@router.delete('/{project_id}', response_model=MessageOutput)
def delete_project(project_id: int, service: Projects) -> MessageOutput:
    service.delete(project_id)
    return MessageOutput(message='Project deleted successfully')
