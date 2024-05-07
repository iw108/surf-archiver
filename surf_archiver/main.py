from dataclasses import asdict, dataclass
from pathlib import Path

from .archiver import ManagedArchiver
from .publisher import ManagedPublisher
from .utils import Date


@dataclass
class Config:
    connection_url: str
    bucket_name: str


async def amain(date_: Date, target_dir: Path, config: Config):
    async with ManagedArchiver(config.bucket_name) as archiver:
        result = await archiver.archive(date_, target_dir)
        async with ManagedPublisher(config.connection_url) as publisher:
            await publisher.publish({"data": asdict(result)})
