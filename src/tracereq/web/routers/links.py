from fastapi import APIRouter

from tracereq.application.commands import CreateLink
from tracereq.domain.entities import Link
from tracereq.web.dependencies import Links
from tracereq.web.schemas import LinkOutput, MessageOutput

router = APIRouter(tags=['Links'])


@router.post('/projects/{project_id}/links', response_model=LinkOutput, status_code=201)
def create_link(project_id: int, command: CreateLink, service: Links) -> Link:
    return service.create(project_id, command)


@router.delete('/links/{link_id}', response_model=MessageOutput)
def delete_link(link_id: int, service: Links) -> MessageOutput:
    service.delete(link_id)
    return MessageOutput(message='Link deleted successfully')
