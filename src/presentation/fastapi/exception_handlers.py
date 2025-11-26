from fastapi import FastAPI
from loguru import logger
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.application.errors import BaseError

def _exception_handler(_: Request, exc: BaseError) -> JSONResponse:
    logger.error('Exception', error=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={'errors': [str(exc)], 'code': exc.status_code}
    )

def setup_exception_handlers(app: FastAPI) -> None:
    app.exception_handler(BaseError)(_exception_handler)