from typing import (
    List,
    Any,
    Dict,
    Optional
)

from fastapi import (
    Request,
    FastAPI
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from models.base import (
    ValidationError,
    ErrorResponse,
    UpdateErrorResponse
)


class UnauthenticatedException(Exception):
    pass


class ForbiddenException(Exception):
    pass


class NotFoundException(Exception):
    pass


async def error_409(errors: List[Any]):
    return JSONResponse(status_code=409, content=UpdateErrorResponse(errors=errors).json())


async def ok_204() -> JSONResponse:
    return JSONResponse(status_code=204)


async def error_500(detail: Optional[str] = None, debug: Optional[str] = None) -> JSONResponse:
    return JSONResponse(status_code=500,
                        content=ErrorResponse(error=detail or 'Server internal fatal_error', debug=debug).dict())


async def error_400_with_detail(detail: Optional[str] = None, debug: Optional[str] = None) -> JSONResponse:
    return JSONResponse(status_code=400,
                        content=ErrorResponse(error=detail or 'Wrong request data', debug=debug).dict())


async def error_404(message: Optional[str] = None) -> JSONResponse:
    return JSONResponse(status_code=404, content=ErrorResponse(error=message or 'not found').dict())


async def error_401(message: Optional[str] = None) -> JSONResponse:
    return JSONResponse(status_code=401, content=ErrorResponse(error=message or 'unauthorized').dict())


async def error_403(message: Optional[str] = None) -> JSONResponse:
    return JSONResponse(status_code=403, content=ErrorResponse(error=message or 'forbidden').dict())


async def error_400(message: Optional[str] = None) -> JSONResponse:
    return JSONResponse(status_code=400, content=ErrorResponse(error=message or 'invalid input data').dict())


async def error_400_with_content(content: Dict) -> JSONResponse:
    return JSONResponse(status_code=400, content=content)


def register_exception_handler(app: FastAPI):
    if not app.state.config['debug']:
        @app.exception_handler(Exception)
        async def http_exception_handler(request, exc) -> JSONResponse:
            return await error_500(debug=str(exc) if app.state.config['debug'] else None)

        @app.exception_handler(StarletteHTTPException)
        async def starlette_http_exception_handler(request, exc) -> JSONResponse:
            return await error_500(debug=str(exc) if app.state.config['debug'] else None)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        validation_error = None
        errors = exc.errors()
        if errors:
            validation_error = []
            for i in errors:
                validation_error.append(
                    ValidationError(
                        field='.'.join([str(l) for l in i['loc'][1:]]),
                        message=i['msg']
                    )
                )

        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error='Client sent incomplete data',
                validation_error=validation_error,
                debug=str(exc) if app.state.config['debug'] else None
            ).dict())

    @app.exception_handler(UnauthenticatedException)
    async def unauthenticated_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return await error_401()

    @app.exception_handler(ForbiddenException)
    async def forbidden_exception_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
        return await error_403()

    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
        return await error_404()
