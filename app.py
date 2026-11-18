"""Веб-приложение TraceReq на FastAPI."""
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from api.routes import api
from database import get_db
from models.project import Project


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="TraceReq")
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
app.include_router(api, prefix='/api')
templates = Jinja2Templates(directory=BASE_DIR / 'templates')


@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name='login.html')


@app.get('/project/{project_id}', response_class=HTMLResponse)
def project_home(request: Request, project_id: int, session: Session = Depends(get_db)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    return templates.TemplateResponse(
        request=request, name='index.html', context={'project': project}
    )


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
