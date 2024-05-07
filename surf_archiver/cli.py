import asyncio
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from .main import Config, amain

DEFAULT_BUCKET_NAME = "prince-data-dev"
DEFAULT_DIR = Path.home() / "prince"
DEFAULT_CONNECTION_URL = "amqp://guest:guest@localhost"

BucketNameT = Annotated[str, typer.Option(envvar="SURF_ARCHIVER_BUCKET")]
TargetDirT = Annotated[Path, typer.Option(envvar="SURF_ARCHIVER_TARGET_DIR")]
ConnectionURL = Annotated[Path, typer.Option(envvar="SURF_ARCHIVER_CONNECTION_URL")]


app = typer.Typer()


@app.command()
def now():
    typer.echo(datetime.now().isoformat())


@app.command()
def archive(
    date: datetime,
    bucket_name: BucketNameT = DEFAULT_BUCKET_NAME,
    target_dir: TargetDirT = DEFAULT_DIR,
    connection_url: ConnectionURL = DEFAULT_CONNECTION_URL,
):
    config = Config(bucket_name=bucket_name, connection_url=connection_url)
    asyncio.run(amain(date, target_dir, config))
