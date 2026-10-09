"""
================================================================================
Module:     tests/test_documentation_service_user_catalog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.3.0
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de tweede cataloguslaag in
            DocumentationService: imports uit imported_catalog.json
            worden samengevoegd met de ingebouwde catalogus.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie: basisintegratie, dubbele
                       document_id, bronresolutie.
  v1.0.1 (2026-10-07)  Regressietests voor de metadata die sinds
                       5D'.2c wordt doorgegeven aan DocumentMetadata.
  v1.1.0 (2026-10-08)  Fase 5D'.2e: tests voor include_archived-
                       parameter en voor het doorgeven van import_status
                       aan DocumentMetadata.
  v1.2.0 (2026-10-09)  Fase 5D'.1b: formele regressietests voor het
                       doorzoeken van importmetadata via search_text.
                       Bevestigt dat manufacturer, series, part_number,
                       document_version, document_date, notes, category
                       en source_url doorzoekbaar zijn, en dat
                       technische identificatie (document_id,
                       source_path) NIET doorzoekbaar is. Geen
                       codewijziging; formaliseert bestaand gedrag van
                       _search_blob.
  v1.2.1 (2026-10-09)  Fix: test_search_text_vindt_source_url gebruikte
                       zoekterm "datasheet", die ook matchte op de
                       ingebouwde categorie DATASHEET. Vervangen door
                       een unieke URL en zoekterm zodat alleen de
                       URL-import matcht.
  v1.3.0 (2026-10-09)  Fase 6C: tests voor docx/xlsx-imports in de
                       gebruikerscatalogus. Bevestigt dat de viewer
                       docx/xlsx herkent als FILE met het juiste
                       source_path.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.documentation.models import DocumentCategory, DocumentSourceType
from app.documentation.service import DocumentationService


# ============================================================================
# Hulp: maak een minimale ingebouwde catalogus in tmp_path
# ============================================================================

def _maak_ingebouwde_catalogus(pad: Path) -> Path:
    pad.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "data_version": "test-1",
                "documents": [
                    {
                        "document_id": "builtin-1",
                        "title": "Ingebouwd document",
                        "category": "DATASHEET",
                        "source_type": "URL",
                        "source_url": "https://example.com/builtin",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return pad


def _schrijf_gebruikerscatalogus(pad: Path, sources: list[dict]) -> Path:
    pad.write_text(
        json.dumps(
            {"schema_version": 1, "sources": sources},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return pad


def _basis_source(
    *,
    source_id: str = "import-1",
    status: str = "concept",
    **extra,
) -> dict:
    bron = {
        "source_id": source_id,
        "source_type": "pdf",
        "title": "Eigen import",
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": status,
        "original_filename": "eigen.pdf",
        "file_hash": "hash_x",
    }
    bron.update(extra)
    return bron


def _service_met_imports(tmp_path: Path, sources: list[dict]) -> DocumentationService:
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        sources,
    )
    return DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )


# ============================================================================
# Basisintegratie
# ============================================================================

def test_gebruikerscatalogus_wordt_samengevoegd(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source()],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs = service.load_documents()
    ids = {d.document_id for d in docs}
    assert ids == {"builtin-1", "import-1"}


def test_gebruikerscatalogus_wint_bij_dubbele_document_id(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source(source_id="builtin-1")],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs = service.load_documents()
    assert len(docs) == 1
    assert docs[0].title == "Eigen import"


# ============================================================================
# Metadata sinds 5D'.2c
# ============================================================================

def test_metadata_wordt_doorgegeven_aan_documentmetadata(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [
            _basis_source(
                category="MANUAL",
                manufacturer="CHONG",
                series="CDX",
                part_number="CDX-1",
                document_version="V1.1",
                document_date="2026-10-08",
                notes="Testnotitie",
            )
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    doc = service.get_document("import-1")
    assert doc.category is DocumentCategory.MANUAL
    assert doc.manufacturer == "CHONG"
    assert doc.series == "CDX"
    assert doc.part_number == "CDX-1"
    assert doc.document_version == "V1.1"
    assert doc.document_date == "2026-10-08"
    assert doc.notes == "Testnotitie"
    assert doc.is_user_import is True


def test_lege_categorie_valt_terug_op_datasheet(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source()],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    doc = service.get_document("import-1")
    assert doc.category is DocumentCategory.DATASHEET


# ============================================================================
# include_archived — sinds 5D'.2e
# ============================================================================

def test_default_verbergt_gearchiveerde_imports(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source(status="gearchiveerd")],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs = service.load_documents()
    ids = {d.document_id for d in docs}
    assert ids == {"builtin-1"}


def test_include_archived_toont_gearchiveerde_imports(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source(status="gearchiveerd")],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs = service.load_documents(include_archived=True)
    ids = {d.document_id for d in docs}
    assert ids == {"builtin-1", "import-1"}


def test_ingebouwde_catalogus_negeert_include_archived(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs_zonder = service.load_documents(include_archived=False)
    docs_met = service.load_documents(include_archived=True)
    assert {d.document_id for d in docs_zonder} == {"builtin-1"}
    assert {d.document_id for d in docs_met} == {"builtin-1"}


def test_combinatie_met_search_text(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [
            _basis_source(
                source_id="import-a",
                status="gearchiveerd",
                manufacturer="CHONG",
            ),
            _basis_source(
                source_id="import-b",
                status="concept",
                manufacturer="PANASONIC",
            ),
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    result = service.list_documents(
        search_text="PANASONIC",
        include_archived=True,
    )
    assert {d.document_id for d in result} == {"import-b"}


def test_combinatie_met_category(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [
            _basis_source(
                source_id="import-a",
                status="gearchiveerd",
                category="MANUAL",
            ),
            _basis_source(
                source_id="import-b",
                status="gearchiveerd",
                category="DATASHEET",
            ),
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    result = service.list_documents(
        category="MANUAL",
        include_archived=True,
    )
    assert {d.document_id for d in result} == {"import-a"}


def test_import_status_wordt_doorgegeven_aan_documentmetadata(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [
            _basis_source(source_id="import-a", status="actief"),
            _basis_source(source_id="import-b", status="gearchiveerd"),
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    doc_a = service.get_document("import-a")
    assert doc_a.import_status == "actief"

    doc_b = service.get_document("import-b")
    assert doc_b.import_status == "gearchiveerd"


# ============================================================================
# Metadata doorzoekbaar via search_text — sinds 5D'.1b
# ============================================================================

def test_search_text_vindt_manufacturer(tmp_path):
    service = _service_met_imports(
        tmp_path,
        [_basis_source(manufacturer="CHONG")],
    )

    result = service.list_documents(search_text="CHONG")
    assert {d.document_id for d in result} == {"import-1"}


def test_search_text_vindt_series(tmp_path):
    service = _service_met_imports(
        tmp_path,
        [_basis_source(series="CDX")],
    )

    result = service.list_documents(search_text="CDX")
    assert {d.document_id for d in result} == {"import-1"}


def test_search_text_vindt_part_number(tmp_path):
    service = _service_met_imports(
        tmp_path,
        [_basis_source(part_number="CDX-1")],
    )

    result = service.list_documents(search_text="CDX-1")
    assert {d.document_id for d in result} == {"import-1"}


def test_search_text_vindt_document_version(tmp_path):
    service = _service_met_imports(
        tmp_path,
        [_basis_source(document_version="V1.1")],
    )

    result = service.list_documents(search_text="V1.1")
    assert {d.document_id for d in result} == {"import-1"}


def test_search_text_vindt_document_date(tmp_path):
    service = _service_met_imports(
        tmp_path,
        [_basis_source(document_date="2026-10-08")],
    )

    result = service.list_documents(search_text="2026-10-08")
    assert {d.document_id for d in result} == {"import-1"}


def test_search_text_vindt_notes(tmp_path):
    service = _service_met_imports(
        tmp_path,
        [_basis_source(notes="Testnotitie")],
    )

    result = service.list_documents(search_text="Testnotitie")
    assert {d.document_id for d in result} == {"import-1"}


def test_search_text_vindt_category(tmp_path):
    service = _service_met_imports(
        tmp_path,
        [_basis_source(category="MANUAL")],
    )

    result = service.list_documents(search_text="MANUAL")
    assert {d.document_id for d in result} == {"import-1"}


def test_search_text_vindt_source_url(tmp_path):
    """De URL van een URL-import is doorzoekbaar.

    Let op: de zoekterm moet uniek zijn. "datasheet" zou ook matchen op
    de ingebouwde categorie DATASHEET, waardoor builtin-1 ten onrechte
    in het resultaat zou komen.
    """
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-url",
                "source_type": "url",
                "title": "URL import",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "source_url": "https://example.com/uniekpad123",
            }
        ],
    )

    result = service.list_documents(search_text="uniekpad123")
    assert {d.document_id for d in result} == {"import-url"}


def test_search_text_vindt_titel(tmp_path):
    service = _service_met_imports(
        tmp_path,
        [_basis_source(title="Eigen import")],
    )

    result = service.list_documents(search_text="Eigen")
    assert {d.document_id for d in result} == {"import-1"}


def test_search_text_negeert_document_id(tmp_path):
    """document_id is technische identificatie en wordt niet doorzocht."""
    service = _service_met_imports(
        tmp_path,
        [_basis_source(source_id="unieke-technische-id")],
    )

    result = service.list_documents(search_text="unieke-technische-id")
    # Alleen builtin-1 heeft geen match; import-1 heeft de id niet in
    # _search_blob. Resultaat: geen enkel document.
    assert result == []


def test_search_text_negeert_source_path(tmp_path):
    """source_path is technische identificatie en wordt niet doorzocht."""
    service = _service_met_imports(
        tmp_path,
        [_basis_source(source_id="import-pad")],
    )

    # source_path wordt afgeleid als "sources/import-pad.pdf".
    result = service.list_documents(search_text="sources/import-pad.pdf")
    assert result == []


def test_search_text_combineert_metadata_en_titel(tmp_path):
    """Meerdere termen moeten allemaal matchen (EN-semantiek)."""
    service = _service_met_imports(
        tmp_path,
        [
            _basis_source(
                source_id="import-a",
                title="Handleiding CDX",
                manufacturer="CHONG",
            ),
            _basis_source(
                source_id="import-b",
                title="Handleiding CDX",
                manufacturer="PANASONIC",
            ),
        ],
    )

    result = service.list_documents(search_text="Handleiding CHONG")
    assert {d.document_id for d in result} == {"import-a"}


def test_search_text_metadata_gearchiveerd_met_include_archived(tmp_path):
    """Gearchiveerde imports blijven doorzoekbaar met include_archived=True."""
    service = _service_met_imports(
        tmp_path,
        [
            _basis_source(
                source_id="import-arch",
                status="gearchiveerd",
                manufacturer="CHONG",
            ),
        ],
    )

    zonder = service.list_documents(search_text="CHONG")
    assert zonder == []

    met = service.list_documents(
        search_text="CHONG",
        include_archived=True,
    )
    assert {d.document_id for d in met} == {"import-arch"}


def test_search_text_metadata_gearchiveerd_zonder_include_archived(tmp_path):
    """Zonder include_archived blijven gearchiveerde imports verborgen,
    ook als hun metadata zou matchen."""
    service = _service_met_imports(
        tmp_path,
        [
            _basis_source(
                source_id="import-arch",
                status="gearchiveerd",
                manufacturer="CHONG",
            ),
        ],
    )

    result = service.list_documents(search_text="CHONG")
    assert result == []


def test_search_text_lege_metadata_matcht_niet(tmp_path):
    """Imports zonder metadata mogen niet per ongeluk matchen op lege
    strings."""
    service = _service_met_imports(
        tmp_path,
        [_basis_source()],
    )

    # Lege search_text toont alles; dat is bestaand gedrag.
    alles = service.list_documents(search_text="")
    assert {d.document_id for d in alles} == {"builtin-1", "import-1"}

    # Een term die nergens voorkomt levert niets op.
    niets = service.list_documents(search_text="bestaat-niet-xyz")
    assert niets == []


# ============================================================================
# v1.3.0 — docx- en xlsx-imports (fase 6C)
# ============================================================================

def test_docx_import_wordt_gelezen_als_file(tmp_path):
    """Een docx-import verschijnt als DocumentSourceType.FILE."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-docx",
                "source_type": "docx",
                "title": "Word-document",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "original_filename": "doc.docx",
                "file_hash": "hash_docx",
            }
        ],
    )

    docs = service.load_documents()
    docx_docs = [d for d in docs if d.document_id == "import-docx"]
    assert len(docx_docs) == 1

    doc = docx_docs[0]
    assert doc.source_type is DocumentSourceType.FILE
    assert doc.source_path == "sources/import-docx.docx"
    assert doc.source_url is None
    assert doc.is_user_import is True


