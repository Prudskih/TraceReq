from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from tracereq.web.dependencies import Projects

router = APIRouter(include_in_schema=False)


@router.get('/', response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(request=request, name='login.html')


@router.get('/project/{project_id}', response_class=HTMLResponse)
def project_home(project_id: int, request: Request, service: Projects) -> HTMLResponse:
    project = service.get(project_id)
    return request.app.state.templates.TemplateResponse(
        request=request,
        name='index.html',
        context={'project': project},
    )
