import logging

import fastapi

logger = logging.getLogger(__name__)


async def get(request: fastapi.Request) -> dict:
    try:
        return request.app.state.config
    except AttributeError:
        raise RuntimeError('Application state has no configs')
