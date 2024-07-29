import asyncio
import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator

from .abc import AbstractArchiver, AbstractConfig, AbstractManagedArchiver, ArchiveEntry
from .file import ArchiveFileSystem, ExperimentFileSystem, managed_s3_file_system
from .utils import DateT

LOGGER = logging.getLogger(__name__)


class Archiver(AbstractArchiver):
    def __init__(
        self,
        experiment_file_system: ExperimentFileSystem,
        archive_file_system: ArchiveFileSystem,
    ):
        self.experiment_file_system = experiment_file_system
        self.archive_file_system = archive_file_system

    async def archive(self, date: DateT) -> list[ArchiveEntry]:
        LOGGER.info("Starting archiving for %s", date.isoformat())

        archives: list[ArchiveEntry] = []
        async for archive in self._archive_iterator(date):
            archives.append(archive)

        LOGGER.info("Archiving complete")

        return archives

    async def _archive_iterator(
        self,
        date: DateT,
    ) -> AsyncGenerator[ArchiveEntry, None]:
        grouped_files = await self.experiment_file_system.list_files_by_date(date)
        experiment_count = len(grouped_files)
        LOGGER.info("Archiving %i experiments", experiment_count)

        tar_name = date.strftime("%Y-%m-%d.tar")
        for index, (experiment_id, files) in enumerate(grouped_files.items(), start=1):
            LOGGER.info("Archiving %s (%i/%i)", experiment_id, index, experiment_count)

            path = Path(experiment_id, tar_name)
            if self.archive_file_system.exists(path):
                LOGGER.info("Skipping %s: Already exists", experiment_id)
                continue

            with self.archive_file_system.get_temp_dir() as temp_dir:
                await self.experiment_file_system.get_files(files, temp_dir.path)
                await self.archive_file_system.add(temp_dir, path)

                await asyncio.gather(
                    *[self.experiment_file_system.tag(file) for file in files],
                )

            yield ArchiveEntry(path=str(path), src_keys=files)


@dataclass
class ArchiverConfig(AbstractConfig):
    bucket_name: str
    base_path: Path


class ManagedArchiver(AbstractManagedArchiver[ArchiverConfig]):
    stack: AsyncExitStack

    async def __aenter__(self) -> Archiver:
        self.stack = await AsyncExitStack().__aenter__()
        s3 = await self.stack.enter_async_context(managed_s3_file_system())

        return Archiver(
            experiment_file_system=ExperimentFileSystem(s3, self.config.bucket_name),
            archive_file_system=ArchiveFileSystem(self.config.base_path),
        )

    async def __aexit__(self, *args):
        await self.stack.aclose()
