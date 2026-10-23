"""
================================================================================
Module:     app/services/exchange/export_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Read-only export-service voor meetketens tussen toestellen
            (§2.28B). Leest via de bestaande MeasurementHistoryService,
            bouwt ExportedMeasurementChain-objecten volgens de canonieke
            velden uit docs/export_import_format.md §5, berekent de
            natuurlijke sleutel (§6) en schrijft een ExportEnvelope als
            UTF-8 JSON zonder BOM.

            De service schrijft nooit naar de database, herberekent geen
            assessment en muteert geen historische waarden. Ze leest
            uitsluitend via get_measurement_detail() en list_measurements().

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie (fase 28B): export_measurements,
                       export_filters, write_envelope. Natural-key-
                       berekening volgens spec §6. Machine-ID uit
                       settings.json, met generatie bij ontbreken.
  v1.0.1 (2026-10-23)  Fase 28F: read_envelope(path) toegevoegd. Leest
                       een exportbestand, valideert format_version en
                       schema_version, en bouwt een ExportEnvelope.
                       Nodig voor de import-tab van de exchange-dialoog.
================================================================================
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace as _dc_replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping
import uuid

from app.config.settings import (
    laad_instellingen,
    sla_instellingen_op,
)
from app.services.exchange.models import (
    FORMAT_VERSION,
    ExchangeError,
    ExportEnvelope,
    ExportedMeasurementChain,
)
from app.services.history_service import MeasurementHistoryService
from app.storage.database import utc_now_ms
from app.storage.schema import CURRENT_SCHEMA_VERSION
from app.version import __version__ as _APP_VERSION


# ---------------------------------------------------------------------------
# Canonieke velden (§5 van de spec). Volgorde is bindend voor natural_key.
# ---------------------------------------------------------------------------

_COMPONENT_MODEL_FIELDS: tuple[str, ...] = (
    "manufacturer",
    "series",
    "part_number",
    "technology",
    "nominal_capacitance_f",
    "nominal_capacitance_value",
    "nominal_capacitance_unit",
    "rated_voltage_v",
    "voltage_type",
    "tolerance_lower_pct",
    "tolerance_upper_pct",
    "temperature_min_c",
    "temperature_max_c",
    "case_size",
    "notes",
)

_COMPONENT_SAMPLE_FIELDS: tuple[str, ...] = (
    "sample_code",
    "sample_state",
    "source",
    "batch_lot_code",
    "date_code",
    "visual_condition",
    "notes",
)

_MEASUREMENT_SESSION_FIELDS: tuple[str, ...] = (
    "started_at_ms",
    "ended_at_ms",
    "operator_name",
    "customer",
    "project",
    "installation",
    "module_board",
    "component_reference",
    "notes",
)

_MEASUREMENT_FIELDS: tuple[str, ...] = (
    "measured_at_ms",
    "measurement_method",
    "tool_key",
    "instrument_key",
    "instrument_name",
    "instrument_profile_version",
    "frequency_hz",
    "test_voltage_vrms",
    "temperature_c",
    "power_off_confirmed",
    "discharged_confirmed",
    "residual_voltage_before_v",
    "residual_voltage_after_v",
    "capacitance_f",
    "esr_ohm",
    "dissipation_factor_d",
    "quality_factor_q",
    "impedance_z_ohm",
    "reactance_x_ohm",
    "out_of_range",
    "open_suspected",
    "short_suspected",
    "unstable_reading",
    "parallel_components_notes",
    "mechanical_condition_notes",
    "notes",
    "record_status",
    "invalid_reason",
)

_ASSESSMENT_FIELDS: tuple[str, ...] = (
    "assessed_at_ms",
    "engine_version",
    "capacitance_status",
    "capacitance_deviation_pct",
    "esr_status",
    "esr_factor",
    "consistency_status",
    "derived_esr_from_d_ohm",
    "reliability_level",
    "final_status",
    "reasons_json",
    "warnings_json",
    "advice_json",
)

_REFERENCE_FIELDS: tuple[str, ...] = (
    "reference_role",
    "reference_level",
    "reference_type",
    "manufacturer",
    "series",
    "part_number",
    "reference_value",
    "reference_unit",
    "frequency_hz",
    "temperature_c",
    "test_voltage_vrms",
    "dc_bias_v",
    "value_kind",
    "source_name",
    "source_document",
    "source_version",
    "source_data_version",
    "source_entry_id",
    "source_hash",
    "snapshot_json",
)


# ---------------------------------------------------------------------------
# Interne helpers — velduittrekking.
# ---------------------------------------------------------------------------

def _enum_naar_waarde(waarde: Any) -> Any:
    """Converteer Enum naar zijn .value; laat andere waarden ongemoeid."""
    if isinstance(waarde, Enum):
        return waarde.value
    return waarde


def _velden_uit_model(model: Any, veldnamen: tuple[str, ...]) -> dict:
    """Trek de canonieke velden uit een dataclass-model of een dict.

    None-waarden worden weggelaten (§5 van de spec). Enum-waarden
    worden vervangen door hun .value.
    """
    if isinstance(model, dict):
        bron: dict = model
    else:
        bron = {veld: getattr(model, veld, None) for veld in veldnamen}

    resultaat: dict = {}
    for veld in veldnamen:
        waarde = _enum_naar_waarde(bron.get(veld))
        if waarde is None:
            continue
        resultaat[veld] = waarde
    return resultaat


# ---------------------------------------------------------------------------
# Natural key (§6).
# ---------------------------------------------------------------------------

def _canonieke_dict_voor_key(
    component_model: dict,
    component_sample: dict,
    measurement_session: dict,
    measurement: dict,
    assessment_snapshots: tuple[dict, ...],
    reference_snapshots_by_assessment_index: tuple[tuple[dict, ...], ...],
) -> dict:
    """Bouw de canonieke dict voor de natural-key-berekening.

    Conform §6: exact de velden uit §5, in volgorde, None weggelaten,
    geen id/created_at_ms/source_*-velden.
    """
    return {
        "component_model": component_model,
        "component_sample": component_sample,
        "measurement_session": measurement_session,
        "measurement": measurement,
        "assessment_snapshots": [
            dict(item) for item in assessment_snapshots
        ],
        "reference_snapshots_by_assessment_index": [
            [dict(item) for item in binnen]
            for binnen in reference_snapshots_by_assessment_index
        ],
    }


def bereken_natural_key(
    component_model: dict,
    component_sample: dict,
    measurement_session: dict,
    measurement: dict,
    assessment_snapshots: tuple[dict, ...],
    reference_snapshots_by_assessment_index: tuple[tuple[dict, ...], ...],
) -> str:
    """Pure functie: SHA-256 hex over de canonieke JSON (§6).

    Publiek zodat tests en 28C (import-planner) dezelfde berekening
    kunnen hergebruiken.
    """
    canoniek = _canonieke_dict_voor_key(
        component_model=component_model,
        component_sample=component_sample,
        measurement_session=measurement_session,
        measurement=measurement,
        assessment_snapshots=assessment_snapshots,
        reference_snapshots_by_assessment_index=reference_snapshots_by_assessment_index,
    )
    tekst = json.dumps(
        canoniek,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Machine-ID (settings.json, categorie "algemeen.machine_id").
# ---------------------------------------------------------------------------

def verkrijg_machine_id() -> str:
    """Geef de machine_id uit settings.json, of genereer en bewaar een nieuwe.

    De machine_id is een UUID4 die één keer per machine wordt aangemaakt
    en daarna hergebruikt. De waarde wordt opgeslagen in
    ``algemeen.machine_id`` via ``sla_instellingen_op``. Faalt de
    opslag (OSError, ValueError), dan geven we de gegenereerde waarde
    terug zonder op te slaan: de export kan doorgaan, alleen niet
    duurzaam geïdentificeerd.
    """
    instellingen = laad_instellingen()
    bestaand = getattr(instellingen.algemeen, "machine_id", "") or ""
    if bestaand.strip():
        return bestaand.strip()

    nieuwe = str(uuid.uuid4())
    try:
        bijgewerkt = _dc_replace(
            instellingen,
            algemeen=_dc_replace(
                instellingen.algemeen,
                machine_id=nieuwe,
            ),
        )
        sla_instellingen_op(bijgewerkt)
    except (OSError, ValueError):
        pass
    return nieuwe


# ---------------------------------------------------------------------------
# Inlezen van een exportbestand (28F).
# ---------------------------------------------------------------------------

def read_envelope(path: Path | str) -> ExportEnvelope:
    """Lees een exportbestand en bouw een ExportEnvelope.

    Valideert: bestand bestaat, geldige JSON, verplichte velden,
    ``format_version`` (via de ExportEnvelope-constructor),
    ``schema_version`` ≤ CURRENT_SCHEMA_VERSION.

    Faalt met ExchangeError bij elke fout. De aanroeper (GUI) toont de
    melding aan de gebruiker.
    """
    doel = Path(path)
    if not doel.exists():
        raise ExchangeError(f"Exportbestand niet gevonden: {doel}")
    if not doel.is_file():
        raise ExchangeError(f"Pad is geen bestand: {doel}")

    try:
        tekst = doel.read_text(encoding="utf-8")
    except OSError as exc:
        raise ExchangeError(
            f"Exportbestand kon niet worden gelezen: {exc}"
        ) from exc

    try:
        data = json.loads(tekst)
    except json.JSONDecodeError as exc:
        raise ExchangeError(
            f"Exportbestand is geen geldige JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ExchangeError(
            "Exportbestand moet een JSON-object met velden bevatten."
        )

    schema_version = data.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version < 1
    ):
        raise ExchangeError(
            "Exportbestand heeft geen geldig schema_version."
        )
    if schema_version > CURRENT_SCHEMA_VERSION:
        raise ExchangeError(
            f"Exportbestand gebruikt schema_version={schema_version}, "
            f"maar deze app ondersteunt maximaal {CURRENT_SCHEMA_VERSION}."
        )

    ruwe_chains = data.get("chains")
    if not isinstance(ruwe_chains, list):
        raise ExchangeError(
            "Exportbestand heeft geen 'chains'-lijst."
        )

    chains: list[ExportedMeasurementChain] = []
    for index, ruwe in enumerate(ruwe_chains):
        if not isinstance(ruwe, dict):
            raise ExchangeError(
                f"chains[{index}] moet een JSON-object zijn."
            )
        try:
            chains.append(_chain_uit_dict(ruwe))
        except ExchangeError as exc:
            raise ExchangeError(
                f"chains[{index}] ongeldig: {exc}"
            ) from exc

    try:
        return ExportEnvelope(
            format_version=data.get("format_version"),
            app_version=data.get("app_version"),
            schema_version=schema_version,
            exported_at_ms=data.get("exported_at_ms"),
            source_machine_id=data.get("source_machine_id"),
            chains=tuple(chains),
        )
    except ExchangeError as exc:
        raise ExchangeError(
            f"Exportbestand ongeldig: {exc}"
        ) from exc


def _chain_uit_dict(ruwe: dict) -> ExportedMeasurementChain:
    """Bouw één ExportedMeasurementChain uit een JSON-dict."""
    assessment_raw = ruwe.get("assessment_snapshots", [])
    if not isinstance(assessment_raw, list):
        raise ExchangeError(
            "assessment_snapshots moet een lijst zijn."
        )
    assessments = tuple(
        dict(item) if isinstance(item, dict) else item
        for item in assessment_raw
    )
    refs_raw = ruwe.get("reference_snapshots_by_assessment_index", [])
    if not isinstance(refs_raw, list):
        raise ExchangeError(
            "reference_snapshots_by_assessment_index moet een lijst zijn."
        )
    refs_index: list[tuple[dict, ...]] = []
    for binnen in refs_raw:
        if not isinstance(binnen, list):
            raise ExchangeError(
                "Elke entry van reference_snapshots_by_assessment_index "
                "moet een lijst zijn."
            )
        refs_index.append(
            tuple(
                dict(item) if isinstance(item, dict) else item
                for item in binnen
            )
        )

    return ExportedMeasurementChain(
        source_measurement_id=ruwe.get("source_measurement_id"),
        source_machine_id=ruwe.get("source_machine_id"),
        natural_key=ruwe.get("natural_key"),
        component_model=dict(ruwe.get("component_model") or {}),
        component_sample=dict(ruwe.get("component_sample") or {}),
        measurement_session=dict(ruwe.get("measurement_session") or {}),
        measurement=dict(ruwe.get("measurement") or {}),
        assessment_snapshots=assessments,
        reference_snapshots_by_assessment_index=tuple(refs_index),
    )


# ---------------------------------------------------------------------------
# ExportService.
# ---------------------------------------------------------------------------

class ExportService:
    """Read-only service die meetketens exporteert als ExportEnvelope."""

    def __init__(
        self,
        *,
        history_service: MeasurementHistoryService | None = None,
        machine_id: str | None = None,
        clock: Callable[[], int] = utc_now_ms,
    ) -> None:
        self._history_service = history_service or MeasurementHistoryService()
        self._machine_id = machine_id
        self._clock = clock

    def _haal_machine_id(self) -> str:
        if self._machine_id is not None:
            return self._machine_id
        return verkrijg_machine_id()

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def export_measurements(
        self,
        measurement_ids: list[int],
    ) -> ExportEnvelope:
        """Exporteer een expliciete lijst metingen als ExportEnvelope.

        Lege lijst geeft ExchangeError. Volgorde blijft die van de
        opgegeven lijst; dubbele id's worden genegeerd.
        """
        if not isinstance(measurement_ids, list):
            raise ExchangeError("measurement_ids moet een lijst zijn.")

        unieke_ids: list[int] = []
        gezien: set[int] = set()
        for mid in measurement_ids:
            if isinstance(mid, bool) or not isinstance(mid, int) or mid < 1:
                raise ExchangeError(
                    "Elke measurement_id moet een positieve integer zijn."
                )
            if mid in gezien:
                continue
            gezien.add(mid)
            unieke_ids.append(mid)

        if not unieke_ids:
            raise ExchangeError("Geen metingen opgegeven voor export.")

        machine_id = self._haal_machine_id()
        chains: list[ExportedMeasurementChain] = []
        for mid in unieke_ids:
            detail = self._history_service.get_measurement_detail(mid)
            if detail is None:
                raise ExchangeError(
                    f"Geen meetdetail gevonden voor measurement_id={mid}."
                )
            chains.append(self._bouw_chain(detail, machine_id=machine_id))

        return ExportEnvelope(
            format_version=FORMAT_VERSION,
            app_version=_APP_VERSION,
            schema_version=CURRENT_SCHEMA_VERSION,
            exported_at_ms=int(self._clock()),
            source_machine_id=machine_id,
            chains=tuple(chains),
        )

    def export_filters(
        self,
        filters: Mapping[str, Any] | None,
    ) -> ExportEnvelope:
        """Exporteer alle metingen die aan de filters voldoen.

        Leest in pagina's via de history-service. Weigert een lege
        selectie met ExchangeError.
        """
        rijen: list[dict[str, Any]] = []
        offset = 0
        pagina = 200
        while True:
            chunk = self._history_service.list_measurements(
                filters, limit=pagina, offset=offset
            )
            rijen.extend(chunk)
            if len(chunk) < pagina:
                break
            offset += len(chunk)

        if not rijen:
            raise ExchangeError("Geen metingen voor deze filters.")

        measurement_ids = [int(r["measurement"].id) for r in rijen]
        return self.export_measurements(measurement_ids)

    def write_envelope(
        self,
        envelope: ExportEnvelope,
        path: Path | str,
    ) -> None:
        """Schrijf een ExportEnvelope als UTF-8 JSON zonder BOM.

        Pretty-printed, 2 spaties inspringing, sort_keys=True.
        Overschrijft een bestaand bestand zonder waarschuwing; de GUI
        (28F) bewaakt dat met een save-dialoog.
        """
        if not isinstance(envelope, ExportEnvelope):
            raise ExchangeError(
                f"envelope moet een ExportEnvelope zijn, "
                f"kreeg {type(envelope)!r}"
            )
        doel = Path(path)
        try:
            tekst = json.dumps(
                envelope.to_dict(),
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
            )
            doel.write_text(tekst + "\n", encoding="utf-8")
        except OSError as exc:
            raise ExchangeError(
                f"Exportbestand kon niet worden geschreven: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Interne bouwstenen
    # ------------------------------------------------------------------

    def _bouw_chain(
        self,
        detail: dict[str, Any],
        *,
        machine_id: str,
    ) -> ExportedMeasurementChain:
        """Zet één get_measurement_detail()-resultaat om naar een chain."""
        model = detail["component_model"]
        sample = detail["component_sample"]
        session = detail["measurement_session"]
        measurement = detail["measurement"]
        assessments = detail.get("assessment_snapshots") or []
        references_by_assessment = (
            detail.get("reference_snapshots_by_assessment_id") or {}
        )

        component_model_dict = _velden_uit_model(
            model, _COMPONENT_MODEL_FIELDS
        )
        component_sample_dict = _velden_uit_model(
            sample, _COMPONENT_SAMPLE_FIELDS
        )
        measurement_session_dict = _velden_uit_model(
            session, _MEASUREMENT_SESSION_FIELDS
        )
        measurement_dict = _velden_uit_model(
            measurement, _MEASUREMENT_FIELDS
        )

        assessment_dicts: list[dict] = []
        reference_index: list[tuple[dict, ...]] = []
        for assessment in assessments:
            assessment_dicts.append(
                _velden_uit_model(assessment, _ASSESSMENT_FIELDS)
            )
            refs = references_by_assessment.get(assessment.id, [])
            reference_index.append(
                tuple(
                    _velden_uit_model(ref, _REFERENCE_FIELDS)
                    for ref in refs
                )
            )

        assessment_tuple = tuple(assessment_dicts)
        reference_tuple = tuple(reference_index)

        natural_key = bereken_natural_key(
            component_model=component_model_dict,
            component_sample=component_sample_dict,
            measurement_session=measurement_session_dict,
            measurement=measurement_dict,
            assessment_snapshots=assessment_tuple,
            reference_snapshots_by_assessment_index=reference_tuple,
        )

        return ExportedMeasurementChain(
            source_measurement_id=int(measurement.id),
            source_machine_id=machine_id,
            natural_key=natural_key,
            component_model=component_model_dict,
            component_sample=component_sample_dict,
            measurement_session=measurement_session_dict,
            measurement=measurement_dict,
            assessment_snapshots=assessment_tuple,
            reference_snapshots_by_assessment_index=reference_tuple,
        )