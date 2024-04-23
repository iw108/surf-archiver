import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from .utils import run_archiving

app = typer.Typer()

DEFAULT_BUCKET_NAME = "prince-data-dev"
DEFAULT_DIR = Path.home() / "prince"

BucketNameT = Annotated[str, typer.Option(envvar="SURF_ARCHIVER_BUCKET")]
TargetDirT = Annotated[Path, typer.Option(envvar="SURF_ARCHIVER_TARGET_DIR")]


@app.command()
def now():
    typer.echo(datetime.now().isoformat())


@app.command()
def archive(
    date: datetime,
    bucket_name: BucketNameT = DEFAULT_BUCKET_NAME,
    target_dir: TargetDirT = DEFAULT_DIR,
):
    data = asyncio.run(run_archiving(date, bucket_name, target_dir))
    typer.echo(json.dumps(data, indent=4))
