"""
================================================================================
Module:     app/services/report_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Read-only applicatieservice voor meetrapporten.

            Leest een of meerdere volledige meetketens via
            MeasurementHistoryService en bundelt die tot een immutable
            ReportBundle dat de pure HTML-renderer (app/helpers/report_render.py)
            kan verwerken. De service schrijft nooit, kent geen Qt en
            herberekent geen assessment- of referentiewaarden: alles komt uit
            de opgeslagen snapshots.

            Multitool-neutraal: de service is niet gebonden aan ESR_CAPACITOR.
            Elke tool_key die de historiek kan opslaan, kan gebundeld worden.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: ReportBundle, ReportService met
                        build_bundle(measurement_id), read-only bewezen door
                        een stub-history in de tests.
  v1.1.0 (2026-10-10)  Multitool: ReportBundle draagt nu een tuple van
                        details; build_bundle_for_measurements en
                        build_bundle_from_filters toegevoegd. build_bundle
                        blijft bestaan als dunne wrapper (backward-compatible).
                        ReportBundle.detail blijft als property bestaan voor
                        bestaande aanroepers en tests.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from app.services.history_service import MeasurementHistoryService
from app.version import __version__ as _APP_VERSION


def _nu_iso() -> str:
    """Lokale ISO-timestamp voor de rapportkop."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True, slots=True)
class ReportBundle:
    """Immutable bundel met alles wat de renderer nodig heeft.

    - ``details`` is een tuple van meetketens, exact zoals
      MeasurementHistoryService.get_measurement_detail() die teruggeeft.
      Bij één meting is dat een tuple van lengte 1.
    - ``taal`` is de actieve app-taal op het moment van genereren.
    - ``rapportdatum`` is een lokale timestamp-string (YYYY-MM-DD HH:MM:SS).
    - ``app_versie`` komt uit app/version.py.
    - ``werkplaats`` is optioneel (leeg = niet opnemen in de kop).
    - ``scope`` is een vrije label-string die de GUI kan gebruiken in de kop;
      leeg betekent "geen expliciete scope".
    """

    details: tuple[dict[str, Any], ...]
    taal: str
    rapportdatum: str
    app_versie: str
    werkplaats: str = ""
    scope: str = ""

    @property
    def detail(self) -> dict[str, Any]:
        """Backward-compatible: eerste (en bij één meting enige) detail."""
        if not self.details:
            raise ValueError("ReportBundle bevat geen details.")
        return self.details[0]

    @property
    def aantal_metingen(self) -> int:
        return len(self.details)

    @property
    def measurement_id(self) -> int:
        """Alleen zinvol bij één meting; anders de eerste."""
        return int(self.detail["measurement"].id)

    @property
    def tool_key(self) -> str:
        return str(self.detail["measurement"].tool_key)


class ReportService:
    """Read-only service die meetketens bundelt tot een ReportBundle."""

    def __init__(
        self,
        *,
        history_service: MeasurementHistoryService | None = None,
    ) -> None:
        self._history_service = history_service or MeasurementHistoryService()

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def build_bundle(
        self,
        measurement_id: int,
        *,
        taal: str,
        werkplaats: str = "",
        rapportdatum: str | None = None,
    ) -> ReportBundle:
        """Bundel één meting (backward-compatible dunne wrapper)."""
        return self.build_bundle_for_measurements(
            [measurement_id],
            taal=taal,
            werkplaats=werkplaats,
            rapportdatum=rapportdatum,
        )

    def build_bundle_for_measurements(
        self,
        measurement_ids: list[int],
        *,
        taal: str,
        werkplaats: str = "",
        rapportdatum: str | None = None,
        scope: str = "",
    ) -> ReportBundle:
        """Bundel een expliciete lijst metingen, read-only.

        Lege lijst geeft ValueError. Volgorde in het rapport is oplopend
        op measured_at_ms (oud → nieuw), consistent met de analyse-tijdreeksen.
        Dubbele id's worden genegeerd.
        """
        if not isinstance(measurement_ids, list):
            raise ValueError("measurement_ids moet een lijst zijn.")

        unieke_ids: list[int] = []
        gezien: set[int] = set()
        for measurement_id in measurement_ids:
            if (
                isinstance(measurement_id, bool)
                or not isinstance(measurement_id, int)
                or measurement_id < 1
            ):
                raise ValueError(
                    "Elke measurement_id moet een positieve integer zijn."
                )
            if measurement_id in gezien:
                continue
            gezien.add(measurement_id)
            unieke_ids.append(measurement_id)

        if not unieke_ids:
            raise ValueError("Geen metingen opgegeven voor het rapport.")

        details: list[dict[str, Any]] = []
        for measurement_id in unieke_ids:
            detail = self._history_service.get_measurement_detail(measurement_id)
            if detail is None:
                raise ValueError(
                    f"Geen meetdetail gevonden voor measurement_id={measurement_id}."
                )
            details.append(detail)

        details.sort(key=lambda d: int(d["measurement"].measured_at_ms))

        return ReportBundle(
            details=tuple(details),
            taal=taal,
            rapportdatum=rapportdatum or _nu_iso(),
            app_versie=_APP_VERSION,
            werkplaats=werkplaats.strip(),
            scope=scope.strip(),
        )

    def build_bundle_from_filters(
        self,
        filters: Mapping[str, Any] | None,
        *,
        taal: str,
        werkplaats: str = "",
        rapportdatum: str | None = None,
        scope: str = "",
        max_metingen: int = 500,
    ) -> ReportBundle:
        """Bundel alle metingen die aan de filters voldoen, read-only.

        Leest in pagina's via de history-service. Weigert een lege selectie.
        ``max_metingen`` is een veiligheidsgrens om te vermijden dat een
        rapport per ongeluk duizenden metingen bevat.
        """
        if isinstance(max_metingen, bool) or not isinstance(max_metingen, int) or max_metingen < 1:
            raise ValueError("max_metingen moet een positieve integer zijn.")

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
            if len(rijen) > max_metingen:
                raise ValueError(
                    f"Te veel metingen voor één rapport (>{max_metingen})."
                )
            offset += len(chunk)

        if not rijen:
            raise ValueError("Geen metingen voor deze filters.")

        measurement_ids = [int(rij["measurement"].id) for rij in rijen]
        return self.build_bundle_for_measurements(
            measurement_ids,
            taal=taal,
            werkplaats=werkplaats,
            rapportdatum=rapportdatum,
            scope=scope,
        )