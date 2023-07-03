import asyncio
from asyncio.queues import Queue
from fastapi import FastAPI
from misc import db, redis


class State(object):
    def __init__(self, loop: asyncio.BaseEventLoop, config: dict):
        super().__init__()
        self.loop: asyncio.BaseEventLoop = loop
        self.config: dict = config
        self.db_pool: db.Connection = None
        self.redis_pool: redis.Connection = None
        self.app: FastAPI = None
        self.template_queue: Queue = Queue()
        self.template_processing: asyncio.Task = None
