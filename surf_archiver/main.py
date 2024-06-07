import logging
from contextlib import AsyncExitStack
from datetime import date, datetime
from typing import Union
from uuid import UUID

from .archiver import AbstractManagedArchiver, ArchiveEntry
from .publisher import AbstractManagedPublisher, BaseMessage
from .utils import Date

LOGGER = logging.getLogger(__name__)


class Payload(BaseMessage):

    job_id: UUID
    date: Union[date, datetime]
    archives: list[ArchiveEntry]


async def run_archiving(
    date_: Date,
    job_id: UUID,
    managed_achviver: AbstractManagedArchiver,
    managed_publisher: AbstractManagedPublisher,
):
    async with AsyncExitStack() as stack:
        archiver = await stack.enter_async_context(managed_achviver)
        publisher = await stack.enter_async_context(managed_publisher)

        archives = await archiver.archive(date_)

        payload = Payload(
            job_id=job_id,
            date=date_.date,
            archives=archives,
        )
        await publisher.publish(payload)
