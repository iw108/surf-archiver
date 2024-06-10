from datetime import date, datetime
from typing import Union

DateT = Union[date, datetime]


class Date:

    def __init__(self, date_: DateT):
        self.date = date_

    def __str__(self) -> str:
        return self.date.strftime("%Y%m%d")

    def isoformat(self) -> str:
        return self.date.isoformat()
