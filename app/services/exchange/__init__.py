"""
================================================================================
Module:     app/services/exchange/__init__.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.4
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Publieke basisexports van het exchange-package (§2.28).

Wijzigingen:
  v1.0.0 (2026-10-22)  Eerste versie (fase 28A): modellen exporteren.
  v1.0.1 (2026-10-23)  Fase 28B: ExportService en bereken_natural_key.
  v1.0.2 (2026-10-23)  Fase 28C: ImportPlanner en
                       HerkomstRepositoryProtocol.
  v1.0.3 (2026-10-23)  Fase 28D: ImportService en HerkomstRepository.
  v1.0.4 (2026-10-23)  Fase 28F: read_envelope toegevoegd aan de
                       publieke exports.
================================================================================
"""

from .export_service import (
    ExportService,
    bereken_natural_key,
    read_envelope,
)
from .import_planner import HerkomstRepositoryProtocol, ImportPlanner
from .import_service import HerkomstRepository, ImportService
from .models import (
    ExchangeError,
    ExportEnvelope,
    ExportedMeasurementChain,
    ImportConflict,
    ImportDecision,
    ImportPlan,
    ImportResult,
)

__all__ = [
    "ExchangeError",
    "ExportEnvelope",
    "ExportService",
    "ExportedMeasurementChain",
    "HerkomstRepository",
    "HerkomstRepositoryProtocol",
    "ImportConflict",
    "ImportDecision",
    "ImportPlan",
    "ImportPlanner",
    "ImportResult",
    "ImportService",
    "bereken_natural_key",
    "read_envelope",
]