def test_xlsx_import_wordt_gelezen_als_file(tmp_path):
    """Een xlsx-import verschijnt als DocumentSourceType.FILE."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-xlsx",
                "source_type": "xlsx",
                "title": "Excel-werkmap",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "original_filename": "doc.xlsx",
                "file_hash": "hash_xlsx",
            }
        ],
    )

    docs = service.load_documents()
    xlsx_docs = [d for d in docs if d.document_id == "import-xlsx"]
    assert len(xlsx_docs) == 1

    doc = xlsx_docs[0]
    assert doc.source_type is DocumentSourceType.FILE
    assert doc.source_path == "sources/import-xlsx.xlsx"
    assert doc.source_url is None
    assert doc.is_user_import is True


def test_docx_import_krijgt_provenance(tmp_path):
    """Een docx-import krijgt een FILE-provenance met originele bestandsnaam."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-docx",
                "source_type": "docx",
                "title": "Word-document",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "original_filename": "mijn-bestand.docx",
                "file_hash": "hash",
            }
        ],
    )

    doc = service.get_document("import-docx")
    assert len(doc.provenance) == 1
    ref = doc.provenance[0]
    assert ref.source_kind == "FILE"
    assert ref.source_path == "sources/import-docx.docx"
    assert "mijn-bestand.docx" in (ref.note or "")


