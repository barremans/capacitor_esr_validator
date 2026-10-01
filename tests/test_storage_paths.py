"""
================================================================================
Module:     tests/test_storage_paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Tests voor de Windows/runtime PathService.

            Controleert:
            - LOCALAPPDATA-resolutie;
            - expliciete test-base-dir;
            - vaste runtime-folderstructuur;
            - idempotente directory-initialisatie;
            - geen onbedoelde databasecreatie;
            - veilige fout bij ontbrekende LOCALAPPDATA.

Wijzigingen:
  v1.0.0 (2026-10-01)  Formele projectheader toegevoegd; bestaande bewezen
                        PathService-tests inhoudelijk ongewijzigd behouden.
================================================================================
"""

from pathlib import Path

import pytest

from app.storage.exceptions import StorageInitializationError
from app.storage.paths import (
    APP_DATA_DIRECTORY_NAME,
    DATABASE_FILENAME,
    PathService,
)


def test_default_root_uses_localappdata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        "LOCALAPPDATA",
        str(tmp_path),
    )

    paths = PathService()

    assert paths.user_root == (
        tmp_path / APP_DATA_DIRECTORY_NAME
    )


def test_explicit_base_dir_overrides_localappdata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_local_app_data = tmp_path / "real-localappdata"
    explicit_test_root = tmp_path / "isolated-test-root"

    monkeypatch.setenv(
        "LOCALAPPDATA",
        str(fake_local_app_data),
    )

    paths = PathService(
        base_dir=explicit_test_root,
    )

    assert paths.user_root == explicit_test_root


def test_expected_runtime_paths(
    tmp_path: Path,
) -> None:
    paths = PathService(
        base_dir=tmp_path,
    )

    assert paths.data_dir == tmp_path / "data"
    assert paths.config_dir == tmp_path / "config"
    assert paths.logs_dir == tmp_path / "logs"
    assert paths.cache_dir == tmp_path / "cache"

    assert paths.database_path == (
        tmp_path
        / "data"
        / DATABASE_FILENAME
    )


def test_ensure_runtime_directories_creates_all_directories(
    tmp_path: Path,
) -> None:
    root = tmp_path / "runtime"

    paths = PathService(
        base_dir=root,
    )

    assert not root.exists()

    paths.ensure_runtime_directories()

    assert paths.user_root.is_dir()
    assert paths.data_dir.is_dir()
    assert paths.config_dir.is_dir()
    assert paths.logs_dir.is_dir()
    assert paths.cache_dir.is_dir()


def test_ensure_runtime_directories_is_idempotent(
    tmp_path: Path,
) -> None:
    paths = PathService(
        base_dir=tmp_path / "runtime",
    )

    paths.ensure_runtime_directories()
    paths.ensure_runtime_directories()

    assert paths.user_root.is_dir()
    assert paths.data_dir.is_dir()
    assert paths.config_dir.is_dir()
    assert paths.logs_dir.is_dir()
    assert paths.cache_dir.is_dir()


def test_ensure_runtime_directories_does_not_create_database(
    tmp_path: Path,
) -> None:
    paths = PathService(
        base_dir=tmp_path / "runtime",
    )

    paths.ensure_runtime_directories()

    assert paths.data_dir.is_dir()
    assert not paths.database_path.exists()


def test_missing_localappdata_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "LOCALAPPDATA",
        raising=False,
    )

    with pytest.raises(
        StorageInitializationError,
        match="LOCALAPPDATA",
    ):
        PathService()


def test_blank_localappdata_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "LOCALAPPDATA",
        "   ",
    )

    with pytest.raises(
        StorageInitializationError,
        match="LOCALAPPDATA",
    ):
        PathService()
