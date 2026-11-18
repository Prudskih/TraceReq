"""Фабрика приложения — место сборки конкретных зависимостей."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import sessionmaker

from tracereq.application.ports import ReportExporter, RequirementParser
from tracereq.infrastructure.documents.docx import DocxImportService
from tracereq.infrastructure.documents.xlsx import XlsxExporter
from tracereq.infrastructure.persistence.database import create_database_engine
from tracereq.settings import Settings
from tracereq.web.errors import register_error_handlers
from tracereq.web.routers import documents, links, pages, projects, requirements
from tracereq.web.schemas import ErrorOutput


def create_app(
    settings: Settings | None = None,
    *,
    requirement_parser: RequirementParser | None = None,
    report_exporter: ReportExporter | None = None,
) -> FastAPI:
    config = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(config)
        app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title='TraceReq', version='0.2.0', lifespan=lifespan)
    app.state.settings = config
    app.state.requirement_parser = (
        requirement_parser
        if requirement_parser is not None
        else DocxImportService(aliases=config.requirement_type_aliases)
    )
    app.state.report_exporter = report_exporter if report_exporter is not None else XlsxExporter()
    assets = Path(__file__).resolve().parent
    app.state.templates = Jinja2Templates(directory=assets / 'templates')
    app.mount('/static', StaticFiles(directory=assets / 'static'), name='static')
    api = APIRouter(
        prefix='/api',
        responses={code: {'model': ErrorOutput} for code in (400, 404, 409, 422, 500)},
    )
    for router in (projects.router, requirements.router, links.router, documents.router):
        api.include_router(router)
    app.include_router(api)
    app.include_router(pages.router)
    register_error_handlers(app)
    return app
