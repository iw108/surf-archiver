from dataclasses import dataclass
from typing import TypeVar

ConfigT = TypeVar("ConfigT", bound="AbstractConfig")


@dataclass
class AbstractConfig:
    pass
