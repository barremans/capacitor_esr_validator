"""
================================================================================
Module:     tests/test_async_worker.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/helpers/async_worker.py (fase 11E.1).
            Geen pytest-qt; offscreen; lokale _app().

            Belangrijk: de aanroeper is eigenaar van de AsyncWorker.
            Elke test bewaart zijn worker in de module-level lijst
            _bewaarde_workers, die aan het einde van de sessie wordt
            leeggemaakt. Zonder die referentie kan de WorkerSignals
            worden opgeruimd voordat de callback is aangeroepen en
            faalt de emit met "Signal source has been deleted".

Wijzigingen:
  v1.0.0 (2026-10-16)  Eerste versie.
  v1.1.0 (2026-10-16)  Workers worden bewaard in _bewaarde_workers,
                        zodat de WorkerSignals blijft leven tot de
                        callback is aangeroepen.
================================================================================
"""

from __future__ import annotations

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

from app.helpers.async_worker import AsyncWorker, run_async


# Bewaar alle gestarte workers tot het einde van de sessie. De
# aanroeper is eigenaar; zonder deze lijst kan de WorkerSignals worden
# opgeruimd voordat de callback is aangeroepen.
_bewaarde_workers: list[AsyncWorker] = []


@pytest.fixture(scope="session", autouse=True)
def _ruim_workers_op_aan_einde():
    yield
    _bewaarde_workers.clear()


def _app():
    return QApplication.instance() or QApplication([])


def _wacht_tot_klaar(timeout_s: float = 3.0) -> None:
    """Laat de event loop draaien tot de globale QThreadPool leeg is."""
    app = _app()
    deadline = time.monotonic() + timeout_s
    pool = QThreadPool.globalInstance()
    while time.monotonic() < deadline:
        app.processEvents()
        if pool.activeThreadCount() == 0:
            app.processEvents()
            return
        time.sleep(0.005)
    raise AssertionError("AsyncWorker werd niet klaar binnen de timeout")


# ---------------------------------------------------------------------------
# AsyncWorker zelf
# ---------------------------------------------------------------------------

def test_async_worker_roept_finished_met_resultaat():
    _app()
    ontvangen: list[object] = []

    worker = AsyncWorker(lambda: 42)
    worker.signals.finished.connect(lambda r: ontvangen.append(r))
    _bewaarde_workers.append(worker)
    QThreadPool.globalInstance().start(worker)

    _wacht_tot_klaar()
    assert ontvangen == [42]


def test_async_worker_roept_failed_met_beschrijving_en_traceback():
    _app()
    fouten: list[tuple[str, str]] = []

    def _faal():
        raise ValueError("gesimuleerd")

    worker = AsyncWorker(_faal)
    worker.signals.failed.connect(lambda kort, tb: fouten.append((kort, tb)))
    _bewaarde_workers.append(worker)
    QThreadPool.globalInstance().start(worker)

    _wacht_tot_klaar()
    assert len(fouten) == 1
    kort, tb = fouten[0]
    assert "ValueError" in kort
    assert "gesimuleerd" in kort
    assert "ValueError" in tb


def test_async_worker_geeft_args_en_kwargs_door():
    _app()
    ontvangen: list[object] = []

    def _fn(a, b, *, c):
        return a + b + c

    worker = AsyncWorker(_fn, 1, 2, c=3)
    worker.signals.finished.connect(lambda r: ontvangen.append(r))
    _bewaarde_workers.append(worker)
    QThreadPool.globalInstance().start(worker)

    _wacht_tot_klaar()
    assert ontvangen == [6]


def test_async_worker_geen_callback_crasht_niet():
    """Zonder aangesloten signalen mag de worker gewoon klaar zijn."""
    _app()
    worker = AsyncWorker(lambda: "ok")
    _bewaarde_workers.append(worker)
    QThreadPool.globalInstance().start(worker)
    _wacht_tot_klaar()


def test_async_worker_meerdere_workers_parallel():
    _app()
    resultaten: list[int] = []

    for waarde in (1, 2, 3):
        worker = AsyncWorker(lambda w=waarde: w * 10)
        worker.signals.finished.connect(lambda r: resultaten.append(r))
        _bewaarde_workers.append(worker)
        QThreadPool.globalInstance().start(worker)

    _wacht_tot_klaar()
    assert sorted(resultaten) == [10, 20, 30]


# ---------------------------------------------------------------------------
# run_async helper
# ---------------------------------------------------------------------------

def test_run_async_roept_on_success():
    _app()
    ontvangen: list[object] = []

    worker = run_async(
        lambda: "hallo",
        on_success=lambda r: ontvangen.append(r),
    )
    _bewaarde_workers.append(worker)

    _wacht_tot_klaar()
    assert ontvangen == ["hallo"]


def test_run_async_roept_on_error():
    _app()
    fouten: list[str] = []

    def _faal():
        raise RuntimeError("kapot")

    worker = run_async(
        _faal,
        on_error=lambda kort, tb: fouten.append(kort),
    )
    _bewaarde_workers.append(worker)

    _wacht_tot_klaar()
    assert len(fouten) == 1
    assert "RuntimeError" in fouten[0]


def test_run_async_zonder_callbacks_werkt():
    _app()
    worker = run_async(lambda: None)
    _bewaarde_workers.append(worker)
    _wacht_tot_klaar()


def test_run_async_geeft_args_en_kwargs_door():
    _app()
    ontvangen: list[object] = []

    worker = run_async(
        lambda a, b, *, c: a * b * c,
        2,
        3,
        c=4,
        on_success=lambda r: ontvangen.append(r),
    )
    _bewaarde_workers.append(worker)

    _wacht_tot_klaar()
    assert ontvangen == [24]