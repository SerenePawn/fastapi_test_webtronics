from fastapi import (
    APIRouter,
    Depends
)
import logging
from fastapi.responses import JSONResponse
from misc.db import (
    Connection as DbConnection
)
from misc.fastapi.depends.db import (
    get as get_db
)
from misc import redis
from misc.redis import Connection as RedisConnection
from misc.handlers import (
    error_404,
    error_400
)
from misc.session import Session
from misc.fastapi.depends.session import get as get_session
from misc.fastapi.depends.redis import get as get_cache
from services.fastapi_test_webtronics.depends.posts import (
    check_availability,
    check_availability_evaluate,
    cache_post
)

from models.posts import (
    NewPost,
    UpdatePost,
    PostSuccessResponse,
    PostListSuccessResponse
)
from db import posts as posts_db


router = APIRouter(
    prefix='/posts',
    tags=['posts']
)

logger = logging.getLogger(__name__)


@router.get(
    '/',
    name='get_posts',
    response_model=PostListSuccessResponse
)
async def get_posts(
        conn: DbConnection = Depends(get_db)
) -> PostListSuccessResponse | JSONResponse:
    # In production this endpoint needs pagination
    result = await posts_db.get_list(conn)

    return PostListSuccessResponse(data=result)


@router.get(
    '/post/{post_id}',
    name='get_post',
    response_model=PostSuccessResponse
)
async def get_post(
        post_id: int,
        conn: DbConnection = Depends(get_db)
) -> PostSuccessResponse | JSONResponse:
    result = await posts_db.get(conn, post_id)
    if not result:
        return await error_404()

    return PostSuccessResponse(data=result)


@router.post(
    '/post/',
    name='create_post',
    response_model=PostSuccessResponse
)
async def create_post(
        data: NewPost,
        session: Session = Depends(get_session),
        conn: DbConnection = Depends(get_db)
) -> PostSuccessResponse | JSONResponse:
    is_exists = await posts_db.get_by_name(conn, data.name, en=False)
    if is_exists:
        return await error_400()

    result = await posts_db.create(conn, data, session.session_user_id)
    logger.debug(f"{result.id} has been created.")
    return PostSuccessResponse(data=result)


@router.post(
    '/post/{post_id}',
    name='update_post',
    response_model=PostSuccessResponse,
    dependencies=[Depends(check_availability)]
)
async def update_post(
        post_id: int,
        data: UpdatePost,
        conn: DbConnection = Depends(get_db)
) -> PostSuccessResponse | JSONResponse:
    result = await posts_db.update(conn, post_id, data)
    logger.debug(f"{post_id} has been updated.")
    return PostSuccessResponse(data=result)


@router.delete(
    '/post/{post_id}',
    name='disable_post',
    response_model=PostSuccessResponse,
    dependencies=[Depends(check_availability)]
)
async def disable_post(
        post_id: int,
        conn: DbConnection = Depends(get_db)
) -> PostSuccessResponse | JSONResponse:
    result = await posts_db.disable(conn, post_id)
    logger.debug(f"{post_id} has been disabled.")
    return PostSuccessResponse(data=result)


@router.post(
    '/post/like/{post_id}',
    name='like_post',
    response_model=PostSuccessResponse,
    dependencies=[
        Depends(check_availability_evaluate),
        Depends(cache_post)
    ]
)
async def like_post(
        post_id: int,
        cache: RedisConnection = Depends(get_cache),
        conn: DbConnection = Depends(get_db)
) -> PostSuccessResponse | JSONResponse:
    cached_post = await redis.get(f'post_{post_id}', conn=cache)
    likes = cached_post.get('likes')
    cached_post.update({'likes': likes + 1})

    result = await posts_db.update(conn, post_id, cached_post)
    await redis.setex(f'post_{post_id}', ttl=3600, value=cached_post, conn=cache)

    logger.debug(f"{result.id} post liked.")
    return PostSuccessResponse(data=result)


@router.post(
    '/post/dislike/{post_id}',
    name='dislike_post',
    response_model=PostSuccessResponse,
    dependencies=[
        Depends(check_availability_evaluate),
        Depends(cache_post)
    ]
)
async def dislike_post(
        post_id: int,
        cache: RedisConnection = Depends(get_cache),
        conn: DbConnection = Depends(get_db)
) -> PostSuccessResponse | JSONResponse:
    cached_post = await redis.get(f'post_{post_id}', conn=cache)
    dislikes = cached_post.get('dislikes')
    cached_post.update({'dislikes': dislikes + 1})

    result = await posts_db.update(conn, post_id, cached_post)
    await redis.setex(f'post_{post_id}', ttl=3600, value=cached_post, conn=cache)

    logger.debug(f"{result.id} post disliked.")
    return PostSuccessResponse(data=result)
