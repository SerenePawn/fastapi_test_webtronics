from fastapi import Depends
from misc.session import Session
from misc.fastapi.depends.session import get as get_session
from misc.fastapi.depends.db import get as get_db
from misc.redis import Connection as RedisConnection
from misc import redis
from misc.fastapi.depends.redis import get as get_cache
from misc.handlers import (
    ForbiddenException,
    NotFoundException
)
from misc import db
from db import posts as posts_db


async def check_availability(
        post_id: int,
        session: Session = Depends(get_session),
        conn: db.Connection = Depends(get_db),
):
    is_exists = await posts_db.get(conn, post_id)
    if not is_exists:
        raise NotFoundException()
    if is_exists.owner_id != session.session_user_id:
        raise ForbiddenException()


async def check_availability_evaluate(
        post_id: int,
        session: Session = Depends(get_session),
        conn: db.Connection = Depends(get_db),
):
    is_exists = await posts_db.get(conn, post_id)
    if not is_exists:
        raise NotFoundException()
    if is_exists.owner_id == session.session_user_id:
        raise ForbiddenException()


async def cache_post(
        post_id: int,
        cache: RedisConnection = Depends(get_cache),
        conn: db.Connection = Depends(get_db),
):
    cached_post = await redis.get(f'post_{post_id}', conn=cache)
    if not cached_post:
        existing_post = await posts_db.get(conn, post_id)
        likes = existing_post.likes
        dislikes = existing_post.dislikes
        await redis.setex(f'post_{post_id}', ttl=3600, value={"likes": likes, "dislikes": dislikes}, conn=cache)
