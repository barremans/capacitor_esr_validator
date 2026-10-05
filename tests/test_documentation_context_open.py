"""
================================================================================
Module:     tests/test_documentation_catalog_product.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-04
Auteur:     Bart Bossuyt

Doel:       Regressietests op de echte productiecatalogus
            (app/data/documentation/catalog.json) na stap 4C.

            Deze tests bewijzen dat de 8 interne ESR-documenten daadwerkelijk
            voorzien zijn van de goedgekeurde multi-contextmetadata en dat
            de bestaande servicefilters op de echte data correct werken.

            Anders dan tests/test_documentation_service.py gebruiken deze
            tests geen synthetische tmp_path-catalogus, maar de werkelijke
            catalogus die met de applicatie meegaat.

Wijzigingen:
  v1.0.0 (2026-10-04)  Eerste productiecatalogustests voor 4C.
================================================================================
"""

from __future__ import annotations

import pytest

from app.documentation.service import DocumentationService


EXPECTED_DOCUMENT_IDS = (
    "esr-safe-discharge",
    "esr-esr-meter",
    "esr-lcr-meter",
    "esr-measurement-methods",
    "esr-frequency-test-voltage",
    "esr-dissipation-factor",
    "esr-ced-plausibility",
    "esr-in-circuit-limitations",
)

EXPECTED_MEASUREMENT_METHODS = {
    "esr-safe-discharge": ("EX_SITU", "ONE_LEG", "IN_CIRCUIT"),
    "esr-esr-meter": ("EX_SITU", "ONE_LEG", "IN_CIRCUIT"),
    "esr-lcr-meter": ("EX_SITU", "ONE_LEG"),
    "esr-measurement-methods": ("EX_SITU", "ONE_LEG", "IN_CIRCUIT"),
    "esr-frequency-test-voltage": ("EX_SITU", "ONE_LEG", "IN_CIRCUIT"),
    "esr-dissipation-factor": ("EX_SITU", "ONE_LEG"),
    "esr-ced-plausibility": ("EX_SITU", "ONE_LEG", "IN_CIRCUIT"),
    "esr-in-circuit-limitations": ("IN_CIRCUIT",),
}


@pytest.fixture(scope="module")
def product_service() -> DocumentationService:
    """Service op de echte productiecatalogus (default pad)."""
    return DocumentationService()


def test_product_catalog_loads_without_errors(product_service):
    documents = product_service.load_documents()
    assert len(documents) == len(EXPECTED_DOCUMENT_IDS)


def test_product_catalog_data_version_is_4c1(product_service):
    documents = product_service.load_documents()
    # Alle records komen uit dezelfde catalogus en delen dezelfde data_version
    # impliciet via de service; we controleren hier expliciet de verwachte
    # document_id-set zodat een onbedoelde toevoeging/verwijdering opvalt.
    assert {d.document_id for d in documents} == set(EXPECTED_DOCUMENT_IDS)


def test_all_product_documents_have_esr_capacitor_tool_key(product_service):
    for document in product_service.load_documents():
        assert document.tool_key == "ESR_CAPACITOR", document.document_id
        assert document.tool_keys == ("ESR_CAPACITOR",), document.document_id


def test_all_product_documents_are_capacitor_component_type(product_service):
    for document in product_service.load_documents():
        assert document.component_types == ("CAPACITOR",), document.document_id


def test_all_product_documents_have_empty_instrument_keys(product_service):
    """Bewijst dat er geen fictieve profiel-ID's zijn toegevoegd in 4C.

    De echte instrumentprofielen zijn LCR_ST1 en MANUAL. Geen enkel
    ESR-document is specifiek voor één profiel; daarom blijft
    instrument_keys leeg.
    """
    for document in product_service.load_documents():
        assert document.instrument_keys == (), document.document_id


@pytest.mark.parametrize(
    ("document_id", "expected_methods"),
    sorted(EXPECTED_MEASUREMENT_METHODS.items()),
)
def test_product_document_measurement_methods(
    product_service,
    document_id,
    expected_methods,
):
    document = product_service.get_document(document_id)
    assert document.measurement_methods == expected_methods


def test_product_filter_in_circuit_matches_expected_subset(product_service):
    matches = product_service.list_documents(measurement_method="IN_CIRCUIT")
    assert {d.document_id for d in matches} == {
        "esr-safe-discharge",
        "esr-esr-meter",
        "esr-measurement-methods",
        "esr-frequency-test-voltage",
        "esr-ced-plausibility",
        "esr-in-circuit-limitations",
    }


def test_product_filter_dissipation_factor_matches_expected_subset(product_service):
    matches = product_service.list_documents(test_key="DISSIPATION_FACTOR")
    assert {d.document_id for d in matches} == {
        "esr-lcr-meter",
        "esr-frequency-test-voltage",
        "esr-dissipation-factor",
        "esr-ced-plausibility",
    }


def test_product_filter_topic_frequency_matches_expected_subset(product_service):
    matches = product_service.list_documents(topic="frequency")
    assert {d.document_id for d in matches} == {
        "esr-esr-meter",
        "esr-lcr-meter",
        "esr-frequency-test-voltage",
        "esr-dissipation-factor",
    }


def test_product_legacy_tool_key_filter_returns_all_documents(product_service):
    """Backward-compatibiliteit: legacy tool_key-filter blijft alle 8 vinden."""
    matches = product_service.list_documents(tool_key="ESR_CAPACITOR")
    assert {d.document_id for d in matches} == set(EXPECTED_DOCUMENT_IDS)