"""
================================================================================
Module:     app/storage/exceptions.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Centrale exceptions voor filesystem-, database- en storageproblemen.
            Voorkomt dat ruwe sqlite3-/filesystemfouten rechtstreeks naar hogere
            applicatielagen hoeven door te lekken.

Wijzigingen:
  v1.0.0 (2026-10-01)  Formele projectheader toegevoegd; bestaande exception-
                        hiërarchie ongewijzigd behouden.
================================================================================
"""


class StorageError(Exception):
    """Basisklasse voor alle storage-gerelateerde fouten."""


class StorageInitializationError(StorageError):
    """Initialisatie van storage of runtime-paden is niet mogelijk."""


class DatabaseOpenError(StorageError):
    """SQLite-database kan niet veilig worden geopend."""


class InvalidDatabaseSchemaError(StorageError):
    """Database bevat geen geldig of herkenbaar applicatieschema."""


class UnsupportedSchemaVersionError(StorageError):
    """Database gebruikt een nieuwere niet-ondersteunde schemaversie."""


class MigrationError(StorageError):
    """Een databaseschemamigratie is mislukt."""


class StorageValidationError(StorageError):
    """Input voor de storage-laag is structureel ongeldig."""


class RelatedRecordNotFoundError(StorageError):
    """Een vereiste gerelateerde database-record bestaat niet."""


class StorageIntegrityError(StorageError):
    """Een relationele of database-integriteitsregel is geschonden."""


class StoredDataFormatError(StorageError):
    """Opgeslagen gegevens hebben een ongeldig of onverwacht formaat."""
