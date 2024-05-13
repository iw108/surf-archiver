import logging
from datetime import date, datetime
from typing import Union
from uuid import UUID

from .archiver import Archive, ManagedArchiver
from .config import Config
from .publisher import BaseMessage, ManagedPublisher
from .utils import Date

LOGGER = logging.getLogger(__name__)


class Payload(BaseMessage):

    job_id: UUID
    date: Union[date, datetime]
    archives: list[Archive]


async def amain(date_: Date, job_id: UUID, config: Config):
    async with ManagedArchiver(config.bucket) as archiver:
        archives = await archiver.archive(date_, config.target_dir)
        payload = Payload(
            job_id=job_id,
            date=date_.date,
            archives=archives,
        )
        async with ManagedPublisher(config.connection_url) as publisher:
            await publisher.publish(payload)
