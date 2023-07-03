import logging
from typing import (
    Optional,
    List,
)
from models.users import (
    User,
    NewUser,
)
from misc import db

logger = logging.getLogger(__name__)

TABLE = 'users'

USER_DISPLAY_FIELDS = [
    'id',
    'en',
    'name',
    'email',
    'ctime',
    'atime',
    'dtime',
]


async def create_user(
        conn: db.Connection,
        email: str,
        password: str,
        username: str,
) -> Optional[User]:
    data = {
        'email': email,
        'name': username,
    }
    result = await db.create(conn, TABLE, data, fields=USER_DISPLAY_FIELDS)
    await set_password(conn, email, password)
    return db.record_to_model(User, result)


async def get_user_by_credentials(
        conn: db.Connection,
        email: str, password: str
) -> Optional[User]:
    result = await db.get_by_where(conn, TABLE, 'email=$1 AND password=$2 and en', values=[email, password],
                                   fields=USER_DISPLAY_FIELDS)
    return db.record_to_model(User, result)


async def get_user(
        conn: db.Connection,
        pk: Optional[int]
) -> Optional[User]:
    values = [pk]
    query = f'SELECT {", ".join(USER_DISPLAY_FIELDS)} FROM {TABLE} WHERE id = $1 AND en'
    result = await conn.fetchrow(query, *values)
    return db.record_to_model(User, result)


async def get_user_for_admin(
        conn: db.Connection,
        pk: Optional[int]
) -> Optional[User]:
    values = [pk]
    query = f'SELECT {", ".join(USER_DISPLAY_FIELDS)} FROM {TABLE} WHERE id = $1'
    result = await conn.fetchrow(query, *values)
    return db.record_to_model(User, result)


async def check_user_exists(
        conn: db.Connection,
        user_id: int
) -> bool:
    query = await conn.fetchrow(
        f"""
        SELECT count(*) FROM {TABLE} where id=$1
        """,
        user_id
    )
    return True if query['count'] else False


async def set_password(
        conn: db.Connection,
        email: str,
        password: str
) -> Optional[int]:
    data = await conn.fetchrow(
        f"UPDATE {TABLE} SET password=$2  WHERE email=$1 RETURNING id",
        email, password
    )
    return data['id'] if data else None


async def delete_user(
        conn: db.Connection,
        user_id: int,

) -> Optional[User]:
    values = [user_id]
    query = f"UPDATE {TABLE} SET en=False WHERE id=$1 RETURNING *"
    result = await conn.fetchrow(query, *values)
    logger.info(f'{query=}')
    logger.info(f'{result=}')
    return db.record_to_model(User, result)


async def email_exists(
        conn: db.Connection,
        email: str
) -> bool:
    user = await db.get_by_where(conn, TABLE, "email=$1 AND en=True", values=[email], fields=['id'])

    return True if user else False


async def get_users(
        limit: int,
        conn: db.Connection,
        page: int = None,

) -> Optional[List[User]]:
    offset = limit * (page - 1)
    values = [limit, offset]
    where = f'WHERE en'
    query = f'''SELECT * FROM {TABLE} {where} 
        ORDER BY name ASC LIMIT $1 OFFSET $2'''
    result = await conn.fetch(query, *values)
    return db.record_to_model_list(User, result)


async def get_total(
        conn: db.Connection,

) -> int:
    values = []
    where = f'WHERE en'
    query = f'''SELECT count(*) FROM {TABLE} {where} 
            ORDER BY name'''
    result = await conn.fetchrow(query, *values)
    return result['count']


async def get_users_for_admin(
        limit: int,
        conn: db.Connection,
        en: bool = None,
        username: str = None,
        email: str = None,
        page: int = None,

) -> Optional[List[User]]:
    offset = limit * (page - 1)
    where = []
    values = [limit, offset]
    idx = 3
    where, values, idx = user_filter(where, values, idx, en, username, email)
    if where:
        where = f'WHERE {" AND ".join(where)}'
    else:
        where = ''
    query = f'''SELECT * FROM {TABLE} {where} 
        ORDER BY name ASC LIMIT $1 OFFSET $2'''
    result = await conn.fetch(query, *values)
    return db.record_to_model_list(User, result)


async def get_total_for_admin(
        conn: db.Connection,
        en: bool = None,
        username: str = None,
        email: str = None,

) -> int:
    where = []
    values = []
    idx = 1
    where, values, idx = user_filter(where, values, idx, en, username, email)
    if where:
        where = f'WHERE {" AND ".join(where)}'
    else:
        where = ''
    query = f'''SELECT count(*) FROM {TABLE} {where}'''
    result = await conn.fetchrow(query, *values)
    return result['count']


async def admin_update_user(
        conn: db.Connection,
        pk: int,
        new_user: NewUser,
) -> Optional[User]:
    data = new_user.dict(exclude_none=True)
    result = await db.update(
        conn=conn,
        table=TABLE,
        pk=pk,
        data=data,
        with_atime=True
    )
    return db.record_to_model(User, result)


async def admin_delete_user(
        conn: db.Connection,
        user_id: int,

) -> Optional[User]:
    result = await db.disable(conn=conn, table=TABLE, pk=user_id)
    return db.record_to_model(User, result)


def user_filter(where, values, idx: int, en: bool = None, username: str = None, email: str = None):
    if en is not None:
        where.append(f"en = ${idx}")
        values.append(en)
        idx += 1
    if username:
        where.append(f"name LIKE ${idx}")
        values.append(f'%{username}%')
        idx += 1
    if email:
        where.append(f'email LIKE ${idx}')
        values.append(f'%{email}%')
        idx += 1
    return where, values, idx
