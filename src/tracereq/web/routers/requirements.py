from fastapi import APIRouter

from tracereq.application.commands import CreateRequirement, DeleteRequirement, UpdateRequirement
from tracereq.domain.entities import HistoryEntry, Requirement
from tracereq.web.dependencies import Requirements
from tracereq.web.schemas import (
    HistoryOutput,
    MessageOutput,
    RequirementDetailsOutput,
    RequirementOutput,
)

router = APIRouter(prefix='/projects/{project_id}/requirements', tags=['Requirements'])


@router.get('', response_model=list[RequirementDetailsOutput])
def list_requirements(project_id: int, service: Requirements) -> list[RequirementDetailsOutput]:
    return [
        RequirementDetailsOutput.from_details(item) for item in service.list_with_links(project_id)
    ]


@router.post('', response_model=RequirementOutput, status_code=201)
def create_requirement(
    project_id: int,
    command: CreateRequirement,
    service: Requirements,
) -> Requirement:
    return service.create(project_id, command)


@router.get('/{requirement_id}', response_model=RequirementDetailsOutput)
def get_requirement(
    project_id: int,
    requirement_id: int,
    service: Requirements,
) -> RequirementDetailsOutput:
    return RequirementDetailsOutput.from_details(service.details(project_id, requirement_id))


@router.put('/{requirement_id}', response_model=RequirementOutput)
def update_requirement(
    project_id: int,
    requirement_id: int,
    command: UpdateRequirement,
    service: Requirements,
) -> Requirement:
    return service.update(project_id, requirement_id, command)


@router.delete('/{requirement_id}', response_model=MessageOutput)
def delete_requirement(
    project_id: int,
    requirement_id: int,
    service: Requirements,
    command: DeleteRequirement | None = None,
) -> MessageOutput:
    service.delete(project_id, requirement_id, command.deleted_by if command else None)
    return MessageOutput(message='Requirement deleted successfully')


@router.get('/{requirement_id}/history', response_model=list[HistoryOutput])
def requirement_history(
    project_id: int,
    requirement_id: int,
    service: Requirements,
) -> list[HistoryEntry]:
    return service.history(project_id, requirement_id)
