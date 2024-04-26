import asyncio
from collections import defaultdict
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory
from typing import AsyncGenerator, Union

from s3fs import S3FileSystem


def tar(src: Path, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    with TarFile.open(target, "w") as tar:
        tar.add(src, arcname=".")


async def atar(src: Path, target: Path, executor: Executor):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, tar, src, target)


@asynccontextmanager
async def managed_file_system() -> AsyncGenerator[S3FileSystem, None]:
    s3 = S3FileSystem(asynchronous=True)

    session = await s3.set_session()

    yield s3

    await session.close()


def group_files(files: list[str]) -> dict[str, list[str]]:
    data: dict[str, list[str]] = defaultdict(list)
    for file_obj, file in zip(map(Path, files), files):
        data[file_obj.parent.name].append(file)
    return data


@dataclass
class Archive:

    path: str
    src_keys: list[str]


async def run_archiving(
    date_: Union[date, datetime],
    bucket_name: str,
    target_dir: Path,
) -> list[Archive]:
    date_str = date_.strftime("%Y%m%d")

    async with AsyncExitStack() as stack:
        temp_dir = Path(stack.enter_context(TemporaryDirectory()))
        pool = stack.enter_context(ProcessPoolExecutor())
        s3 = await stack.enter_async_context(managed_file_system())

        archives = []
        tar_futures = []

        grouped_files = group_files(await s3._glob(f"{bucket_name}/*/{date_str}*.tar"))
        for experiment_id, files in grouped_files.items():
            experiment_temp_dir = temp_dir / experiment_id
            experiment_target_dir = target_dir / experiment_id / f"{date_str}.tar"

            await s3._get(files, f"{experiment_temp_dir}/", batch_size=-1)
            tar_futures.append(
                asyncio.create_task(
                    atar(experiment_temp_dir, experiment_target_dir, pool),
                )
            )

            archives.append(
                Archive(
                    path=str(experiment_target_dir.relative_to(target_dir)), 
                    src_keys=files,
                )
            )

        await asyncio.gather(*tar_futures)

    return archives