def test_xlsx_import_krijgt_provenance(tmp_path):
    """Een xlsx-import krijgt een FILE-provenance met originele bestandsnaam."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-xlsx",
                "source_type": "xlsx",
                "title": "Excel-werkmap",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "original_filename": "mijn-bestand.xlsx",
                "file_hash": "hash",
            }
        ],
    )

    doc = service.get_document("import-xlsx")
    assert len(doc.provenance) == 1
    ref = doc.provenance[0]
    assert ref.source_kind == "FILE"
    assert ref.source_path == "sources/import-xlsx.xlsx"
    assert "mijn-bestand.xlsx" in (ref.note or "")


def test_docx_en_xlsx_kunnen_gearchiveerd_worden(tmp_path):
    """Ook docx/xlsx respecteren include_archived."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-docx",
                "source_type": "docx",
                "title": "Word",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "gearchiveerd",
                "original_filename": "doc.docx",
                "file_hash": "h1",
            },
            {
                "source_id": "import-xlsx",
                "source_type": "xlsx",
                "title": "Excel",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "gearchiveerd",
                "original_filename": "doc.xlsx",
                "file_hash": "h2",
            },
        ],
    )

    zonder = service.load_documents()
    zonder_ids = {d.document_id for d in zonder}
    assert "import-docx" not in zonder_ids
    assert "import-xlsx" not in zonder_ids

    met = service.load_documents(include_archived=True)
    met_ids = {d.document_id for d in met}
    assert "import-docx" in met_ids
    assert "import-xlsx" in met_ids


