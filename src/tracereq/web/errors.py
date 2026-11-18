"""Единый формат ошибок без раскрытия SQL и внутренних исключений клиенту."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from tracereq.domain.errors import ApplicationError, Conflict, InvalidInput, NotFound

logger = logging.getLogger(__name__)


async def application_error(_request: Request, exc: ApplicationError) -> JSONResponse:
    if isinstance(exc, NotFound):
        status = 404
    elif isinstance(exc, Conflict):
        status = 409
    elif isinstance(exc, InvalidInput):
        status = 400
    else:
        status = 500
    return JSONResponse({'error': str(exc)}, status_code=status)


async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    messages = [
        f'{".".join(str(part) for part in error["loc"])}: {error["msg"]}' for error in exc.errors()
    ]
    return JSONResponse({'error': '; '.join(messages)}, status_code=422)


async def http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        {'error': str(exc.detail)}, status_code=exc.status_code, headers=exc.headers
    )


async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        'Unhandled error for %s %s',
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse({'error': 'Internal server error'}, status_code=500)


def register_error_handlers(app: FastAPI) -> None:
    app.exception_handler(ApplicationError)(application_error)
    app.exception_handler(RequestValidationError)(validation_error)
    app.exception_handler(HTTPException)(http_error)
    app.exception_handler(Exception)(unexpected_error)
