import threading
from io import BytesIO
from pathlib import Path
from typing import Generator
from uuid import uuid4

import pytest
from httpx import Client
from typer.testing import CliRunner

from surf_archiver.cli import app
from surf_archiver.config import Config
from surf_archiver.test_utils import MessageWaiter, Subscriber, SubscriberConfig


@pytest.fixture()
def random_str() -> str:
    return uuid4().hex


@pytest.fixture()
def message_waiter(random_str: str) -> Generator[MessageWaiter, None, None]:

    def _target(message_waiter: MessageWaiter):
        config = SubscriberConfig(
            connection_url="amqp://guest:guest@localhost:5671",
            exchange=random_str,
        )
        Subscriber(config).consume(message_waiter, timeout=5)

    message_waiter = MessageWaiter()

    thread = threading.Thread(target=_target, args=(message_waiter,))

    thread.start()

    yield message_waiter

    thread.join()


@pytest.fixture()
def object_store_data(random_str: str):
    bucket_url = f"http://localhost:9091/{random_str}"
    file_url = f"{bucket_url}/test-id/20000101_0000.tar"

    with Client() as client:
        client.put(bucket_url)
        client.put(file_url, files={"upload-file": BytesIO(b"test")})

        yield

        client.delete(file_url)
        client.delete(bucket_url)


@pytest.fixture()
def config(random_str: str, tmp_path: Path) -> Config:
    return Config(
        target_dir=tmp_path,
        connection_url="amqp://guest:guest@localhost:5671",
        bucket=random_str,
        exchange_name=random_str,
        log_file=tmp_path / "test.log",
    )


@pytest.fixture()
def config_file(config: Config, tmp_path: Path) -> Path:

    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config_file = config_dir / "config.yaml"
    config_file.write_text(config.model_dump_json())

    return config_file


@pytest.fixture()
def runner() -> CliRunner:
    env = {
        "AWS_ACCESS_KEY_ID": "aws-access-key-id",
        "AWS_SECRET_ACCESS_KEY": "aws-access-key-id",
        "AWS_ENDPOINT_URL": "http://localhost:9091",
    }
    return CliRunner(env=env)


@pytest.mark.usefixtures("object_store_data")
def test_app(
    runner: CliRunner,
    config_file: Path,
    config: Config,
    message_waiter: MessageWaiter,
):
    cmd = ["archive", "2000-01-01", "--config-path", str(config_file)]
    result = runner.invoke(app, cmd)

    assert result.exit_code == 0

    assert config.log_file and config.log_file.exists()
    assert (config.target_dir / "test-id" / "20000101.tar").exists()

    message_waiter.wait()
    assert message_waiter.message
