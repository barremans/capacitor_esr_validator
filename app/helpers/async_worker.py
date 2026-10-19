"""
================================================================================
Module:     app/helpers/async_worker.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     2.0.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Generieke Qt-helper om een synchrone functie in een
            achtergrondthread uit te voeren zonder de GUI-thread te
            blokkeren. Gebaseerd op QThreadPool + QRunnable.

            Bewust GEEN netwerklogica, GEEN domeinkennis.

            **Eigenaarschap — belangrijk:**
            De aanroeper van run_async() is eigenaar van de
            teruggegeven AsyncWorker. Die moet de referentie bewaren
            zolang de worker bezig is. Zodra de aanroeper de referentie
            laat vallen, kan de WorkerSignals worden opgeruimd en
            faalt de emit met "Signal source has been deleted". Dit is
            dezelfde conventie als bij QNetworkAccessManager: de
            aanroeper is eigenaar.

            In de GUI bewaart ToolHubWindow de worker in
            self._update_check_worker / self._release_notes_worker.
            In tests moet de test de worker in een lijst bewaren tot
            de callback is aangeroepen.

Wijzigingen:
  v1.0.0 (2026-10-16)  Eerste versie (fase 11E.1).
  v1.0.1 (2026-10-16)  setAutoDelete(False) + sterke registry. De
                        registry ruimde de worker op tijdens de emit
                        en veroorzaakte "Signal source has been
                        deleted".
  v1.0.2 (2026-10-16)  QTimer.singleShot in de worker-thread. Faalde.
  v1.0.3 (2026-10-16)  QMetaObject.invokeMethod. AsyncWorker is geen
                        QObject. Faalde.
  v1.1.0 (2026-10-16)  WeakSet. De tests lieten de worker vallen.
                        Faalde.
  v1.2.0 (2026-10-16)  Module-level QObject als parent. De parent
                        werd opgeruimd door de garbage collector
                        voordat de laatste workers klaar waren.
                        Faalde.
  v2.0.0 (2026-10-16)  Definitieve oplossing. Terug naar de simpelste
                        correcte vorm: WorkerSignals als sterk
                        Python-attribuut op de worker, setAutoDelete
                        (False), geen registry. De aanroeper is
                        eigenaar en moet de worker bewaren. De tests
                        zijn aangepast zodat ze de worker bewaren.
================================================================================
"""

from __future__ import annotations

import traceback
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class WorkerSignals(QObject):
    """Signalen die een AsyncWorker uitzendt.

    - finished(object): de callable is klaar; het resultaat is de return.
    - failed(str, str): de callable heeft een exception gegooid; de
      eerste string is een korte weergave (type + message), de tweede
      is het volledige traceback.

    De signalen worden altijd in de GUI-thread afgeleverd (Qt doet dat
    automatisch voor cross-thread signalen naar een QObject dat in de
    GUI-thread leeft).

    Levensduur: de WorkerSignals wordt vastgehouden door de
    AsyncWorker via een sterk Python-attribuut. Zolang de AsyncWorker
    leeft, leeft de WorkerSignals. De aanroeper van run_async() is
    eigenaar van de AsyncWorker.
    """

    finished = Signal(object)
    failed = Signal(str, str)


class AsyncWorker(QRunnable):
    """Voert één callable uit in een achtergrondthread.

    Gebruik:
        worker = AsyncWorker(fn, arg1, arg2, kwarg=waarde)
        worker.signals.finished.connect(on_success)
        worker.signals.failed.connect(on_error)
        QThreadPool.globalInstance().start(worker)

    Of gebruik de helper `run_async(...)` hieronder.

    **Levensduur — belangrijk:** de aanroeper MOET de return-waarde
    van run_async() (of de AsyncWorker zelf) bewaren zolang de worker
    bezig is. Zodra de aanroeper de referentie laat vallen, kan de
    WorkerSignals worden opgeruimd en faalt de emit met
    "Signal source has been deleted".

    `setAutoDelete(False)` zorgt ervoor dat Qt de Python-wrapper niet
    halverwege opruimt; de aanroeper doet dat.
    """

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        # Sterk Python-attribuut: de worker houdt zijn eigen signalen
        # vast. Zolang de worker leeft, leven de signalen.
        self.signals = WorkerSignals()
        # Qt mag de Python-wrapper niet opruimen; de aanroeper doet dat.
        self.setAutoDelete(False)

    @Slot()
    def run(self) -> None:  # noqa: D401 — Qt-API
        """Qt entry point. Voert de callable uit en zendt het resultaat."""
        try:
            resultaat = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 — bewust breed
            kort = f"{type(exc).__name__}: {exc}"
            volledig = traceback.format_exc()
            self.signals.failed.emit(kort, volledig)
            return
        self.signals.finished.emit(resultaat)


def run_async(
    fn: Callable[..., Any],
    *args: Any,
    on_success: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[str, str], None]] = None,
    **kwargs: Any,
) -> AsyncWorker:
    """Start `fn(*args, **kwargs)` in een achtergrondthread.

    Parameters
    ----------
    fn:
        De synchrone functie die uitgevoerd moet worden.
    on_success:
        Wordt aangeroepen in de GUI-thread met het resultaat van `fn`.
        Mag None zijn.
    on_error:
        Wordt aangeroepen in de GUI-thread met een korte beschrijving
        en het volledige traceback. Mag None zijn.
    *args, **kwargs:
        Doorgegeven aan `fn`.

    Returns
    -------
    AsyncWorker
        De gestarte worker. **De aanroeper MOET deze referentie
        bewaren zolang de worker bezig is.** Zonder die referentie kan
        de worker worden opgeruimd en faalt de emit met
        "Signal source has been deleted".
    """
    worker = AsyncWorker(fn, *args, **kwargs)
    if on_success is not None:
        worker.signals.finished.connect(on_success)
    if on_error is not None:
        worker.signals.failed.connect(on_error)
    QThreadPool.globalInstance().start(worker)
    return worker