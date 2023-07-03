from fastapi import (
    APIRouter,
    Depends
)
from . import (
    auth,
    post,
)
from ..depends.users import check_auth


def register_routers(app):
    router = APIRouter(prefix='/api/v1')

    router.include_router(
        auth.router,
    )
    router.include_router(
        post.router,
        dependencies=[Depends(check_auth)]
    )
    app.include_router(router)
    return app
