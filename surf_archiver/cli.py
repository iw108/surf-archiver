import asyncio
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import typer

from .log import configure_logging
from .main import Config, amain
from .utils import Date

DEFAULT_BUCKET_NAME = "prince-data-dev"
DEFAULT_DIR = Path.home() / "prince"
DEFAULT_CONNECTION_URL = "amqp://guest:guest@localhost"

BucketNameT = Annotated[str, typer.Option(envvar="SURF_ARCHIVER_BUCKET")]
TargetDirT = Annotated[Path, typer.Option(envvar="SURF_ARCHIVER_TARGET_DIR")]
ConnectionURL = Annotated[str, typer.Option(envvar="SURF_ARCHIVER_CONNECTION_URL")]

app = typer.Typer()


@app.command()
def now():
    typer.echo(datetime.now().isoformat())


@app.command()
def archive(
    date: datetime,
    job_id: Annotated[UUID, typer.Argument(default_factory=uuid4)],
    bucket_name: BucketNameT = DEFAULT_BUCKET_NAME,
    target_dir: TargetDirT = DEFAULT_DIR,
    connection_url: ConnectionURL = DEFAULT_CONNECTION_URL,
    log_to_file: bool = True,
):
    if log_to_file:
        configure_logging(job_id)

    config = Config(
        bucket_name=bucket_name,
        connection_url=connection_url,
        target_dir=target_dir,
    )

    asyncio.run(amain(Date(date), job_id, config))
