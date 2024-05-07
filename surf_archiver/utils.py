import asyncio
from concurrent.futures import Executor
from datetime import date, datetime
from pathlib import Path
from tarfile import TarFile


class Date:

    def __init__(self, date_: date | datetime):
        self.date = date_

    def __str__(self) -> str:
        return self.date.strftime("%Y%m%d")


def tar(src: Path, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    with TarFile.open(target, "w") as tar:
        tar.add(src, arcname=".")


async def atar(src: Path, target: Path, executor: Executor):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, tar, src, target)
