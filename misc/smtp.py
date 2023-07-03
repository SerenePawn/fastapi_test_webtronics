import re
import logging
from typing import Union

import aiosmtplib
from fastapi import Depends

from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class SMTP(object):
    def __init__(self, config):
        super().__init__()
        self._config = config

    @property
    def smtp_config(self):
        return self._config['transport']

    @property
    def sender(self):
        self._config['sender']

    async def send(self, message):
        if 'from' not in message:
            message['from'] = self.sender

        conn = aiosmtplib.SMTP(
            **self.smtp_config
        )

        await conn.connect()
        res = await conn.send_message(message)
        await conn.quit()
        return res


async def init(config: dict) -> SMTP:
    smtp = SMTP(config)
    return smtp


async def send(
        smtp: SMTP,
        message: Union[EmailMessage, MIMEMultipart]
):
    return await smtp.send(message)