def test_docx_metadata_wordt_doorgegeven(tmp_path):
    """Metadata van een docx-import komt door in DocumentMetadata."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-docx",
                "source_type": "docx",
                "title": "Word-doc",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "original_filename": "doc.docx",
                "file_hash": "h",
                "category": "MANUAL",
                "manufacturer": "CHONG",
                "series": "CDX",
                "part_number": "CDX-1",
                "document_version": "V1.1",
                "document_date": "2026-10-09",
                "notes": "Word notitie",
            }
        ],
    )

    doc = service.get_document("import-docx")
    assert doc.category is DocumentCategory.MANUAL
    assert doc.manufacturer == "CHONG"
    assert doc.series == "CDX"
    assert doc.part_number == "CDX-1"
    assert doc.document_version == "V1.1"
    assert doc.document_date == "2026-10-09"
    assert doc.notes == "Word notitie"


def test_xlsx_metadata_wordt_doorgegeven(tmp_path):
    """Metadata van een xlsx-import komt door in DocumentMetadata."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-xlsx",
                "source_type": "xlsx",
                "title": "Excel-werkmap",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "original_filename": "doc.xlsx",
                "file_hash": "h",
                "category": "REFERENCE_TABLE",
                "manufacturer": "TDK",
            }
        ],
    )

    doc = service.get_document("import-xlsx")
    assert doc.category is DocumentCategory.REFERENCE_TABLE
    assert doc.manufacturer == "TDK"


def test_docx_zoekbaar_op_metadata(tmp_path):
    """Docx-imports zijn doorzoekbaar op hun metadata."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-docx",
                "source_type": "docx",
                "title": "Word-doc",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "original_filename": "doc.docx",
                "file_hash": "h",
                "manufacturer": "CHONG",
            }
        ],
    )

    result = service.list_documents(search_text="CHONG")
    assert {d.document_id for d in result} == {"import-docx"}


def test_xlsx_zoekbaar_op_metadata(tmp_path):
    """Xlsx-imports zijn doorzoekbaar op hun metadata."""
    service = _service_met_imports(
        tmp_path,
        [
            {
                "source_id": "import-xlsx",
                "source_type": "xlsx",
                "title": "Excel-werkmap",
                "imported_at": 1_700_000_000_000,
                "imported_by": "tester",
                "status": "concept",
                "original_filename": "doc.xlsx",
                "file_hash": "h",
                "manufacturer": "TDK",
            }
        ],
    )

    result = service.list_documents(search_text="TDK")
    assert {d.document_id for d in result} == {"import-xlsx"}