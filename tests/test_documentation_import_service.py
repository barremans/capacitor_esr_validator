"""
================================================================================
Module:     tests/test_documentation_import_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.1
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Regressietests voor ImportService: registratie, statusmachine,
            JSON-persistentie, corrupte catalogus, schema_version,
            atomair schrijven, duplicate-detectie, replace_source en de
            beste-match-prioriteit (ACTIEF > CONCEPT > GEARCHIVEERD).
            Sinds v1.2.0 ook metadata-uitbreiding (5D'.2b) en de
            sentinel-logica van replace_source.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.0.1 (2026-10-06)  Qt-onafhankelijkheid niet meer via sys.modules-
                        manipulatie. Vervangen door statische broncheck.
  v1.1.0 (2026-10-07)  Tests voor find_by_file_hash, find_by_source_url en
                        replace_source (fase 5D'.2a).
  v1.1.1 (2026-10-07)  Tests voor beste-match-prioriteit: ACTIEF >
                        CONCEPT > GEARCHIVEERD, dan meest recente.
  v1.2.0 (2026-10-07)  Metadata-uitbreiding (5D'.2b): register_* met
                        metadata, replace_source met sentinel,
                        persistentie van metadata, backward-compat.
  v1.2.1 (2026-10-09)  Fix flakiness: test_find_by_file_hash_gelijke_status_
                        kiest_recentste en test_find_by_source_url_gelijke_
                        status_kiest_recentste registreerden twee bronnen
                        binnen dezelfde milliseconde, waardoor imported_at
                        gelijk was en de sortering niet-deterministisch.
                        time.sleep(0.01) tussen de registraties maakt de
                        tests deterministisch. Geen productiecodewijziging.
  v1.3.0 — register_docx en register_xlsx (fase 6A)                      
================================================================================
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from app.documentation.import_models import (
    ImportSourceType,
    ImportStatus,
    ImportValidationError,
)
from app.documentation.import_service import (
    CATALOG_SCHEMA_VERSION,
    ImportService,
)


@pytest.fixture()
def service(tmp_path):
    return ImportService(catalog_path=tmp_path / "imported_catalog.json")


def _lees_catalogus(pad):
    return json.loads(pad.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- registratie

def test_register_pdf_maakt_concept(service):
    result = service.register_pdf(
        title="FR-serie", original_filename="fr.pdf"
    )
    assert result.changed is True
    assert result.source.source_type is ImportSourceType.PDF
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.original_filename == "fr.pdf"


def test_register_url_maakt_concept(service):
    result = service.register_url(
        title="Fabrikant", source_url="https://example.com"
    )
    assert result.source.source_type is ImportSourceType.URL
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.source_url == "https://example.com"


def test_register_pdf_zonder_titel_faalt(service):
    with pytest.raises(ImportValidationError):
        service.register_pdf(title="", original_filename="x.pdf")


def test_register_url_zonder_url_faalt(service):
    with pytest.raises(ImportValidationError):
        service.register_url(title="x", source_url="")


# ---------------------------------------------------------------- persistentie

def test_catalogus_wordt_aangemaakt_met_schema_version(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    service = ImportService(catalog_path=pad)
    service.register_pdf(title="A", original_filename="a.pdf")
    data = _lees_catalogus(pad)
    assert data["schema_version"] == CATALOG_SCHEMA_VERSION
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) == 1


def test_meerdere_registraties_blijven_bewaard(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    service = ImportService(catalog_path=pad)
    service.register_pdf(title="A", original_filename="a.pdf")
    service.register_url(title="B", source_url="https://example.com")
    items = service.list_sources()
    assert len(items) == 2
    assert {i.source_type for i in items} == {
        ImportSourceType.PDF,
        ImportSourceType.URL,
    }


def test_ontbrekend_bestand_geeft_lege_lijst(tmp_path):
    service = ImportService(catalog_path=tmp_path / "bestaat_niet.json")
    assert service.list_sources() == []


def test_corrupte_json_faalt_zonder_reset(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    pad.write_text("{ dit is geen geldige json", encoding="utf-8")
    service = ImportService(catalog_path=pad)
    with pytest.raises(ImportValidationError):
        service.list_sources()
    # Bestand mag niet stil zijn gereset
    assert pad.read_text(encoding="utf-8").startswith("{ dit is geen geldige")


def test_verkeerde_schema_version_faalt(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    pad.write_text(
        json.dumps({"schema_version": 999, "sources": []}),
        encoding="utf-8",
    )
    service = ImportService(catalog_path=pad)
    with pytest.raises(ImportValidationError):
        service.list_sources()


def test_sources_moet_lijst_zijn(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    pad.write_text(
        json.dumps({"schema_version": CATALOG_SCHEMA_VERSION, "sources": {}}),
        encoding="utf-8",
    )
    service = ImportService(catalog_path=pad)
    with pytest.raises(ImportValidationError):
        service.list_sources()


# ---------------------------------------------------------------- get

def test_get_onbekende_id_faalt(service):
    with pytest.raises(ImportValidationError):
        service.get("bestaat-niet")


def test_get_bestaande_id(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    hersteld = service.get(result.source.source_id)
    assert hersteld == result.source


# ---------------------------------------------------------------- statusmachine

def test_status_concept_naar_actief(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    updated = service.set_status(result.source.source_id, ImportStatus.ACTIEF)
    assert updated.source.status is ImportStatus.ACTIEF


def test_status_ongeldige_overgang_faalt(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    service.set_status(result.source.source_id, ImportStatus.GEARCHIVEERD)
    with pytest.raises(ImportValidationError):
        service.set_status(result.source.source_id, ImportStatus.ACTIEF)


def test_revoke_gaat_terug_naar_concept_en_behoudt_bron(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    service.set_status(result.source.source_id, ImportStatus.ACTIEF)
    terug = service.revoke(result.source.source_id)
    assert terug.source.status is ImportStatus.CONCEPT
    # Bron blijft bestaan
    assert service.get(result.source.source_id).status is ImportStatus.CONCEPT


def test_archive_behoudt_bron(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    gearchiveerd = service.archive(result.source.source_id)
    assert gearchiveerd.source.status is ImportStatus.GEARCHIVEERD
    # Nog steeds opvraagbaar
    assert service.get(result.source.source_id).status is ImportStatus.GEARCHIVEERD


def test_set_status_onbekende_id_faalt(service):
    with pytest.raises(ImportValidationError):
        service.set_status("bestaat-niet", ImportStatus.ACTIEF)


# ---------------------------------------------------------------- opnieuw importeren

def test_opnieuw_importeren_geeft_nieuwe_id_en_behoudt_oude(service):
    eerste = service.register_pdf(title="A", original_filename="a.pdf")
    tweede = service.register_pdf(title="A", original_filename="a.pdf")
    assert eerste.source.source_id != tweede.source.source_id
    items = service.list_sources()
    assert len(items) == 2


# ---------------------------------------------------------------- list filter

def test_list_sources_filter_op_status(service):
    a = service.register_pdf(title="A", original_filename="a.pdf")
    b = service.register_pdf(title="B", original_filename="b.pdf")
    service.set_status(b.source.source_id, ImportStatus.ACTIEF)

    concepten = service.list_sources(status=ImportStatus.CONCEPT)
    actief = service.list_sources(status=ImportStatus.ACTIEF)
    assert [s.source_id for s in concepten] == [a.source.source_id]
    assert [s.source_id for s in actief] == [b.source.source_id]


def test_list_sources_ongeldige_status_faalt(service):
    with pytest.raises(ImportValidationError):
        service.list_sources(status="concept")  # type: ignore[arg-type]


# ---------------------------------------------------------------- geen Qt

def test_import_service_en_models_bevatten_geen_qt_import():
    """Bewijs dat de import-laag GUI-onafhankelijk is."""
    project_root = Path(__file__).resolve().parents[1]
    te_controleren = [
        project_root / "app" / "documentation" / "import_service.py",
        project_root / "app" / "documentation" / "import_models.py",
    ]
    verboden = ("PySide6", "PyQt5", "PyQt6", "PyQt")
    for pad in te_controleren:
        tekst = pad.read_text(encoding="utf-8")
        for token in verboden:
            assert token not in tekst, (
                f"{pad.name} bevat verboden Qt-import: {token}"
            )


# ============================================================================
# v1.1.0 — find_by_file_hash, find_by_source_url, replace_source
# ============================================================================

# ---------------------------------------------------------------- find_by_file_hash

def test_find_by_file_hash_geen_match(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    assert service.find_by_file_hash("def456") is None


def test_find_by_file_hash_match(service):
    r = service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == r.source.source_id


def test_find_by_file_hash_case_insensitive(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="ABC123"
    )
    assert service.find_by_file_hash("abc123") is not None
    assert service.find_by_file_hash("ABC123") is not None


def test_find_by_file_hash_strip_whitespace(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    assert service.find_by_file_hash("  abc123  ") is not None


def test_find_by_file_hash_lege_hash_geeft_none(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    assert service.find_by_file_hash("") is None
    assert service.find_by_file_hash("   ") is None


def test_find_by_file_hash_gearchiveerd_match(service):
    r = service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    service.archive(r.source.source_id)
    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.status is ImportStatus.GEARCHIVEERD


# ---------------------------------------------------------------- find_by_source_url

def test_find_by_source_url_geen_match(service):
    service.register_url(title="A", source_url="https://example.com")
    assert service.find_by_source_url("https://other.com") is None


def test_find_by_source_url_match(service):
    r = service.register_url(title="A", source_url="https://example.com")
    gevonden = service.find_by_source_url("https://example.com")
    assert gevonden is not None
    assert gevonden.source_id == r.source.source_id


def test_find_by_source_url_trailing_slash_genegeerd(service):
    service.register_url(title="A", source_url="https://example.com")
    assert service.find_by_source_url("https://example.com/") is not None


def test_find_by_source_url_lege_url_geeft_none(service):
    service.register_url(title="A", source_url="https://example.com")
    assert service.find_by_source_url("") is None
    assert service.find_by_source_url("   ") is None


def test_find_by_source_url_gearchiveerd_match(service):
    r = service.register_url(title="A", source_url="https://example.com")
    service.archive(r.source.source_id)
    gevonden = service.find_by_source_url("https://example.com")
    assert gevonden is not None
    assert gevonden.status is ImportStatus.GEARCHIVEERD


# ---------------------------------------------------------------- replace_source

def test_replace_source_wijzigt_velden(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes="nieuwe notitie",
    )
    assert result.changed is True
    assert result.source.source_id == r.source.source_id
    assert result.source.title == "Nieuw"
    assert result.source.file_hash == "hash_nieuw"
    assert result.source.original_filename == "nieuw.pdf"
    assert result.source.notes == "nieuwe notitie"
    assert result.source.imported_at == r.source.imported_at


def test_replace_source_behoudt_source_id_en_type(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
    )
    assert result.source.source_id == r.source.source_id
    assert result.source.source_type is ImportSourceType.PDF
    assert result.source.imported_by == r.source.imported_by


def test_replace_source_status_overschrijven_naar_concept(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    service.set_status(r.source.source_id, ImportStatus.ACTIEF)
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
        status=ImportStatus.CONCEPT,
    )
    assert result.source.status is ImportStatus.CONCEPT


def test_replace_source_zonder_status_behoudt_bestaande(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    service.set_status(r.source.source_id, ImportStatus.ACTIEF)
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
    )
    assert result.source.status is ImportStatus.ACTIEF


def test_replace_source_custom_imported_at(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    nieuw_ts = r.source.imported_at + 5000
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
        imported_at=nieuw_ts,
    )
    assert result.source.imported_at == nieuw_ts


def test_replace_source_onbekende_id_faalt(service):
    with pytest.raises(ImportValidationError):
        service.replace_source(
            "bestaat-niet",
            title="X",
            file_hash="y",
            original_filename="z.pdf",
            notes=None,
        )


def test_replace_source_persisteert_naar_disk(service, tmp_path):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
    )
    service2 = ImportService(catalog_path=service.catalog_path)
    terug = service2.get(r.source.source_id)
    assert terug.title == "Nieuw"
    assert terug.file_hash == "hash_nieuw"


def test_replace_source_url_behoudt_source_url(service):
    r = service.register_url(title="Oud", source_url="https://example.com")
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash=None,
        original_filename=None,
        notes="nieuw",
    )
    assert result.source.source_url == "https://example.com"


# ============================================================================
# v1.1.1 — beste match bij duplicate-detectie
# ============================================================================

def test_find_by_file_hash_kiest_actief_boven_gearchiveerd(service):
    """Bij meerdere matches met dezelfde hash: Actief wint van Gearchiveerd."""
    oud = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="abc123"
    )
    service.archive(oud.source.source_id)

    nieuw = service.register_pdf(
        title="Nieuw", original_filename="nieuw.pdf", file_hash="abc123"
    )
    service.set_status(nieuw.source.source_id, ImportStatus.ACTIEF)

    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == nieuw.source.source_id
    assert gevonden.status is ImportStatus.ACTIEF


def test_find_by_file_hash_kiest_concept_boven_gearchiveerd(service):
    """Concept wint van Gearchiveerd."""
    oud = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="abc123"
    )
    service.archive(oud.source.source_id)

    nieuw = service.register_pdf(
        title="Nieuw", original_filename="nieuw.pdf", file_hash="abc123"
    )

    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == nieuw.source.source_id
    assert gevonden.status is ImportStatus.CONCEPT


def test_find_by_file_hash_kiest_actief_boven_concept(service):
    """Actief wint van Concept."""
    eerste = service.register_pdf(
        title="Eerste", original_filename="eerste.pdf", file_hash="abc123"
    )
    service.set_status(eerste.source.source_id, ImportStatus.ACTIEF)

    service.register_pdf(
        title="Tweede", original_filename="tweede.pdf", file_hash="abc123"
    )

    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == eerste.source.source_id
    assert gevonden.status is ImportStatus.ACTIEF


def test_find_by_file_hash_gelijke_status_kiest_recentste(service):
    """Bij gelijke status: hoogste imported_at (meest recente).

    De kleine slaap garandeert dat imported_at verschilt; zonder die slaap
    kunnen beide registraties binnen dezelfde milliseconde vallen en is
    de sortering niet-deterministisch.
    """
    service.register_pdf(
        title="Eerste", original_filename="eerste.pdf", file_hash="abc123"
    )
    time.sleep(0.01)
    tweede = service.register_pdf(
        title="Tweede", original_filename="tweede.pdf", file_hash="abc123"
    )

    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == tweede.source.source_id


def test_find_by_source_url_kiest_actief_boven_gearchiveerd(service):
    """Bij meerdere URL-matches: Actief wint van Gearchiveerd."""
    oud = service.register_url(title="Oud", source_url="https://example.com")
    service.archive(oud.source.source_id)

    nieuw = service.register_url(
        title="Nieuw", source_url="https://example.com"
    )
    service.set_status(nieuw.source.source_id, ImportStatus.ACTIEF)

    gevonden = service.find_by_source_url("https://example.com")
    assert gevonden is not None
    assert gevonden.source_id == nieuw.source.source_id
    assert gevonden.status is ImportStatus.ACTIEF


def test_find_by_source_url_gelijke_status_kiest_recentste(service):
    """Bij gelijke status: hoogste imported_at.

    De kleine slaap garandeert dat imported_at verschilt; zonder die slaap
    kunnen beide registraties binnen dezelfde milliseconde vallen en is
    de sortering niet-deterministisch.
    """
    service.register_url(title="Eerste", source_url="https://example.com")
    time.sleep(0.01)
    tweede = service.register_url(
        title="Tweede", source_url="https://example.com"
    )

    gevonden = service.find_by_source_url("https://example.com")
    assert gevonden is not None
    assert gevonden.source_id == tweede.source.source_id


# ============================================================================
# v1.2.0 — metadata-uitbreiding (5D'.2b)
# ============================================================================

def test_register_pdf_met_metadata(service):
    result = service.register_pdf(
        title="FR-serie",
        original_filename="fr.pdf",
        category="DATASHEET",
        manufacturer="Panasonic",
        series="FR",
        part_number="FR-123",
        document_version="1.2",
        document_date="2024-01",
        notes="noot",
    )
    s = result.source
    assert s.category == "DATASHEET"
    assert s.manufacturer == "Panasonic"
    assert s.series == "FR"
    assert s.part_number == "FR-123"
    assert s.document_version == "1.2"
    assert s.document_date == "2024-01"
    assert s.notes == "noot"


def test_register_url_met_metadata(service):
    result = service.register_url(
        title="Fabrikant",
        source_url="https://example.com",
        category="MANUAL",
        manufacturer="TDK",
        series="C-series",
        part_number="C-456",
        document_version="2.0",
        document_date="2023-06",
    )
    s = result.source
    assert s.category == "MANUAL"
    assert s.manufacturer == "TDK"
    assert s.series == "C-series"
    assert s.part_number == "C-456"
    assert s.document_version == "2.0"
    assert s.document_date == "2023-06"


def test_register_zonder_metadata_geeft_none(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    s = result.source
    assert s.category is None
    assert s.manufacturer is None
    assert s.series is None
    assert s.part_number is None
    assert s.document_version is None
    assert s.document_date is None


def test_register_lege_metadata_wordt_none(service):
    result = service.register_pdf(
        title="A",
        original_filename="a.pdf",
        category="",
        manufacturer="   ",
        series="",
        part_number="",
        document_version="",
        document_date="",
    )
    s = result.source
    assert s.category is None
    assert s.manufacturer is None
    assert s.series is None
    assert s.part_number is None
    assert s.document_version is None
    assert s.document_date is None


def test_metadata_persisteert_naar_disk(service):
    result = service.register_pdf(
        title="A",
        original_filename="a.pdf",
        category="DATASHEET",
        manufacturer="Panasonic",
    )
    service2 = ImportService(catalog_path=service.catalog_path)
    terug = service2.get(result.source.source_id)
    assert terug.category == "DATASHEET"
    assert terug.manufacturer == "Panasonic"


def test_replace_source_met_metadata(service):
    r = service.register_pdf(title="Oud", original_filename="oud.pdf")
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash=None,
        original_filename="nieuw.pdf",
        notes=None,
        category="MANUAL",
        manufacturer="TDK",
        series="C-series",
        part_number="C-456",
        document_version="2.0",
        document_date="2023-06",
    )
    s = result.source
    assert s.category == "MANUAL"
    assert s.manufacturer == "TDK"
    assert s.series == "C-series"
    assert s.part_number == "C-456"
    assert s.document_version == "2.0"
    assert s.document_date == "2023-06"


def test_replace_source_metadata_sentinel_behoudt_bestaande(service):
    """Niet meegegeven metadata-parameter = bestaande waarde behouden."""
    r = service.register_pdf(
        title="Oud",
        original_filename="oud.pdf",
        category="DATASHEET",
        manufacturer="Panasonic",
        series="FR",
    )
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash=None,
        original_filename="nieuw.pdf",
        notes=None,
        # category, manufacturer, series niet meegegeven
    )
    assert result.source.category == "DATASHEET"
    assert result.source.manufacturer == "Panasonic"
    assert result.source.series == "FR"


def test_replace_source_metadata_expliciet_none_maakt_leeg(service):
    """Expliciet None meegeven = veld leegmaken."""
    r = service.register_pdf(
        title="Oud",
        original_filename="oud.pdf",
        category="DATASHEET",
        manufacturer="Panasonic",
    )
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash=None,
        original_filename="nieuw.pdf",
        notes=None,
        category=None,
        manufacturer=None,
    )
    assert result.source.category is None
    assert result.source.manufacturer is None


def test_replace_source_metadata_string_vervangt(service):
    r = service.register_pdf(
        title="Oud",
        original_filename="oud.pdf",
        category="DATASHEET",
        manufacturer="Panasonic",
    )
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash=None,
        original_filename="nieuw.pdf",
        notes=None,
        category="MANUAL",
        manufacturer="TDK",
    )
    assert result.source.category == "MANUAL"
    assert result.source.manufacturer == "TDK"


def test_replace_source_behoudt_metadata_bij_statuswijziging(service):
    """Een statuswijziging mag metadata niet wissen."""
    r = service.register_pdf(
        title="A",
        original_filename="a.pdf",
        category="DATASHEET",
        manufacturer="Panasonic",
        series="FR",
    )
    service.set_status(r.source.source_id, ImportStatus.ACTIEF)
    terug = service.get(r.source.source_id)
    assert terug.status is ImportStatus.ACTIEF
    assert terug.category == "DATASHEET"
    assert terug.manufacturer == "Panasonic"
    assert terug.series == "FR"


def test_catalogus_backward_compat_zonder_metadata(tmp_path):
    """Catalogus van vóór 5D'.2b blijft leesbaar."""
    pad = tmp_path / "imported_catalog.json"
    pad.write_text(
        json.dumps(
            {
                "schema_version": CATALOG_SCHEMA_VERSION,
                "sources": [
                    {
                        "source_id": "oud-1",
                        "source_type": "pdf",
                        "title": "Oud document",
                        "imported_at": 1_700_000_000_000,
                        "imported_by": "tester",
                        "status": "concept",
                        "original_filename": "oud.pdf",
                        "source_url": None,
                        "file_hash": "abc",
                        "notes": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    service = ImportService(catalog_path=pad)
    items = service.list_sources()
    assert len(items) == 1
    assert items[0].category is None
    assert items[0].manufacturer is None
    
# ============================================================================
# v1.3.0 — register_docx en register_xlsx (fase 6A)
# ============================================================================

def test_register_docx_maakt_concept(service):
    result = service.register_docx(
        title="Word-doc", original_filename="doc.docx"
    )
    assert result.changed is True
    assert result.source.source_type is ImportSourceType.DOCX
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.original_filename == "doc.docx"


def test_register_xlsx_maakt_concept(service):
    result = service.register_xlsx(
        title="Excel-werkmap", original_filename="doc.xlsx"
    )
    assert result.changed is True
    assert result.source.source_type is ImportSourceType.XLSX
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.original_filename == "doc.xlsx"


def test_register_docx_zonder_titel_faalt(service):
    with pytest.raises(ImportValidationError):
        service.register_docx(title="", original_filename="doc.docx")


def test_register_xlsx_zonder_titel_faalt(service):
    with pytest.raises(ImportValidationError):
        service.register_xlsx(title="", original_filename="doc.xlsx")


def test_register_docx_zonder_bestandsnaam_faalt(service):
    with pytest.raises(ImportValidationError):
        service.register_docx(title="Titel", original_filename="")


def test_register_xlsx_zonder_bestandsnaam_faalt(service):
    with pytest.raises(ImportValidationError):
        service.register_xlsx(title="Titel", original_filename="")


def test_register_docx_met_metadata(service):
    result = service.register_docx(
        title="Word-doc",
        original_filename="doc.docx",
        category="MANUAL",
        manufacturer="CHONG",
        series="CDX",
        part_number="CDX-1",
        document_version="V1.1",
        document_date="2026-10-09",
        notes="noot",
    )
    s = result.source
    assert s.category == "MANUAL"
    assert s.manufacturer == "CHONG"
    assert s.series == "CDX"
    assert s.part_number == "CDX-1"
    assert s.document_version == "V1.1"
    assert s.document_date == "2026-10-09"
    assert s.notes == "noot"


def test_register_xlsx_met_metadata(service):
    result = service.register_xlsx(
        title="Excel-werkmap",
        original_filename="doc.xlsx",
        category="REFERENCE_TABLE",
        manufacturer="TDK",
    )
    s = result.source
    assert s.category == "REFERENCE_TABLE"
    assert s.manufacturer == "TDK"


def test_docx_persisteert_naar_disk(service):
    result = service.register_docx(
        title="Word-doc", original_filename="doc.docx"
    )
    service2 = ImportService(catalog_path=service.catalog_path)
    terug = service2.get(result.source.source_id)
    assert terug.source_type is ImportSourceType.DOCX


def test_xlsx_persisteert_naar_disk(service):
    result = service.register_xlsx(
        title="Excel-werkmap", original_filename="doc.xlsx"
    )
    service2 = ImportService(catalog_path=service.catalog_path)
    terug = service2.get(result.source.source_id)
    assert terug.source_type is ImportSourceType.XLSX    