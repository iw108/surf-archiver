from datetime import date
from unittest.mock import AsyncMock

import pytest

from surf_archiver.archiver import ArchiveEntry, Archiver
from surf_archiver.file import ArchiveFileSystem, ExperimentFileSystem


@pytest.fixture()
def experiment_file_system() -> ExperimentFileSystem:

    file_system = AsyncMock(ExperimentFileSystem)
    file_system.list_files_by_date.return_value = {
        "test-id": ["test-bucket/test-id/20000101_0000.tar"],
    }
    return file_system


async def test_new_files_are_archived(experiment_file_system: ExperimentFileSystem):
    archive_file_system = AsyncMock(ArchiveFileSystem)
    archive_file_system.exists.return_value = False

    archiver = Archiver(experiment_file_system, archive_file_system)

    expected = [
        ArchiveEntry(
            path="test-id/2000-01-01.tar",
            src_keys=["test-bucket/test-id/20000101_0000.tar"],
        )
    ]

    archives = await archiver.archive(date(2000, 1, 1))

    assert archives == expected


async def test_already_archived_files_are_skipped(
    experiment_file_system: ExperimentFileSystem,
):
    archive_file_system = AsyncMock(ArchiveFileSystem)
    archive_file_system.exists.return_value = True

    archiver = Archiver(experiment_file_system, archive_file_system)

    archives = await archiver.archive(date(2000, 1, 1))
    assert not archives
