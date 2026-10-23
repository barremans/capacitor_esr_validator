"""
================================================================================
Module:     app/services/exchange/import_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Import-service voor meetketens tussen toestellen (§2.28D).
            Voert een ImportPlan uit: schrijft IMPORT_NEW- en
            IMPORT_AS_CONFLICT_COPY-ketens via de bestaande
            StorageService.save_new_measurement_chain, slaat
            SKIP_DUPLICATE-ketens over, en rapporteert per keten.

            De service doet vóór elke write een race-check: bestaat de
            keten inmiddels al (op herkomst of op natural_key)? Zo ja,
            dan telt hij als skip in plaats van een dubbele keten op te
            slaan. Dat dekt de situatie waarin twee imports tegelijk
            lopen of de gebruiker tijdens een import een nieuwe meting
            opslaat.

            De service herberekent geen assessment, muteert geen
            historische waarden, en schrijft alleen via
            save_new_measurement_chain. Bij een fout in één keten gaat
            de rest door; ImportResult.errors rapporteert per keten.

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie (fase 28D): ImportService,
                       HerkomstRepository, apply_plan met
                       conflict_copy-default, race-check, per-keten
                       rollback.
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from app.services.exchange.export_service import bereken_natural_key
from app.services.exchange.import_planner import (
    HerkomstRepositoryProtocol,
    ImportPlanner,
    NaturalKeyCache,
)
from app.services.exchange.models import (
    ExchangeError,
    ExportedMeasurementChain,
    ImportDecision,
    ImportPlan,
    ImportResult,
)
from app.services.history_service import MeasurementHistoryService
from app.storage.database import open_database
from app.storage.exceptions import StorageError
from app.storage.service import StorageService


# Toegestane waarden voor on_conflict.
_ON_CONFLICT_SKIP = "skip"
_ON_CONFLICT_CONFLICT_COPY = "conflict_copy"
_ALLOWED_ON_CONFLICT = {_ON_CONFLICT_SKIP, _ON_CONFLICT_CONFLICT_COPY}


class HerkomstRepository:
    """Concrete implementatie van HerkomstRepositoryProtocol (§8).

    Leest uit de measurements-tabel op
    ``(source_machine_id, source_measurement_id)``. Alleen lezen; de
    schrijfacties gebeuren via save_new_measurement_chain.
    """

    def __init__(self, database_path: Any) -> None:
        self._database_path = database_path

    def find_measurement_id_by_source(
        self, source_machine_id: str, source_measurement_id: int
    ) -> int | None:
        if not isinstance(source_machine_id, str) or not source_machine_id.strip():
            return None
        if (
            isinstance(source_measurement_id, bool)
            or not isinstance(source_measurement_id, int)
            or source_measurement_id < 1
        ):
            return None

        try:
            connection = open_database(self._database_path)
        except StorageError:
            return None
        try:
            row = connection.execute(
                "SELECT id FROM measurements "
                "WHERE source_machine_id = ? AND source_measurement_id = ? "
                "LIMIT 1",
                (source_machine_id.strip(), source_measurement_id),
            ).fetchone()
            return int(row[0]) if row is not None else None
        finally:
            connection.close()


class ImportService:
    """Voert een ImportPlan uit; schrijft via StorageService."""

    def __init__(
        self,
        *,
        storage_service_factory: Callable[[], StorageService] | None = None,
        history_service: MeasurementHistoryService | None = None,
        herkomst_repository: HerkomstRepositoryProtocol | None = None,
        natural_key_cache: NaturalKeyCache | None = None,
        page_size: int = 500,
    ) -> None:
        self._storage_service_factory = storage_service_factory
        self._history_service = history_service or MeasurementHistoryService()
        self._herkomst_repository = herkomst_repository
        self._natural_key_cache = natural_key_cache
        self._page_size = int(page_size)
        if self._page_size < 1:
            raise ValueError("page_size moet een positief geheel getal zijn.")

    def _storage(self) -> StorageService:
        if self._storage_service_factory is not None:
            return self._storage_service_factory()
        return StorageService(self._history_service._path_service_factory().database_path)

    def apply_plan(
        self,
        plan: ImportPlan,
        *,
        on_conflict: str = _ON_CONFLICT_CONFLICT_COPY,
    ) -> ImportResult:
        """Voer een ImportPlan uit en geef een ImportResult terug.

        ``on_conflict`` bepaalt wat er gebeurt met een NEEDS_USER_CHOICE
        (de planner kent die niet toe, maar de GUI zou hem kunnen
        omzetten):

        - ``"conflict_copy"`` (default): sla op als nieuwe keten.
        - ``"skip"``: sla over.

        ``IMPORT_NEW``-ketens worden altijd opgeslagen.
        ``SKIP_DUPLICATE``-ketens worden altijd overgeslagen.
        """
        if on_conflict not in _ALLOWED_ON_CONFLICT:
            raise ExchangeError(
                f"on_conflict moet één van {sorted(_ALLOWED_ON_CONFLICT)} "
                f"zijn, kreeg {on_conflict!r}."
            )
        if not isinstance(plan, ImportPlan):
            raise ExchangeError(
                f"plan moet een ImportPlan zijn, kreeg {type(plan)!r}"
            )

        storage = self._storage()
        herkomst = self._herkomst_repository
        bestaande_keys = (
            set(self._natural_key_cache().keys())
            if self._natural_key_cache is not None
            else self._bestaande_natural_keys()
        )

        imported_ids: list[int] = []
        conflict_copy_ids: list[int] = []
        skipped = 0
        errors: list[str] = []

        for index, chain in enumerate(plan.envelope.chains):
            decision = plan.decisions[index]
            herberekend = self._herbereken_natural_key(chain)

            # Race-check: bestaat de keten inmiddels al?
            if herkomst is not None:
                bestaande_id = herkomst.find_measurement_id_by_source(
                    chain.source_machine_id, chain.source_measurement_id
                )
                if bestaande_id is not None:
                    skipped += 1
                    continue
            if herberekend in bestaande_keys:
                skipped += 1
                continue

            if decision == ImportDecision.SKIP_DUPLICATE:
                skipped += 1
                continue

            if decision == ImportDecision.NEEDS_USER_CHOICE:
                if on_conflict == _ON_CONFLICT_SKIP:
                    skipped += 1
                    continue
                # on_conflict == conflict_copy: valt door naar write.

            if decision not in (
                ImportDecision.IMPORT_NEW,
                ImportDecision.IMPORT_AS_CONFLICT_COPY,
                ImportDecision.NEEDS_USER_CHOICE,
            ):
                errors.append(
                    f"Keten {index} (source_measurement_id="
                    f"{chain.source_measurement_id}): onbekende decision "
                    f"{decision!r}."
                )
                continue

            try:
                measurement_id = self._schrijf_keten(storage, chain)
            except Exception as exc:
                errors.append(
                    f"Keten {index} (source_measurement_id="
                    f"{chain.source_measurement_id}): {exc}"
                )
                continue

            imported_ids.append(measurement_id)
            if decision == ImportDecision.IMPORT_AS_CONFLICT_COPY:
                conflict_copy_ids.append(measurement_id)
            bestaande_keys.add(herberekend)

        return ImportResult(
            imported_measurement_ids=tuple(imported_ids),
            skipped_duplicate_count=skipped,
            conflict_copy_measurement_ids=tuple(conflict_copy_ids),
            errors=tuple(errors),
        )

    # ------------------------------------------------------------------
    # Interne stappen
    # ------------------------------------------------------------------

    def _schrijf_keten(
        self,
        storage: StorageService,
        chain: ExportedMeasurementChain,
    ) -> int:
        """Schrijf één keten via save_new_measurement_chain; geef measurement_id.

        De keten bevat assessment_snapshots en
        reference_snapshots_by_assessment_index. We schrijven de
        LAATSTE assessment-snapshot (of geen, als er geen is) en zijn
        bijbehorende referenties. Dat is consistent met de bestaande
        save_new_measurement_chain-API, die één assessment per keten
        ondersteunt.
        """
        assessment = (
            dict(chain.assessment_snapshots[-1])
            if chain.assessment_snapshots
            else {}
        )
        # De canonieke keten bevat assessed_at_ms; als die ontbreekt,
        # gebruiken we measured_at_ms + 1 (analoog aan de bestaande
        # rapportage-flow).
        if "assessed_at_ms" not in assessment:
            assessment["assessed_at_ms"] = int(
                chain.measurement.get(
                    "measured_at_ms", chain.measurement_session.get(
                        "started_at_ms", 0
                    )
                )
            ) + 1

        reference_snapshots: list[dict] = []
        if chain.reference_snapshots_by_assessment_index:
            reference_snapshots = [
                dict(item)
                for item in chain.reference_snapshots_by_assessment_index[-1]
            ]

        measurement_payload = dict(chain.measurement)
        measurement_payload["source_machine_id"] = chain.source_machine_id
        measurement_payload["source_measurement_id"] = (
            chain.source_measurement_id
        )

        result = storage.save_new_measurement_chain(
            component_model=dict(chain.component_model),
            component_sample=dict(chain.component_sample),
            measurement_session=dict(chain.measurement_session),
            measurement=measurement_payload,
            assessment_snapshot=assessment,
            reference_snapshots=reference_snapshots,
        )
        return int(result["measurement"].id)

    def _herbereken_natural_key(
        self, chain: ExportedMeasurementChain
    ) -> str:
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
        """Scan de bestaande historiek op natural_keys.

        Hergebruikt dezelfde logica als de planner: per bestaande rij
        een get_measurement_detail() en _natural_key_uit_detail(). Voor
        grote historieken is dit duur; de GUI (28F) kan een cache
        meegeven via ``natural_key_cache``.
        """
        planner = ImportPlanner(
            history_service=self._history_service,
            page_size=self._page_size,
        )
        return planner._bestaande_natural_keys()