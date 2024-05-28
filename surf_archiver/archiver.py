import asyncio
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor
from contextlib import AsyncExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator

from .file import ExperimentFileSystem, get_temp_dir, managed_file_system
from .utils import Date, tar

LOGGER = logging.getLogger(__name__)


@dataclass
class Archive:

    path: str
    src_keys: list[str]


class AbstractArchiver(ABC):

    @abstractmethod
    async def archive(self, date_: Date, target_dir: Path) -> list[Archive]: ...


class AbstractManagedArchiver(ABC):

    @abstractmethod
    async def __aenter__(self) -> AbstractArchiver: ...

    @abstractmethod
    async def __aexit__(self, *args) -> None: ...


class Archiver(AbstractArchiver):

    def __init__(
        self,
        file_system: ExperimentFileSystem,
        pool: ProcessPoolExecutor,
    ):
        self.file_system = file_system
        self.pool = pool

    async def archive(self, date_: Date, target_dir: Path) -> list[Archive]:
        LOGGER.info("Starting archiving for %s", date_.isoformat())

        archives: list[Archive] = []
        async for archive in self._task_iterator(date_, target_dir):
            archives.append(archive)

        LOGGER.info("Archiving complete")

        return archives

    async def _task_iterator(
        self,
        date_: Date,
        target_dir: Path,
    ) -> AsyncGenerator[Archive, None]:
        grouped_files = await self.file_system.list_files_by_date(date_)

        experiment_count = len(grouped_files)
        LOGGER.info("Archiving %i experiments", experiment_count)

        for index, (experiment_id, files) in enumerate(grouped_files.items(), start=1):
            LOGGER.info("Archiving %s (%i/%i)", experiment_id, index, experiment_count)

            experiment_target_dir = target_dir / experiment_id / f"{date_}.tar"
            if experiment_target_dir.exists():
                LOGGER.info("Skipping %s: Already exists", experiment_id)
                continue

            with get_temp_dir() as temp_dir:
                await self.file_system.get_files(files, temp_dir)
                await self._tar(temp_dir, experiment_target_dir)

            yield Archive(
                path=str(experiment_target_dir.relative_to(target_dir)),
                src_keys=files,
            )

    async def _tar(self, src_dir: Path, target_dir: Path):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.pool, tar, src_dir, target_dir)


class ManagedArchiver:

    stack: AsyncExitStack

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name

    async def __aenter__(self) -> Archiver:

        self.stack = await AsyncExitStack().__aenter__()

        s3 = await self.stack.enter_async_context(managed_file_system())
        pool = self.stack.enter_context(ProcessPoolExecutor())

        return Archiver(
            file_system=ExperimentFileSystem(s3, self.bucket_name),
            pool=pool,
        )

    async def __aexit__(self, *args):
        await self.stack.aclose()
