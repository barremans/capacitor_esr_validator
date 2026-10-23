"""
================================================================================
Module:     app/services/exchange/import_planner.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Pure conflictanalyse voor import tussen toestellen (§2.28C).
            Leest de bestaande database via de history-service, maar
            schrijft nooit. Produceert een ImportPlan met per keten een
            ImportDecision.

            De planner hergebruikt bereken_natural_key() uit
            export_service.py: één bron van waarheid voor de canonieke
            sleutel, zowel bij export als bij import.

            Herkomst-detectie (source_machine_id + source_measurement_id)
            is optioneel via een HerkomstRepositoryProtocol. In 28C is die
            None (de kolommen bestaan nog niet); in 28E/28D vult de
            import-service een echte implementatie in zonder de planner
            te herschrijven.

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie (fase 28C): ImportPlanner,
                       HerkomstRepositoryProtocol, natural-key-
                       hercontrole, duplicate-detectie op natural_key.
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol, runtime_checkable

from app.services.exchange.export_service import bereken_natural_key
from app.services.exchange.models import (
    ExchangeError,
    ExportEnvelope,
    ExportedMeasurementChain,
    ImportDecision,
    ImportPlan,
)
from app.services.history_service import MeasurementHistoryService
from app.storage.schema import CURRENT_SCHEMA_VERSION


@runtime_checkable
class HerkomstRepositoryProtocol(Protocol):
    """Protocol voor herkomst-detectie (§8 van de spec).

    De implementatie in 28E/28D zoekt op
    ``(source_machine_id, source_measurement_id)`` in de
    ``measurements``-tabel. In 28C is er geen implementatie; de
    planner slaat de herkomst-stap dan over.
    """

    def find_measurement_id_by_source(
        self, source_machine_id: str, source_measurement_id: int
    ) -> int | None:
        ...


# Type alias voor de optionele natural-key-cache.
NaturalKeyCache = Callable[[], Mapping[str, int]]


class ImportPlanner:
    """Read-only conflictanalyse voor een ExportEnvelope."""

    def __init__(
        self,
        *,
        history_service: MeasurementHistoryService | None = None,
        herkomst_repository: HerkomstRepositoryProtocol | None = None,
        natural_key_cache: NaturalKeyCache | None = None,
        page_size: int = 500,
    ) -> None:
        self._history_service = history_service or MeasurementHistoryService()
        self._herkomst_repository = herkomst_repository
        self._natural_key_cache = natural_key_cache
        self._page_size = int(page_size)
        if self._page_size < 1:
            raise ValueError("page_size moet een positief geheel getal zijn.")

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def plan(self, envelope: ExportEnvelope) -> ImportPlan:
        """Analyseer de envelope en produceer een ImportPlan.

        Leest de bestaande database via de history-service. Schrijft
        nooit. Faalt met ExchangeError bij een ongeldige envelope of
        een natural-key-mismatch in één van de ketens.
        """
        if not isinstance(envelope, ExportEnvelope):
            raise ExchangeError(
                f"envelope moet een ExportEnvelope zijn, "
                f"kreeg {type(envelope)!r}"
            )

        if envelope.schema_version > CURRENT_SCHEMA_VERSION:
            raise ExchangeError(
                f"Envelope gebruikt schema_version="
                f"{envelope.schema_version}, maar deze app ondersteunt "
                f"maximaal {CURRENT_SCHEMA_VERSION}."
            )

        # Lege envelope: geldig, niets te beslissen.
        if not envelope.chains:
            return ImportPlan(envelope=envelope, decisions=())

        # Stap 1: herbereken de natural_key per keten en controleer dat
        # die overeenkomt met de meegeschreven waarde. Bij afwijking
        # weigeren we de hele envelope (corrupt of handmatig bewerkt).
        herberekend: list[str] = []
        for index, chain in enumerate(envelope.chains):
            sleutel = self._herbereken_natural_key(chain)
            if sleutel != chain.natural_key:
                raise ExchangeError(
                    f"Chain {index} (source_measurement_id="
                    f"{chain.source_measurement_id}) heeft een "
                    f"natural_key die niet overeenkomt met de inhoud. "
                    f"Het bestand is mogelijk beschadigd of handmatig "
                    f"bewerkt."
                )
            herberekend.append(sleutel)

        # Stap 2: bouw de set bestaande natural_keys in de database.
        bestaande_keys = self._bestaande_natural_keys()

        # Stap 3: beslis per keten.
        decisions: list[ImportDecision] = []
        for index, chain in enumerate(envelope.chains):
            decisions.append(
                self._beslis(chain, herberekend[index], bestaande_keys)
            )

        return ImportPlan(
            envelope=envelope,
            decisions=tuple(decisions),
        )

    # ------------------------------------------------------------------
    # Interne stappen
    # ------------------------------------------------------------------

    def _beslis(
        self,
        chain: ExportedMeasurementChain,
        natural_key: str,
        bestaande_keys: set[str],
    ) -> ImportDecision:
        """Bepaal de ImportDecision voor één keten."""
        # Herkomst-detectie (alleen als de repository bestaat).
        if self._herkomst_repository is not None:
            bestaande_id = self._herkomst_repository.find_measurement_id_by_source(
                chain.source_machine_id, chain.source_measurement_id
            )
            if bestaande_id is not None:
                return ImportDecision.SKIP_DUPLICATE

        # Natural-key-detectie.
        if natural_key in bestaande_keys:
            return ImportDecision.SKIP_DUPLICATE

        return ImportDecision.IMPORT_NEW

    def _herbereken_natural_key(
        self, chain: ExportedMeasurementChain
    ) -> str:
        """Herbereken de natural_key uit de ketenvelden (§6)."""
        return bereken_natural_key(
            component_model=dict(chain.component_model),
            component_sample=dict(chain.component_sample),
            measurement_session=dict(chain.measurement_session),
            measurement=dict(chain.measurement),
            assessment_snapshots=chain.assessment_snapshots,
            reference_snapshots_by_assessment_index=(
                chain.reference_snapshots_by_assessment_index
            ),
        )

    def _bestaande_natural_keys(self) -> set[str]:
        """Bouw de set bestaande natural_keys uit de database.

        Gebruikt de optionele cache als die is meegegeven; anders
        scant de planner de historiek in pagina's via de
        history-service. Voor elke bestaande keten wordt de
        natural_key herberekend uit het detail.
        """
        if self._natural_key_cache is not None:
            return set(self._natural_key_cache().keys())

        keys: set[str] = set()
        offset = 0
        while True:
            chunk = self._history_service.list_measurements(
                None, limit=self._page_size, offset=offset
            )
            if not chunk:
                break
            for row in chunk:
                measurement_id = int(row["measurement"].id)
                detail = self._history_service.get_measurement_detail(
                    measurement_id
                )
                if detail is None:
                    # Race: rij verdwenen tussen list en detail. Sla
                    # over; de import-service zal later opnieuw
                    # controleren.
                    continue
                keys.add(self._natural_key_uit_detail(detail))
            if len(chunk) < self._page_size:
                break
            offset += len(chunk)
        return keys

    def _natural_key_uit_detail(self, detail: dict[str, Any]) -> str:
        """Herbereken de natural_key uit een get_measurement_detail()-resultaat.

        Dit is dezelfde berekening als in ExportService._bouw_chain(),
        maar zonder de ExportedMeasurementChain tussenstap. Zo blijft
        de canonieke vorm identiek aan wat de export heeft
        meegeschreven.
        """
        from app.services.exchange.export_service import (
            _REFERENCE_FIELDS,
            _velden_uit_model,
        )

        model = detail["component_model"]
        sample = detail["component_sample"]
        session = detail["measurement_session"]
        measurement = detail["measurement"]
        assessments = detail.get("assessment_snapshots") or []
        references_by_assessment = (
            detail.get("reference_snapshots_by_assessment_id") or {}
        )

        component_model_dict = _velden_uit_model(
            model,
            _canonieke_component_model_velden(),
        )
        component_sample_dict = _velden_uit_model(
            sample,
            _canonieke_component_sample_velden(),
        )
        measurement_session_dict = _velden_uit_model(
            session,
            _canonieke_measurement_session_velden(),
        )
        measurement_dict = _velden_uit_model(
            measurement,
            _canonieke_measurement_velden(),
        )

        assessment_dicts: list[dict] = []
        reference_index: list[tuple[dict, ...]] = []
        for assessment in assessments:
            assessment_dicts.append(
                _velden_uit_model(
                    assessment,
                    _canonieke_assessment_velden(),
                )
            )
            refs = references_by_assessment.get(assessment.id, [])
            reference_index.append(
                tuple(
                    _velden_uit_model(ref, _REFERENCE_FIELDS)
                    for ref in refs
                )
            )

        return bereken_natural_key(
            component_model=component_model_dict,
            component_sample=component_sample_dict,
            measurement_session=measurement_session_dict,
            measurement=measurement_dict,
            assessment_snapshots=tuple(assessment_dicts),
            reference_snapshots_by_assessment_index=tuple(reference_index),
        )


# ---------------------------------------------------------------------------
# Canonieke velden — doorverwijzing naar export_service.
# ---------------------------------------------------------------------------
#
# De veldlijsten leven in export_service.py en zijn daar de bron van
# waarheid. We importeren ze hier via kleine wrappers zodat de planner
# niet afhankelijk is van de private namen (met underscore) elders.

def _canonieke_component_model_velden() -> tuple[str, ...]:
    from app.services.exchange.export_service import _COMPONENT_MODEL_FIELDS
    return _COMPONENT_MODEL_FIELDS


def _canonieke_component_sample_velden() -> tuple[str, ...]:
    from app.services.exchange.export_service import _COMPONENT_SAMPLE_FIELDS
    return _COMPONENT_SAMPLE_FIELDS


def _canonieke_measurement_session_velden() -> tuple[str, ...]:
    from app.services.exchange.export_service import _MEASUREMENT_SESSION_FIELDS
    return _MEASUREMENT_SESSION_FIELDS


def _canonieke_measurement_velden() -> tuple[str, ...]:
    from app.services.exchange.export_service import _MEASUREMENT_FIELDS
    return _MEASUREMENT_FIELDS


def _canonieke_assessment_velden() -> tuple[str, ...]:
    from app.services.exchange.export_service import _ASSESSMENT_FIELDS
    return _ASSESSMENT_FIELDS