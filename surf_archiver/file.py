from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import AsyncGenerator, Generator

from s3fs import S3FileSystem

from .utils import Date


@contextmanager
def get_temp_dir() -> Generator[Path, None, None]:
    with TemporaryDirectory() as _temp_path:
        yield Path(_temp_path)


@asynccontextmanager
async def managed_file_system() -> AsyncGenerator[S3FileSystem, None]:
    s3 = S3FileSystem(asynchronous=True)

    session = await s3.set_session()

    yield s3

    await session.close()


class ExperimentFileSystem:

    def __init__(
        self,
        s3: S3FileSystem,
        bucket_name: str,
    ):
        self.s3 = s3
        self.bucket_name = bucket_name
        self.batch_size = -1

    async def list_files_by_date(self, date_: Date) -> dict[str, list[str]]:
        files = await self.s3._glob(f"{self.bucket_name}/*/{date_}*.tar")
        return self._group_files(files)

    async def get_files(self, files: list[str], target_dir: Path):
        await self.s3._get(files, f"{target_dir}/", batch_size=self.batch_size)

    @staticmethod
    def _group_files(files: list[str]) -> dict[str, list[str]]:
        data: dict[str, list[str]] = defaultdict(list)
        for file_obj, file in zip(map(Path, files), files):
            data[file_obj.parent.name].append(file)
        return data
