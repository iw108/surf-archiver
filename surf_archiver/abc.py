from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from .utils import DateT

ConfigT = TypeVar("ConfigT", bound="AbstractConfig")


@dataclass
class AbstractConfig:
    pass


@dataclass
class ArchiveEntry:
    path: str
    src_keys: list[str]


class AbstractArchiver(ABC):
    @abstractmethod
    async def archive(self, date: DateT, *, tag: bool = True) -> list[ArchiveEntry]: ...


class AbstractManagedArchiver(Generic[ConfigT], ABC):
    def __init__(self, config: ConfigT):
        self.config = config

    @abstractmethod
    async def __aenter__(self) -> AbstractArchiver: ...

    @abstractmethod
    async def __aexit__(self, *args) -> None: ...
