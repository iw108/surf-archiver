from datetime import date, datetime
from pathlib import Path
from tarfile import TarFile
from typing import Union


class Date:

    def __init__(self, date_: Union[date, datetime]):
        self.date = date_

    def __str__(self) -> str:
        return self.date.strftime("%Y%m%d")

    def isoformat(self) -> str:
        return self.date.isoformat()


def tar(src: Path, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    with TarFile.open(target, "w") as tar:
        tar.add(src, arcname=".")
