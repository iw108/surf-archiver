from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Union
from uuid import UUID

from .archiver import Archive, ManagedArchiver
from .publisher import BaseMessage, ManagedPublisher
from .utils import Date


@dataclass
class Config:
    target_dir: Path
    connection_url: str
    bucket_name: str


class Payload(BaseMessage):

    job_id: UUID
    date: Union[date, datetime]
    archives: list[Archive]


async def amain(date_: Date, job_id: UUID, config: Config):
    async with ManagedArchiver(config.bucket_name) as archiver:
        archives = await archiver.archive(date_, config.target_dir)
        payload = Payload(
            job_id=job_id,
            date=date_.date,
            archives=archives,
        )
        async with ManagedPublisher(config.connection_url) as publisher:
            await publisher.publish(payload)
