import logging
import datetime
from typing import (
    Optional,
    Any,
    List,
    Dict,
    Union,
    Type,
    TypeVar
)
import asyncpg
import json
from pydantic import BaseModel

logger = logging.getLogger(__name__)

Connection = asyncpg.Connection
ModelCls = TypeVar('ModelCls', bound=BaseModel)


async def init(config: dict) -> asyncpg.Pool:
    dsn = config.get('dsn')
    if not dsn:
        raise RuntimeError('DB connection parameters not defined')
    return await asyncpg.create_pool(
        dsn,
        init=init_connection,
        **{k: v for k, v in config.items() if k != 'dsn'}
    )


async def get_conn(config: dict) -> Connection:
    dsn = config.pop('dsn')
    if not dsn:
        raise RuntimeError('DB connection parameters not defined')
    return await asyncpg.connect(dsn, **config)


async def close(db: Union[asyncpg.Pool, asyncpg.Connection]):
    await db.close()


async def init_connection(conn):
    await conn.set_type_codec(
        'jsonb',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )
    return conn


async def get_by_where(
        conn: Connection,
        table: str,
        where: str,
        values: Optional[List] = [],
        fields: Optional[List[str]] = None
) -> Optional[asyncpg.Record]:
    select_fields = ', '.join(fields) if fields else '*'
    query = f'SELECT {select_fields} FROM {table} WHERE {where}'
    try:
        return await conn.fetchrow(query, *values)
    except:
        logger.exception(f'Query {query} failed')
        raise


def record_to_model_list(model_cls: Type[ModelCls], records: List[asyncpg.Record]) -> List[ModelCls]:
    if records:
        models = []
        for i in records:
            record_model = record_to_model(model_cls, i)
            if record_model is not None:
                models.append(record_model)
        return models
    return []


def record_to_model(model_cls: Type[ModelCls], record: Optional[asyncpg.Record]) -> Optional[ModelCls]:
    if record:
        return model_cls.parse_obj(record)
    return None


async def get(
        conn: Connection,
        table: str,
        pk: int,
        fields: Optional[List[str]] = None
) -> Optional[asyncpg.Record]:
    select_fields = ', '.join(fields) if fields else '*'
    query = f'SELECT {select_fields} FROM {table} WHERE id = $1'
    try:
        return await conn.fetchrow(query, pk)
    except:
        logger.exception(f'Query {query} failed')
        raise


async def get_list(
        conn: Connection,
        table: str,
        where: str,
        values: List = [],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[List[str]] = None,
        group: Optional[List[str]] = None,
        fields: List[str] = [],
) -> List[asyncpg.Record]:
    select_fields = ', '.join(fields) if fields else '*'
    where_query, limit_query, offset_query, order_query, group_query = '', '', '', '', ''
    if where:
        where_query = f'WHERE {where}'
    if limit:
        limit_query = f'LIMIT {limit}'
    if offset:
        offset_query = f'OFFSET {(offset - 1) * limit}'
    if order:
        order_query = 'ORDER BY ' + ', '.join([f'{i[1:]} DESC' if i.startswith('-') else i for i in order])
    if group:
        group_query = f"GROUP BY {','.join(group)}"
    query = f'SELECT {select_fields} FROM {table} {where_query} {order_query} {group_query} {limit_query} {offset_query}'
    try:
        return await conn.fetch(query, *values)
    except:
        logger.exception(f'Query {query} failed')
        raise


async def create(
        conn: Connection,
        table: str,
        data: Dict[str, Any],
        insert_fields: Optional[List[str]] = None,
        ignore_fields: Optional[List[str]] = None,
        fields: Optional[List[str]] = []
) -> Optional[asyncpg.Record]:
    return_fields = ', '.join(fields) if fields else '*'
    field_names = []
    placeholders = []
    values = []
    idx = 1
    for key in data.keys():
        if insert_fields and key not in insert_fields:
            continue

        if ignore_fields and key in ignore_fields:
            continue

        field_names.append(key)
        placeholders.append(f"${idx}")
        values.append(data[key])
        idx += 1
    query = f'INSERT INTO {table} ({", ".join(field_names)}) VALUES ({", ".join(placeholders)}) RETURNING {return_fields}'
    try:
        return await conn.fetchrow(query, *values)
    except:
        logger.exception(f'Query {query} failed')
        raise


