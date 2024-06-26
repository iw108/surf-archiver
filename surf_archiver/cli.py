import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import typer

from .config import DEFAULT_CONFIG_PATH, get_config
from .log import configure_logging
from .main import amain
from .utils import Date

LOGGER = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def now():
    typer.echo(datetime.now().isoformat())


@app.command()
def archive(
    date: datetime,
    job_id: Annotated[UUID, typer.Argument(default_factory=uuid4)],
    config_path: Path = DEFAULT_CONFIG_PATH,
):
    config = get_config(config_path)
    if config.log_file:
        configure_logging(job_id, file=config.log_file)

    try:
        asyncio.run(amain(Date(date), job_id, config))
    except Exception as err:
        LOGGER.exception(err, stack_info=True)
        raise typer.Exit(code=1)
