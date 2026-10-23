"""
================================================================================
Module:     app/services/exchange/models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       Immutable modellen voor export/import tussen toestellen (§2.28).
            GUI-onafhankelijk, geen Qt, geen SQLite, geen netwerk.

            Dit model is de ENIGE vorm waarin export- en importcode
            meetketens uitwisselen. De storage-laag levert dicts, deze
            modellen normaliseren ze en bewaken het contract uit
            docs/export_import_format.md.

Wijzigingen:
  v1.0.0 (2026-10-22)  Eerste versie (fase 28A): ExchangeError,
                       ExportedMeasurementChain, ExportEnvelope,
                       ImportDecision, ImportConflict, ImportPlan,
                       ImportResult. Frozen en slots, met expliciete
                       validatie in __post_init__.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


FORMAT_VERSION = "1.0"


class ExchangeError(ValueError):
    """Uniforme fout bij export of import tussen toestellen.

    De originele exceptie (OSError, sqlite3.Error, ...) blijft als
    ``__cause__`` bewaard, zodat een debugger of log de bron van de
    fout kan achterhalen zonder dat de exchange-laag alle
    onderliggende exceptietypes hoeft te kennen.
    """


class ImportDecision(str, Enum):
    """Uitkomst van de conflictanalyse voor één keten.

    - ``IMPORT_NEW``: geen match, keten wordt als nieuwe keten opgeslagen.
    - ``SKIP_DUPLICATE``: bestaande keten met dezelfde identiteit of
      dezelfde natuurlijke sleutel; niets doen.
    - ``IMPORT_AS_CONFLICT_COPY``: de gebruiker heeft gekozen voor
      "als kopie importeren"; de keten wordt als nieuwe keten
      opgeslagen, met herkomst-kolommen gevuld.
    - ``NEEDS_USER_CHOICE``: de planner kan niet automatisch beslissen
      (bv. inhoudelijke match maar verschillende herkomst); de GUI
      (28F) moet de gebruiker vragen.
    """

    IMPORT_NEW = "IMPORT_NEW"
    SKIP_DUPLICATE = "SKIP_DUPLICATE"
    IMPORT_AS_CONFLICT_COPY = "IMPORT_AS_CONFLICT_COPY"
    NEEDS_USER_CHOICE = "NEEDS_USER_CHOICE"


def _normaliseer_optionele_tekst(
    waarde: Optional[str], veldnaam: str
) -> Optional[str]:
    """Valideer en normaliseer een optioneel tekstveld.

    - None blijft None.
    - Een lege of whitespace-only string wordt None.
    - Een niet-string, niet-None waarde is een fout.
    """
    if waarde is None:
        return None
    if not isinstance(waarde, str):
        raise ExchangeError(
            f"{veldnaam} moet een string of None zijn, kreeg {type(waarde)!r}"
        )
    gestript = waarde.strip()
    return gestript or None


def _normaliseer_verplichte_tekst(waarde: Any, veldnaam: str) -> str:
    """Valideer en normaliseer een verplicht tekstveld."""
    if not isinstance(waarde, str) or not waarde.strip():
        raise ExchangeError(
            f"{veldnaam} moet een niet-lege string zijn, kreeg {waarde!r}"
        )
    return waarde.strip()


def _normaliseer_dict_kopie(waarde: Any, veldnaam: str) -> dict:
    """Controleer dat waarde een dict is en maak een defensieve kopie.

    Het object is frozen, maar de dict zelf niet. Zonder kopie kan een
    aanroeper de dict van een bestaand model achteraf nog muteren.
    """
    if not isinstance(waarde, dict):
        raise ExchangeError(
            f"{veldnaam} moet een dict zijn, kreeg {type(waarde)!r}"
        )
    return dict(waarde)


def _normaliseer_tuple_van_dicts(
    waarde: Any, veldnaam: str
) -> tuple[dict, ...]:
    """Controleer dat waarde een tuple van dicts is en kopieer defensief."""
    if not isinstance(waarde, tuple):
        raise ExchangeError(
            f"{veldnaam} moet een tuple zijn, kreeg {type(waarde)!r}"
        )
    resultaat: list[dict] = []
    for index, item in enumerate(waarde):
        if not isinstance(item, dict):
            raise ExchangeError(
                f"{veldnaam}[{index}] moet een dict zijn, "
                f"kreeg {type(item)!r}"
            )
        resultaat.append(dict(item))
    return tuple(resultaat)


def _normaliseer_tuple_van_tuples_van_dicts(
    waarde: Any, veldnaam: str
) -> tuple[tuple[dict, ...], ...]:
    """Controleer dat waarde een tuple van tuples van dicts is."""
    if not isinstance(waarde, tuple):
        raise ExchangeError(
            f"{veldnaam} moet een tuple zijn, kreeg {type(waarde)!r}"
        )
    resultaat: list[tuple[dict, ...]] = []
    for buiten_index, binnen in enumerate(waarde):
        if not isinstance(binnen, tuple):
            raise ExchangeError(
                f"{veldnaam}[{buiten_index}] moet een tuple zijn, "
                f"kreeg {type(binnen)!r}"
            )
        binnen_lijst: list[dict] = []
        for binnen_index, item in enumerate(binnen):
            if not isinstance(item, dict):
                raise ExchangeError(
                    f"{veldnaam}[{buiten_index}][{binnen_index}] "
                    f"moet een dict zijn, kreeg {type(item)!r}"
                )
            binnen_lijst.append(dict(item))
        resultaat.append(tuple(binnen_lijst))
    return tuple(resultaat)


def _normaliseer_positieve_int(waarde: Any, veldnaam: str) -> int:
    """Valideer een positieve integer (bool is geen int)."""
    if isinstance(waarde, bool) or not isinstance(waarde, int) or waarde < 1:
        raise ExchangeError(
            f"{veldnaam} moet een positieve integer zijn, kreeg {waarde!r}"
        )
    return waarde


def _normaliseer_niet_negatieve_int(waarde: Any, veldnaam: str) -> int:
    """Valideer een niet-negatieve integer (bool is geen int)."""
    if isinstance(waarde, bool) or not isinstance(waarde, int) or waarde < 0:
        raise ExchangeError(
            f"{veldnaam} moet een niet-negatieve integer zijn, "
            f"kreeg {waarde!r}"
        )
    return waarde


@dataclass(frozen=True, slots=True)
class ExportedMeasurementChain:
    """Eén volledige meetketen in exportvorm (§4 van de spec).

    Velden zijn bewust dicts: de exchange-laag normaliseert ze niet
    inhoudelijk (dat doet de storage-laag al bij creatie). Ze zijn wel
    defensief gekopieerd, zodat het model immutable blijft.
    """

    source_measurement_id: int
    source_machine_id: str
    natural_key: str
    component_model: dict
    component_sample: dict
    measurement_session: dict
    measurement: dict
    assessment_snapshots: tuple[dict, ...]
    reference_snapshots_by_assessment_index: tuple[tuple[dict, ...], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_measurement_id",
            _normaliseer_positieve_int(
                self.source_measurement_id, "source_measurement_id"
            ),
        )
        object.__setattr__(
            self,
            "source_machine_id",
            _normaliseer_verplichte_tekst(
                self.source_machine_id, "source_machine_id"
            ),
        )
        object.__setattr__(
            self,
            "natural_key",
            _normaliseer_verplichte_tekst(self.natural_key, "natural_key"),
        )
        object.__setattr__(
            self,
            "component_model",
            _normaliseer_dict_kopie(self.component_model, "component_model"),
        )
        object.__setattr__(
            self,
            "component_sample",
            _normaliseer_dict_kopie(
                self.component_sample, "component_sample"
            ),
        )
        object.__setattr__(
            self,
            "measurement_session",
            _normaliseer_dict_kopie(
                self.measurement_session, "measurement_session"
            ),
        )
        object.__setattr__(
            self,
            "measurement",
            _normaliseer_dict_kopie(self.measurement, "measurement"),
        )
        object.__setattr__(
            self,
            "assessment_snapshots",
            _normaliseer_tuple_van_dicts(
                self.assessment_snapshots, "assessment_snapshots"
            ),
        )
        object.__setattr__(
            self,
            "reference_snapshots_by_assessment_index",
            _normaliseer_tuple_van_tuples_van_dicts(
                self.reference_snapshots_by_assessment_index,
                "reference_snapshots_by_assessment_index",
            ),
        )
        if (
            len(self.reference_snapshots_by_assessment_index)
            != len(self.assessment_snapshots)
        ):
            raise ExchangeError(
                "reference_snapshots_by_assessment_index moet evenveel "
                "items hebben als assessment_snapshots."
            )

    def to_dict(self) -> dict:
        """Serialiseer naar een JSON-vriendelijk dict."""
        return {
            "source_measurement_id": self.source_measurement_id,
            "source_machine_id": self.source_machine_id,
            "natural_key": self.natural_key,
            "component_model": dict(self.component_model),
            "component_sample": dict(self.component_sample),
            "measurement_session": dict(self.measurement_session),
            "measurement": dict(self.measurement),
            "assessment_snapshots": [
                dict(item) for item in self.assessment_snapshots
            ],
            "reference_snapshots_by_assessment_index": [
                [dict(item) for item in binnen]
                for binnen in self.reference_snapshots_by_assessment_index
            ],
        }


@dataclass(frozen=True, slots=True)
class ExportEnvelope:
    """Eén exportbestand (§3 van de spec).

    ``chains`` mag leeg zijn: een lege export is geldig en wordt bij
    import als "niets te doen" behandeld.
    """

    format_version: str
    app_version: str
    schema_version: int
    exported_at_ms: int
    source_machine_id: str
    chains: tuple[ExportedMeasurementChain, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "format_version",
            _normaliseer_verplichte_tekst(
                self.format_version, "format_version"
            ),
        )
        if self.format_version != FORMAT_VERSION:
            raise ExchangeError(
                f"Onbekende format_version {self.format_version!r}; "
                f"deze app ondersteunt alleen {FORMAT_VERSION!r}."
            )
        object.__setattr__(
            self,
            "app_version",
            _normaliseer_verplichte_tekst(self.app_version, "app_version"),
        )
        object.__setattr__(
            self,
            "schema_version",
            _normaliseer_positieve_int(
                self.schema_version, "schema_version"
            ),
        )
        object.__setattr__(
            self,
            "exported_at_ms",
            _normaliseer_niet_negatieve_int(
                self.exported_at_ms, "exported_at_ms"
            ),
        )
        object.__setattr__(
            self,
            "source_machine_id",
            _normaliseer_verplichte_tekst(
                self.source_machine_id, "source_machine_id"
            ),
        )
        if not isinstance(self.chains, tuple):
            raise ExchangeError(
                f"chains moet een tuple zijn, kreeg {type(self.chains)!r}"
            )
        for index, chain in enumerate(self.chains):
            if not isinstance(chain, ExportedMeasurementChain):
                raise ExchangeError(
                    f"chains[{index}] moet een ExportedMeasurementChain "
                    f"zijn, kreeg {type(chain)!r}"
                )

    def to_dict(self) -> dict:
        """Serialiseer naar een JSON-vriendelijk dict."""
        return {
            "format_version": self.format_version,
            "app_version": self.app_version,
            "schema_version": self.schema_version,
            "exported_at_ms": self.exported_at_ms,
            "source_machine_id": self.source_machine_id,
            "chains": [chain.to_dict() for chain in self.chains],
        }


@dataclass(frozen=True, slots=True)
class ImportConflict:
    """Eén conflict dat de gebruiker moet oplossen (28F).

    ``bestaande_measurement_id`` is de id van de bestaande keten op
    dit toestel; die kan de gebruiker in de GUI tonen.
    """

    chain_index: int
    natural_key: str
    source_measurement_id: int
    source_machine_id: str
    bestaande_measurement_id: int
    reden: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chain_index",
            _normaliseer_niet_negatieve_int(
                self.chain_index, "chain_index"
            ),
        )
        object.__setattr__(
            self,
            "natural_key",
            _normaliseer_verplichte_tekst(self.natural_key, "natural_key"),
        )
        object.__setattr__(
            self,
            "source_measurement_id",
            _normaliseer_positieve_int(
                self.source_measurement_id, "source_measurement_id"
            ),
        )
        object.__setattr__(
            self,
            "source_machine_id",
            _normaliseer_verplichte_tekst(
                self.source_machine_id, "source_machine_id"
            ),
        )
        object.__setattr__(
            self,
            "bestaande_measurement_id",
            _normaliseer_positieve_int(
                self.bestaande_measurement_id, "bestaande_measurement_id"
            ),
        )
        object.__setattr__(
            self,
            "reden",
            _normaliseer_verplichte_tekst(self.reden, "reden"),
        )


@dataclass(frozen=True, slots=True)
class ImportPlan:
    """Resultaat van de conflictanalyse (§7 van de spec).

    ``decisions[i]`` hoort bij ``envelope.chains[i]``. ``conflicts``
    bevat alleen de ketens met ``NEEDS_USER_CHOICE``, in dezelfde
    volgorde als ``decisions``.
    """

    envelope: ExportEnvelope
    decisions: tuple[ImportDecision, ...]
    conflicts: tuple[ImportConflict, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, ExportEnvelope):
            raise ExchangeError(
                f"envelope moet een ExportEnvelope zijn, "
                f"kreeg {type(self.envelope)!r}"
            )
        if not isinstance(self.decisions, tuple):
            raise ExchangeError(
                f"decisions moet een tuple zijn, "
                f"kreeg {type(self.decisions)!r}"
            )
        for index, decision in enumerate(self.decisions):
            if not isinstance(decision, ImportDecision):
                raise ExchangeError(
                    f"decisions[{index}] moet een ImportDecision zijn, "
                    f"kreeg {type(decision)!r}"
                )
        if len(self.decisions) != len(self.envelope.chains):
            raise ExchangeError(
                "decisions moet evenveel items hebben als "
                "envelope.chains."
            )
        if not isinstance(self.conflicts, tuple):
            raise ExchangeError(
                f"conflicts moet een tuple zijn, "
                f"kreeg {type(self.conflicts)!r}"
            )
        for index, conflict in enumerate(self.conflicts):
            if not isinstance(conflict, ImportConflict):
                raise ExchangeError(
                    f"conflicts[{index}] moet een ImportConflict zijn, "
                    f"kreeg {type(conflict)!r}"
                )


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Resultaat van het daadwerkelijk importeren (28D).

    Per keten wordt de uitkomst vastgelegd, zodat de GUI (28F) een
    samenvatting kan tonen zonder de envelope opnieuw te doorlopen.
    """

    imported_measurement_ids: tuple[int, ...] = ()
    skipped_duplicate_count: int = 0
    conflict_copy_measurement_ids: tuple[int, ...] = ()
    errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.imported_measurement_ids, tuple):
            raise ExchangeError(
                "imported_measurement_ids moet een tuple zijn, "
                f"kreeg {type(self.imported_measurement_ids)!r}"
            )
        for index, mid in enumerate(self.imported_measurement_ids):
            _normaliseer_positieve_int(
                mid, f"imported_measurement_ids[{index}]"
            )
        object.__setattr__(
            self,
            "skipped_duplicate_count",
            _normaliseer_niet_negatieve_int(
                self.skipped_duplicate_count, "skipped_duplicate_count"
            ),
        )
        if not isinstance(self.conflict_copy_measurement_ids, tuple):
            raise ExchangeError(
                "conflict_copy_measurement_ids moet een tuple zijn, "
                f"kreeg {type(self.conflict_copy_measurement_ids)!r}"
            )
        for index, mid in enumerate(self.conflict_copy_measurement_ids):
            _normaliseer_positieve_int(
                mid, f"conflict_copy_measurement_ids[{index}]"
            )
        if not isinstance(self.errors, tuple):
            raise ExchangeError(
                f"errors moet een tuple zijn, kreeg {type(self.errors)!r}"
            )
        for index, error in enumerate(self.errors):
            if not isinstance(error, str):
                raise ExchangeError(
                    f"errors[{index}] moet een string zijn, "
                    f"kreeg {type(error)!r}"
                )

    @property
    def imported_count(self) -> int:
        return len(self.imported_measurement_ids)

    @property
    def conflict_copy_count(self) -> int:
        return len(self.conflict_copy_measurement_ids)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)