import asyncio
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import typer

from .config import get_config
from .log import configure_logging
from .main import amain
from .utils import Date


DEFAULT_CONFIG_PATH = Path.home() / ".surf-archiver" / "config.yaml"


app = typer.Typer()


@app.command()
def now():
    typer.echo(datetime.now().isoformat())


@app.command()
def archive(
    date: datetime,
    job_id: Annotated[UUID, typer.Argument(default_factory=uuid4)],
    log_to_file: bool = True,
    config_path: Path = DEFAULT_CONFIG_PATH,
):
    if log_to_file:
        configure_logging(job_id)

    config = get_config(config_path)

    asyncio.run(amain(Date(date), job_id, config))
