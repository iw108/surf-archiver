import asyncio
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import AsyncGenerator

from .file import ExperimentFileSystem, get_temp_dir, managed_file_system
from .utils import Date, atar


@dataclass
class Archive:

    path: str
    src_keys: list[str]


class AbstractArchiver(ABC):

    @abstractmethod
    def archive(self, date_: date, target_dir: Path) -> list[Archive]: ...


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
        archives: list[Archive] = []
        tar_futures: list[asyncio.Task] = []

        with get_temp_dir() as temp_dir:
            async for archive, task in self._task_iterator(date_, temp_dir, target_dir):
                archives.append(archive)
                tar_futures.append(task)

            await asyncio.gather(*tar_futures)

        return archives

    async def _task_iterator(
        self,
        date_: Date,
        temp_dir: Path,
        target_dir: Path,
    ) -> AsyncGenerator[tuple[Archive, asyncio.Task], None]:
        grouped_files = await self.file_system.list_files_by_date(date_)
        for experiment_id, files in grouped_files.items():
            experiment_temp_dir = temp_dir / experiment_id
            experiment_target_dir = target_dir / experiment_id / f"{date_}.tar"

            await self.file_system.get_files(files, experiment_temp_dir)

            archive = Archive(
                path=str(experiment_target_dir.relative_to(target_dir)),
                src_keys=files,
            )

            task = asyncio.create_task(
                atar(experiment_temp_dir, experiment_target_dir, self.pool),
            )

            yield archive, task


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
