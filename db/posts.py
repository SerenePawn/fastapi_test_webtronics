import logging
from typing import (
    Optional,
)
from models.posts import (
    Post,
    NewPost,
    UpdatePost
)
from misc import db

logger = logging.getLogger(__name__)

TABLE = 'posts'


async def get(
    conn: db.Connection,
    post_id: int
) -> Optional[Post]:
    where = "id = $1 AND en"
    result = await db.get_by_where(conn, TABLE, where, [post_id])
    return db.record_to_model(Post, result)


async def get_list(
    conn: db.Connection,
) -> Optional[list[Post]]:
    where = "en"
    result = await db.get_list(conn, TABLE, where)
    return db.record_to_model_list(Post, result)


async def get_by_name(
    conn: db.Connection,
    post_name: str,
    en: bool = True
) -> Optional[Post]:
    wheres = ["name = $1"]
    if en:
        wheres.append("en")
    where = " AND ".join(wheres)

    result = await db.get_by_where(conn, TABLE, where, [post_name])
    return db.record_to_model(Post, result)


async def create(
        conn: db.Connection,
        data: NewPost,
        owner_id: int
) -> Optional[Post]:
    post_dict = data.dict()
    post_dict.update({'owner_id': owner_id})
    result = await db.create(conn, TABLE, post_dict)
    return db.record_to_model(Post, result)


async def update(
        conn: db.Connection,
        post_id: int,
        data: UpdatePost | dict
) -> Optional[Post]:
    post_dict = data.dict() if isinstance(data, UpdatePost) else data
    result = await db.update(conn, TABLE, post_id, post_dict, with_atime=True)
    return db.record_to_model(Post, result)


async def disable(
        conn: db.Connection,
        post_id: int
) -> Optional[Post]:
    result = await db.disable_by_where(conn, TABLE, post_id, with_dtime=True)
    logger.debug(f'{result=}')
    return db.record_to_model(Post, result)
