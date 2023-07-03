from fastapi import Depends
from misc.session import Session
from misc.fastapi.depends.session import get as get_session
from misc.handlers import UnauthenticatedException


async def check_auth(
        session: Session = Depends(get_session)
):
    if not session.user.is_authenticated:
        raise UnauthenticatedException()
