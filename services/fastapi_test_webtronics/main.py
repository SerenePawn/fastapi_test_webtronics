from misc import (
    db,
    ctrl,
    redis,
    smtp,
    config
)

import asyncio
from fastapi import (
    FastAPI,
    Depends,
)
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from .state import State
from misc.fastapi.depends.session import (
    get as get_session
)
from models.base import ErrorResponse, UpdateErrorResponse
from misc.handlers import register_exception_handler
import os
from . import template_processing

logger = logging.getLogger(__name__)


def factory():
    app = ctrl.main_with_parses(None, main)
    if not app:
        raise RuntimeError
    return app


def main(args, config):
    loop = asyncio.get_event_loop()
    root_path = config.get('rot_path', None)
    state = State(
        loop=loop,
        config=config
    )
    app = FastAPI(
        title='Fastapi template REST API',
        debug=config.get('debug', False),
        root_path=root_path,
        responses=responses(),
        dependencies=[Depends(get_session)],
    )

    app.state = state
    state.app = app
    check_folders(config)
    register_exception_handler(app)

    register_routers(app)
    register_startup(app)
    register_shutdown(app)

    static = StaticFiles(directory=Path(__name__).parent.parent.parent.absolute() / 'static')
    app.mount('/static', static, name='static')

    return app


def register_startup(app):
    @app.on_event("startup")
    async def handler_startup():
        logger.info('Startup called')
        try:
            await startup(app)
            logger.info(f"REST API app startup executed")
        except:
            logger.exception('Startup crashed')


def register_shutdown(app):
    @app.on_event("shutdown")
    async def handler_shutdown():
        logger.info('Shutdown called')
        try:
            await shutdown(app)
            logger.info(f"REST API app shutdown executed")
        except:
            logger.exception('Shutdown crashed')


async def startup(app):
    app.state.db_pool = await db.init(app.state.config['db'])
    app.state.redis_pool = await redis.init(app.state.config['redis'])
    app.state.smtp = await smtp.init(app.state.config['smtp'])
    app.state.template_processing = await template_processing.init(app.state)
    app = await startup_jinja(app)
    return app


async def shutdown(app):
    if app.state.db_pool:
        await db.close(app.state.db_pool)
    if app.state.redis_pool:
        await redis.close(app.state.redis_pool)
    if app.state.template_processing:
        await template_processing.close(app.state.template_processing)


async def startup_jinja(app):
    from jinja2 import (
        Environment,
        ChoiceLoader,
        PackageLoader,
        FileSystemLoader,
        select_autoescape
    )

    env = Environment(
        loader=ChoiceLoader([
            FileSystemLoader('templates')
        ]),
        autoescape=select_autoescape()
    )
    app.state.jinja = env
    return app


def register_routers(app):
    from . import routers
    return routers.register_routers(app)


def check_folders(conf):
    if not os.path.exists(config.static_files_folder(conf)):
        os.makedirs(config.static_files_folder(conf))
    if not os.path.exists(config.template_files_folder(conf)):
        os.makedirs(config.template_files_folder(conf))


def responses():
    return {
        409: {
            "model": UpdateErrorResponse
        },
        400: {
            "model": ErrorResponse
        },
        401: {
            "model": ErrorResponse
        },
        404: {
            "model": ErrorResponse
        },
        422: {
            "model": ErrorResponse
        },
        500: {
            "model": ErrorResponse
        },
    }
