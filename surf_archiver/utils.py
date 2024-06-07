from datetime import date, datetime
from typing import Union


class Date:

    def __init__(self, date_: Union[date, datetime]):
        self.date = date_

    def __str__(self) -> str:
        return self.date.strftime("%Y%m%d")

    def isoformat(self) -> str:
        return self.date.isoformat()
