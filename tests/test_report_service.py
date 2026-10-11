"""
================================================================================
Module:     tests/test_report_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Regressietests voor ReportService: read-only gedrag, validatie
            van measurement_id, correcte bundeling van app-versie,
            rapportdatum, taal en werkplaats, en multitool-gedrag.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie. Bewijst read-only via een stub die
                        elke schrijfmethode laat falen.
  v1.1.0 (2026-10-10)  Multitool: build_bundle_for_measurements,
                        build_bundle_from_filters, sortering op tijd.
  v1.2.0 (2026-10-10)  Extra tests voor deduplicatie, veiligheidsgrens,
                        scope-label en gemengde tools.
================================================================================
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.report_service import ReportService


class _ReadOnlyHistoryStub:
    """History-service die elke schrijfpoging hard laat falen."""

    def __init__(self, details: dict[int, dict]):
        self._details = details
        self.read_calls: list[int] = []
        self.list_calls: list[tuple[dict, int, int]] = []
        self._list_rows: list[dict] = []

    def set_list_rows(self, rows: list[dict]) -> None:
        self._list_rows = rows

    def get_measurement_detail(self, measurement_id):
        self.read_calls.append(measurement_id)
        return self._details.get(measurement_id)

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.list_calls.append((dict(filters or {}), limit, offset))
        return self._list_rows[offset: offset + limit]

    def create_measurement(self, *args, **kwargs):
        raise AssertionError("ReportService mag niet schrijven (create).")

    def save_measurement(self, *args, **kwargs):
        raise AssertionError("ReportService mag niet schrijven (save).")

    def update_measurement(self, *args, **kwargs):
        raise AssertionError("ReportService mag niet schrijven (update).")

    def delete_measurement(self, *args, **kwargs):
        raise AssertionError("ReportService mag niet schrijven (delete).")


def _detail(measurement_id: int = 42, *, tool_key: str = "ESR_CAPACITOR", measured_at_ms: int | None = None):
    measurement = SimpleNamespace(
        id=measurement_id,
        tool_key=tool_key,
        measured_at_ms=measured_at_ms if measured_at_ms is not None else 1_700_000_000_000 + measurement_id,
    )
    return {
        "component_model": SimpleNamespace(id=1),
        "component_sample": SimpleNamespace(id=2),
        "measurement_session": SimpleNamespace(id=3),
        "measurement": measurement,
        "assessment_snapshots": [],
        "reference_snapshots_by_assessment_id": {},
    }


# ---------------------------------------------------------------------------
# build_bundle (backward-compatible)
# ---------------------------------------------------------------------------

def test_build_bundle_returns_full_bundle():
    stub = _ReadOnlyHistoryStub({42: _detail(measurement_id=42)})
    service = ReportService(history_service=stub)

    bundle = service.build_bundle(
        measurement_id=42,
        taal="nl_NL",
        werkplaats="Labo A",
        rapportdatum="2026-10-10 09:00:00",
    )

    assert bundle.measurement_id == 42
    assert bundle.tool_key == "ESR_CAPACITOR"
    assert bundle.taal == "nl_NL"
    assert bundle.rapportdatum == "2026-10-10 09:00:00"
    assert bundle.werkplaats == "Labo A"
    assert bundle.app_versie
    assert bundle.aantal_metingen == 1
    assert stub.read_calls == [42]


def test_build_bundle_uses_default_rapportdatum_when_missing():
    stub = _ReadOnlyHistoryStub({42: _detail(measurement_id=42)})
    service = ReportService(history_service=stub)

    bundle = service.build_bundle(measurement_id=42, taal="nl_NL")

    assert bundle.rapportdatum
    assert "T" not in bundle.rapportdatum
    assert ":" in bundle.rapportdatum


def test_build_bundle_strips_werkplaats():
    stub = _ReadOnlyHistoryStub({42: _detail(measurement_id=42)})
    service = ReportService(history_service=stub)

    bundle = service.build_bundle(
        measurement_id=42,
        taal="nl_NL",
        werkplaats="   Labo A   ",
    )

    assert bundle.werkplaats == "Labo A"


def test_build_bundle_raises_for_missing_measurement():
    class _EmptyHistory:
        def get_measurement_detail(self, measurement_id):
            return None

    service = ReportService(history_service=_EmptyHistory())

    with pytest.raises(ValueError):
        service.build_bundle(measurement_id=42, taal="nl_NL")


@pytest.mark.parametrize("ongeldig", [0, -1, True, False, "42", 4.2, None])
def test_build_bundle_rejects_invalid_measurement_id(ongeldig):
    stub = _ReadOnlyHistoryStub({42: _detail(measurement_id=42)})
    service = ReportService(history_service=stub)

    with pytest.raises(ValueError):
        service.build_bundle(measurement_id=ongeldig, taal="nl_NL")


def test_build_bundle_does_not_write():
    stub = _ReadOnlyHistoryStub({42: _detail(measurement_id=42)})
    service = ReportService(history_service=stub)

    service.build_bundle(measurement_id=42, taal="nl_NL", werkplaats="Labo A")

    assert stub.read_calls == [42]


# ---------------------------------------------------------------------------
# build_bundle_for_measurements (multitool)
# ---------------------------------------------------------------------------

def test_build_bundle_for_measurements_accepts_multiple_ids():
    stub = _ReadOnlyHistoryStub({
        1: _detail(measurement_id=1, measured_at_ms=1000),
        2: _detail(measurement_id=2, measured_at_ms=2000),
        3: _detail(measurement_id=3, measured_at_ms=3000),
    })
    service = ReportService(history_service=stub)

    bundle = service.build_bundle_for_measurements(
        [2, 1, 3],
        taal="nl_NL",
    )

    assert bundle.aantal_metingen == 3
    # Volgorde: oplopend op measured_at_ms (oud -> nieuw)
    assert [d["measurement"].id for d in bundle.details] == [1, 2, 3]


def test_build_bundle_for_measurements_deduplicates_ids():
    stub = _ReadOnlyHistoryStub({
        1: _detail(measurement_id=1, measured_at_ms=1000),
        2: _detail(measurement_id=2, measured_at_ms=2000),
    })
    service = ReportService(history_service=stub)

    bundle = service.build_bundle_for_measurements(
        [1, 1, 2, 2, 1],
        taal="nl_NL",
    )

    assert bundle.aantal_metingen == 2
    assert stub.read_calls == [1, 2]


def test_build_bundle_for_measurements_rejects_empty_list():
    stub = _ReadOnlyHistoryStub({})
    service = ReportService(history_service=stub)

    with pytest.raises(ValueError):
        service.build_bundle_for_measurements([], taal="nl_NL")


def test_build_bundle_for_measurements_rejects_unknown_id():
    stub = _ReadOnlyHistoryStub({1: _detail(measurement_id=1)})
    service = ReportService(history_service=stub)

    with pytest.raises(ValueError):
        service.build_bundle_for_measurements([1, 99], taal="nl_NL")


def test_build_bundle_for_measurements_accepts_mixed_tools():
    """Multitool: ESR + een fictieve RESISTOR-meting in één bundel."""
    stub = _ReadOnlyHistoryStub({
        1: _detail(measurement_id=1, tool_key="ESR_CAPACITOR", measured_at_ms=1000),
        2: _detail(measurement_id=2, tool_key="RESISTOR", measured_at_ms=2000),
    })
    service = ReportService(history_service=stub)

    bundle = service.build_bundle_for_measurements([1, 2], taal="nl_NL")

    assert bundle.aantal_metingen == 2
    tool_keys = [d["measurement"].tool_key for d in bundle.details]
    assert tool_keys == ["ESR_CAPACITOR", "RESISTOR"]


def test_build_bundle_for_measurements_scope_label():
    stub = _ReadOnlyHistoryStub({1: _detail(measurement_id=1)})
    service = ReportService(history_service=stub)

    bundle = service.build_bundle_for_measurements(
        [1], taal="nl_NL", scope="enkel"
    )

    assert bundle.scope == "enkel"


# ---------------------------------------------------------------------------
# build_bundle_from_filters
# ---------------------------------------------------------------------------

def test_build_bundle_from_filters_uses_list_measurements():
    stub = _ReadOnlyHistoryStub({
        1: _detail(measurement_id=1, measured_at_ms=1000),
        2: _detail(measurement_id=2, measured_at_ms=2000),
    })
    stub.set_list_rows([
        {"measurement": SimpleNamespace(id=1)},
        {"measurement": SimpleNamespace(id=2)},
    ])
    service = ReportService(history_service=stub)

    bundle = service.build_bundle_from_filters(
        {"tool_key": "ESR_CAPACITOR"},
        taal="nl_NL",
    )

    assert bundle.aantal_metingen == 2
    assert stub.list_calls[0][0] == {"tool_key": "ESR_CAPACITOR"}
    assert stub.read_calls == [1, 2]


def test_build_bundle_from_filters_rejects_empty_result():
    stub = _ReadOnlyHistoryStub({})
    stub.set_list_rows([])
    service = ReportService(history_service=stub)

    with pytest.raises(ValueError):
        service.build_bundle_from_filters({}, taal="nl_NL")


def test_build_bundle_from_filters_rejects_too_many():
    stub = _ReadOnlyHistoryStub({})
    stub.set_list_rows([{"measurement": SimpleNamespace(id=i + 1)} for i in range(50)])
    service = ReportService(history_service=stub)

    with pytest.raises(ValueError):
        service.build_bundle_from_filters({}, taal="nl_NL", max_metingen=10)