"""
================================================================================
Module:     tests/test_documentation_catalog_product.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.2
Datum:      2026-10-05
Auteur:     Bart Bossuyt

Doel:       Regressietests op de echte productiecatalogus
            (app/data/documentation/catalog.json) na stap 4C en 4D.

            Bewijst dat de 8 interne ESR-documenten voorzien zijn van de
            goedgekeurde multi-contextmetadata en dat de bestaande
            servicefilters én de nieuwe zoektaal op de echte data correct
            werken.

            Anders dan tests/test_documentation_service.py gebruiken deze
            tests geen synthetische tmp_path-catalogus, maar de werkelijke
            catalogus die met de applicatie meegaat.

Wijzigingen:
  v1.0.0 (2026-10-04)  Eerste productiecatalogustests voor 4C.
  v1.1.0 (2026-10-04)  Zoektaal-tests op de echte catalogus (4D.2).
  v1.1.1 (2026-10-05)  _search_blob versmald naar menselijke metadata.
                        document_id en source_path worden niet meer via het
                        zoekveld gematcht. Zoekverwachtingen bijgesteld op
                        basis van de werkelijke catalogusinhoud.
  v1.1.2 (2026-10-05)  title_key uit zoekblob verwijderd. Test
                        test_product_search_matches_title_key vervangen door
                        test_product_search_does_not_match_title_key.
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
    assert {d.document_id for d in documents} == set(EXPECTED_DOCUMENT_IDS)


def test_all_product_documents_have_esr_capacitor_tool_key(product_service):
    for document in product_service.load_documents():
        assert document.tool_key == "ESR_CAPACITOR", document.document_id
        assert document.tool_keys == ("ESR_CAPACITOR",), document.document_id


def test_all_product_documents_are_capacitor_component_type(product_service):
    for document in product_service.load_documents():
        assert document.component_types == ("CAPACITOR",), document.document_id


def test_all_product_documents_have_empty_instrument_keys(product_service):
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
    matches = product_service.list_documents(tool_key="ESR_CAPACITOR")
    assert {d.document_id for d in matches} == set(EXPECTED_DOCUMENT_IDS)


# ---------------------------------------------------------------------------
# Zoektaal op de echte productiecatalogus
# ---------------------------------------------------------------------------


def test_product_search_capa_matches_two_documents(product_service):
    """'capa' matcht titel van esr-lcr-meter en notes van esr-dissipation-factor."""
    matches = product_service.list_documents(search_text="capa")
    assert {d.document_id for d in matches} == {
        "esr-lcr-meter",
        "esr-dissipation-factor",
    }


def test_product_search_esr_matches_four_documents(product_service):
    """'esr' matcht titel en/of notes van 4 documenten — niet via document_id."""
    matches = product_service.list_documents(search_text="esr")
    assert {d.document_id for d in matches} == {
        "esr-esr-meter",
        "esr-lcr-meter",
        "esr-dissipation-factor",
        "esr-ced-plausibility",
    }


def test_product_search_esr_and_meter_matches_two_documents(product_service):
    matches = product_service.list_documents(search_text="esr meter")
    assert {d.document_id for d in matches} == {
        "esr-esr-meter",
        "esr-lcr-meter",
    }


def test_product_search_esr_or_lcr_matches_four_documents(product_service):
    matches = product_service.list_documents(search_text="esr|lcr")
    assert {d.document_id for d in matches} == {
        "esr-esr-meter",
        "esr-lcr-meter",
        "esr-dissipation-factor",
        "esr-ced-plausibility",
    }


def test_product_search_wildcard_meter_matches_two_documents(product_service):
    matches = product_service.list_documents(search_text="%meter")
    assert {d.document_id for d in matches} == {
        "esr-esr-meter",
        "esr-lcr-meter",
    }


def test_product_search_exclusion_lcr_matches_seven_documents(product_service):
    matches = product_service.list_documents(search_text="!lcr")
    assert {d.document_id for d in matches} == set(EXPECTED_DOCUMENT_IDS) - {
        "esr-lcr-meter"
    }


def test_product_search_esr_and_not_lcr_matches_three_documents(product_service):
    matches = product_service.list_documents(search_text="esr !lcr")
    assert {d.document_id for d in matches} == {
        "esr-esr-meter",
        "esr-dissipation-factor",
        "esr-ced-plausibility",
    }


def test_product_search_unknown_term_returns_empty(product_service):
    assert product_service.list_documents(search_text="xyz123") == []


# ---------------------------------------------------------------------------
# Bewijst dat technische velden NIET meedoen in het zoekveld
# ---------------------------------------------------------------------------


def test_product_search_does_not_match_document_id(product_service):
    """document_id is technisch en wordt bewust niet via het zoekveld gematcht.

    'ced' komt voor in document_id 'esr-ced-plausibility', maar niet in de
    titel ('C–ESR–D plausibiliteitscontrole') of notes.
    """
    matches = product_service.list_documents(search_text="ced")
    assert matches == []


def test_product_search_does_not_match_source_path(product_service):
    """source_path is technisch en wordt bewust niet via het zoekveld gematcht.

    'capacitor_safe' komt voor in source_path 'internal/nl_NL/capacitor_safe_discharge.md',
    maar niet in de titel of notes van esr-safe-discharge.
    """
    matches = product_service.list_documents(search_text="capacitor_safe")
    assert matches == []


def test_product_search_does_not_match_title_key(product_service):
    """title_key is een technische i18n-sleutel en wordt bewust niet via het
    zoekveld gematcht.

    Alle 8 interne documenten hebben een title_key die begint met
    'documentatie.document_titels.esr_...'. Toch mag 'document_titels'
    geen match opleveren — het is geen menselijke metadata.
    """
    matches = product_service.list_documents(search_text="document_titels")
    assert matches == []


def test_product_search_source_url_when_present(product_service):
    """source_url is informatief en blijft doorzoekbaar.

    De 8 interne documenten hebben geen source_url. Deze test is een
    placeholder om te bewijzen dat zoeken op URL-achtige termen geen
    onverwachte match geeft.
    """
    matches = product_service.list_documents(search_text="example.com")
    assert matches == []