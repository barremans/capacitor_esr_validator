"""
================================================================================
Module:     app/storage/paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Bepaalt uitsluitend waar mutable applicatiedata wordt opgeslagen.

            Productie:
                %LOCALAPPDATA%\\ElectronicsDiagnosticToolHub\\

            Test:
                een expliciete base_dir kan worden geïnjecteerd.

            Deze service:
            - maakt runtime-directories aan wanneer expliciet gevraagd;
            - maakt nooit zelf de SQLite-database aan;
            - bevat geen SQL;
            - bevat geen GUI-code;
            - schrijft niet naar Program Files;
            - gebruikt geen Documents/Desktop-fallback.

Wijzigingen:
  v1.0.0 (2026-10-01)  Formele projectheader toegevoegd; bewezen PathService-
                        functionaliteit ongewijzigd behouden.
================================================================================
"""

from __future__ import annotations

import os
from pathlib import Path

from .exceptions import StorageInitializationError


APP_DATA_DIRECTORY_NAME = "ElectronicsDiagnosticToolHub"
DATABASE_FILENAME = "measurements.sqlite3"


class PathService:
    """
    Bepaalt de writable runtime-paden van de applicatie.

    Bij productiegebruik wordt ``LOCALAPPDATA`` gebruikt.

    Voor tests kan een expliciete ``base_dir`` worden opgegeven.
    Die directory wordt dan rechtstreeks als ``user_root`` gebruikt,
    zodat tests volledig geïsoleerd blijven van echte gebruikersdata.
    """

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir is not None:
            self._user_root = Path(base_dir)
            return

        local_app_data = os.environ.get("LOCALAPPDATA")

        if not local_app_data or not local_app_data.strip():
            raise StorageInitializationError(
                "LOCALAPPDATA is niet beschikbaar; "
                "het runtime-datapad kan niet veilig worden bepaald."
            )

        self._user_root = (
            Path(local_app_data)
            / APP_DATA_DIRECTORY_NAME
        )

    @property
    def user_root(self) -> Path:
        """Rootdirectory voor mutable per-user applicatiedata."""
        return self._user_root

    @property
    def data_dir(self) -> Path:
        """Directory voor persistente applicatiedata."""
        return self.user_root / "data"

    @property
    def database_path(self) -> Path:
        """Pad van de SQLite-meetdatabase."""
        return self.data_dir / DATABASE_FILENAME

    @property
    def config_dir(self) -> Path:
        """Directory voor mutable configuratie."""
        return self.user_root / "config"

    @property
    def logs_dir(self) -> Path:
        """Directory voor applicatielogs."""
        return self.user_root / "logs"

    @property
    def cache_dir(self) -> Path:
        """Directory voor tijdelijke/cachegegevens."""
        return self.user_root / "cache"

    def ensure_runtime_directories(self) -> None:
        """
        Maak de vereiste runtime-directories aan.

        Deze methode maakt bewust geen SQLite-databasebestand aan.
        Database-initialisatie behoort tot de database/storage-laag.
        """
        directories = (
            self.user_root,
            self.data_dir,
            self.config_dir,
            self.logs_dir,
            self.cache_dir,
        )

        try:
            for directory in directories:
                directory.mkdir(
                    parents=True,
                    exist_ok=True,
                )
        except OSError as exc:
            raise StorageInitializationError(
                "De runtime-directories konden niet worden aangemaakt."
            ) from exc