async def update(
        conn: Connection,
        table: str,
        pk: int,
        data: Dict[str, Any],
        update_fields: Optional[List[str]] = None,
        ignore_fields: Optional[List[str]] = None,
        fields: Optional[List[str]] = [],
        with_atime: bool = False
) -> Optional[asyncpg.Record]:
    return_fields = ', '.join(fields) if fields else '*'
    placeholders = []
    values = []
    idx = 1
    for key in data.keys():
        if with_atime and key == 'atime':
            continue

        if update_fields and key not in update_fields:
            continue

        if ignore_fields and key in ignore_fields:
            continue

        placeholders.append(f"{key} = ${idx}")
        values.append(data[key])
        idx += 1
    if with_atime:
        placeholders.append(f"atime = (now() at time zone 'utc')")
    update = ', '.join(placeholders)
    query = f'UPDATE {table} SET {update} WHERE id = ${len(values) + 1} RETURNING {return_fields}'
    values.append(pk)
    try:
        return await conn.fetchrow(query, *values)
    except:
        logger.exception(f'Query {query} failed')
        raise


async def update_by_where(
        conn: Connection,
        table: str,
        data: Dict[str, Any],
        where: str,
        values: Optional[List] = [],
        update_fields: Optional[List[str]] = None,
        ignore_fields: Optional[List[str]] = None,
        fields: Optional[List[str]] = [],
        with_atime: bool = False
) -> Optional[asyncpg.Record]:
    return_fields = ', '.join(fields) if fields else '*'
    placeholders = []
    update_values = []
    idx = len(values) + 1
    for key in data.keys():
        if with_atime and key == 'atime':
            continue

        if update_fields and key not in update_fields:
            continue

        if ignore_fields and key in ignore_fields:
            continue

        placeholders.append(f"{key} = ${idx}")
        update_values.append(data[key])
        idx += 1
    if with_atime:
        placeholders.append(f"atime = (now() at time zone 'utc')")
    update = ', '.join(placeholders)
    values.extend(update_values)
    query = f'UPDATE {table} SET {update} WHERE {where} RETURNING {return_fields}'
    try:
        return await conn.fetchrow(query, *values)
    except:
        logger.exception(f'Query {query} failed')
        raise


async def disable_by_where(
        conn: Connection,
        table: str,
        pk: int,
        data: Optional[Dict[str, Any]] = None,
        with_dtime: bool = False
) -> Optional[asyncpg.Record]:
    values = [pk]
    wheres = [f"id = $1"]
    idx = 2
    if data:
        for k in data:
            values.append(data[k])
            wheres.append(f"{k} = ${idx}")
            idx += 1
    query = f"""
            UPDATE {table} 
            SET en = false 
            {",dtime = (now() at time zone 'utc')" if with_dtime is True else ""} 
            {"WHERE " + " AND ".join(wheres) if wheres else ""}
            RETURNING *
            """
    try:
        return await conn.fetchrow(
            query,
            *values
        )
    except:
        logger.exception(f'Query {query} failed')
        raise


async def delete_by_where(
        table: str,
        pk: int,
        conn: Connection,
        data: Optional[Dict[str, Any]] = None,

) -> Optional[asyncpg.Record]:
    values = [pk]
    wheres = [f"id = $1"]
    idx = 2
    if data:
        for k in data:
            values.append(data[k])
            wheres.append(f"{k} = ${idx}")
            idx += 1
    query = f"""
            DELETE FROM {table} 
            {"WHERE " + " AND ".join(wheres) if wheres else ""}
            RETURNING *
            """
    try:
        return await conn.fetchrow(
            query,
            *values
        )
    except:
        logger.exception(f'Query {query} failed')
        raise

