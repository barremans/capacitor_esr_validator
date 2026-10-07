"""
================================================================================
Module:     tests/test_documentation_duplicate_check.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Regressietests voor duplicate_check: normalize_url,
            find_duplicate (PDF op file_hash, URL op genormaliseerde URL),
            foutpaden, en beste-match-prioriteit (ACTIEF > CONCEPT >
            GEARCHIVEERD).

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie.
  v1.0.1 (2026-10-07)  Tests voor beste-match-prioriteit toegevoegd
                        (fase 5D'.2a bugfix).
================================================================================
"""

from __future__ import annotations

import pytest

from app.documentation.duplicate_check import (
    find_duplicate,
    normalize_url,
)
from app.documentation.import_models import (
    ImportStatus,
    ImportValidationError,
)
from app.documentation.import_service import ImportService


@pytest.fixture()
def service(tmp_path):
    return ImportService(catalog_path=tmp_path / "cat.json")


# ------------------------------------------------------------------ normalize_url

@pytest.mark.parametrize(
    "invoer, verwacht",
    [
        ("https://example.com", "https://example.com"),
        ("  https://example.com  ", "https://example.com"),
        ("https://Example.COM", "https://example.com"),
        ("HTTPS://EXAMPLE.COM", "https://example.com"),
        ("https://example.com/", "https://example.com"),
        ("https://example.com/pad/", "https://example.com/pad"),
        ("https://example.com/pad#fragment", "https://example.com/pad"),
        (
            "https://example.com/pad?a=1#frag",
            "https://example.com/pad?a=1",
        ),
        ("https://example.com/Pad", "https://example.com/Pad"),  # case pad
        ("", ""),
        ("niet-een-url", "niet-een-url"),
    ],
)
def test_normalize_url(invoer, verwacht):
    assert normalize_url(invoer) == verwacht


def test_normalize_url_none_wordt_lege_string():
    assert normalize_url(None) == ""


# ------------------------------------------------------------------ validatie

def test_find_duplicate_zonder_argumenten_faalt(service):
    with pytest.raises(ImportValidationError):
        find_duplicate(service)


def test_find_duplicate_met_beide_argumenten_faalt(service):
    with pytest.raises(ImportValidationError):
        find_duplicate(
            service, file_hash="abc", source_url="https://example.com"
        )


def test_find_duplicate_met_lege_hash_geeft_none(service):
    assert find_duplicate(service, file_hash="") is None
    assert find_duplicate(service, file_hash="   ") is None


def test_find_duplicate_met_lege_url_geeft_none(service):
    assert find_duplicate(service, source_url="") is None
    assert find_duplicate(service, source_url="   ") is None


# ------------------------------------------------------------------ PDF-match

