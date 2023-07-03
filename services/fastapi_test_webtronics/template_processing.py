import asyncio
import logging
from misc import (
    db,
)
from asyncio import Queue

logger = logging.getLogger(__name__)


class State(object):
    def __init__(self, db_pool):
        super().__init__()
        self.stopping: bool = False
        self.queue: Queue = Queue()
        self.db_pool: db.Connection = db_pool
        self.task: asyncio.Task = asyncio.create_task(handler(self))


async def init(db_pool: db.Connection) -> State:
    state = State(db_pool)
    return state


async def close(state: State):
    state.stopping = True
    await state.queue.put(None)
    if state.task and not state.task.done():
        try:
            await asyncio.wait([state.task], timeout=10)
        except TimeoutError:
            logger.error('Template processing task not stopped')
        except asyncio.CancelledError:
            pass
        except:
            logger.exception('Processing task failed')


async def handle_template(id: int, instance: State) -> None:
    await instance.queue.put(id)


async def handler(state: State):
    logger.info('Template processing handler started')
    db_pool = state.db_pool
    queue = state.queue
    id = None
    while not state.stopping:
        try:
            id = await queue.get()
            if id is None:
                continue
        except (asyncio.CancelledError, GeneratorExit):
            logger.error(f'Template queue handler cancelled {id}')
            raise
        except (UnicodeDecodeError, UnicodeError, KeyError, SystemError, AttributeError, GeneratorExit):
            logger.exception('Template queue handler exception.')
        except Exception:
            logger.exception(f'Error!')
        queue.task_done()
        id = None