def test_find_duplicate_pdf_geen_match(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    assert find_duplicate(service, file_hash="def456") is None


def test_find_duplicate_pdf_match(service):
    r = service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    match = find_duplicate(service, file_hash="abc123")
    assert match is not None
    assert match.match_type == "file_hash"
    assert match.bestaande.source_id == r.source.source_id


def test_find_duplicate_pdf_hash_case_insensitive(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="ABC123"
    )
    match = find_duplicate(service, file_hash="abc123")
    assert match is not None
    assert match.match_type == "file_hash"


def test_find_duplicate_pdf_match_gearchiveerd(service):
    r = service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    service.archive(r.source.source_id)
    match = find_duplicate(service, file_hash="abc123")
    assert match is not None
    assert match.bestaande.status is ImportStatus.GEARCHIVEERD


# ------------------------------------------------------------------ URL-match

def test_find_duplicate_url_geen_match(service):
    service.register_url(title="A", source_url="https://example.com")
    assert find_duplicate(service, source_url="https://other.com") is None


def test_find_duplicate_url_match(service):
    r = service.register_url(title="A", source_url="https://example.com")
    match = find_duplicate(service, source_url="https://example.com")
    assert match is not None
    assert match.match_type == "source_url"
    assert match.bestaande.source_id == r.source.source_id


def test_find_duplicate_url_match_na_normalisatie(service):
    service.register_url(title="A", source_url="https://example.com")
    match = find_duplicate(service, source_url="HTTPS://Example.COM/")
    assert match is not None
    assert match.match_type == "source_url"


def test_find_duplicate_url_match_met_fragment(service):
    service.register_url(title="A", source_url="https://example.com/pad")
    match = find_duplicate(
        service, source_url="https://example.com/pad#sectie"
    )
    assert match is not None
    assert match.match_type == "source_url"


def test_find_duplicate_url_gearchiveerd(service):
    r = service.register_url(title="A", source_url="https://example.com")
    service.archive(r.source.source_id)
    match = find_duplicate(service, source_url="https://example.com")
    assert match is not None
    assert match.bestaande.status is ImportStatus.GEARCHIVEERD


def test_find_duplicate_url_mag_niet_pdf_zijn(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc"
    )
    match = find_duplicate(service, source_url="https://example.com")
    assert match is None


# ------------------------------------------------------------------ verkeerd type

def test_find_duplicate_met_verkeerd_service_type_faalt():
    with pytest.raises(ImportValidationError):
        find_duplicate("geen service", file_hash="abc")  # type: ignore[arg-type]


# ============================================================================
# v1.0.1 — beste match bij duplicate-detectie
# ============================================================================

def test_find_duplicate_kiest_actief_boven_gearchiveerd(service):
    """Bij meerdere PDF-matches: Actief wint van Gearchiveerd."""
    oud = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="abc123"
    )
    service.archive(oud.source.source_id)

    nieuw = service.register_pdf(
        title="Nieuw", original_filename="nieuw.pdf", file_hash="abc123"
    )
    service.set_status(nieuw.source.source_id, ImportStatus.ACTIEF)

    match = find_duplicate(service, file_hash="abc123")
    assert match is not None
    assert match.bestaande.source_id == nieuw.source.source_id
    assert match.bestaande.status is ImportStatus.ACTIEF


def test_find_duplicate_kiest_concept_boven_gearchiveerd(service):
    """Concept wint van Gearchiveerd."""
    oud = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="abc123"
    )
    service.archive(oud.source.source_id)

    nieuw = service.register_pdf(
        title="Nieuw", original_filename="nieuw.pdf", file_hash="abc123"
    )

    match = find_duplicate(service, file_hash="abc123")
    assert match is not None
    assert match.bestaande.source_id == nieuw.source.source_id
    assert match.bestaande.status is ImportStatus.CONCEPT


def test_find_duplicate_kiest_actief_boven_concept(service):
    """Actief wint van Concept."""
    eerste = service.register_pdf(
        title="Eerste", original_filename="eerste.pdf", file_hash="abc123"
    )
    service.set_status(eerste.source.source_id, ImportStatus.ACTIEF)

    service.register_pdf(
        title="Tweede", original_filename="tweede.pdf", file_hash="abc123"
    )

    match = find_duplicate(service, file_hash="abc123")
    assert match is not None
    assert match.bestaande.source_id == eerste.source.source_id
    assert match.bestaande.status is ImportStatus.ACTIEF


def test_find_duplicate_url_kiest_concept_boven_gearchiveerd(service):
    """Bij meerdere URL-matches: Concept wint van Gearchiveerd."""
    oud = service.register_url(title="Oud", source_url="https://example.com")
    service.archive(oud.source.source_id)

    nieuw = service.register_url(
        title="Nieuw", source_url="https://example.com"
    )

    match = find_duplicate(service, source_url="https://example.com")
    assert match is not None
    assert match.bestaande.source_id == nieuw.source.source_id
    assert match.bestaande.status is ImportStatus.CONCEPT


def test_find_duplicate_url_kiest_actief_boven_concept(service):
    """Actief wint van Concept."""
    eerste = service.register_url(
        title="Eerste", source_url="https://example.com"
    )
    service.set_status(eerste.source.source_id, ImportStatus.ACTIEF)

    service.register_url(title="Tweede", source_url="https://example.com")

    match = find_duplicate(service, source_url="https://example.com")
    assert match is not None
    assert match.bestaande.source_id == eerste.source.source_id
    assert match.bestaande.status is ImportStatus.ACTIEF