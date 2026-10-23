"""
================================================================================
Module:     app/gui/dialogs/exchange_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Modale dialoog voor export/import tussen toestellen (§2.28F).

            Twee tabbladen:
              - Exporteren: selectie of filters exporteren naar een
                .esrexchange.json-bestand.
              - Importeren: een exportbestand inlezen, de conflictanalyse
                tonen, en per rij kiezen tussen overslaan (default) en
                als kopie importeren.

            De dialoog schrijft nooit zelf naar de database; alle writes
            gebeuren via ImportService. Alle reads via ExportService.

            Thema-afhankelijke QTextBrowser-stijl via apply_theme(theme).
            Geen QApplication.setStyleSheet.

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie (fase 28F).
  v1.0.1 (2026-10-23)  Fix: _laad_plan splitst nu in _laad_plan (leest
                       bestand, foutafhandeling) en _toon_plan (GUI-
                       vulling). Zo kan de GUI-tests de tabel vullen
                       zonder een echt bestand te schrijven, en is de
                       scheiding van verantwoordelijkheden duidelijker.
================================================================================
"""

from __future__ import annotations

from dataclasses import replace as _dc_replace
from pathlib import Path
from typing import Any, Mapping

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import normaliseer_thema
from app.helpers.dialog_start_directory import (
    beste_startmap,
    onthoud_startmap,
    startpad_voor_bestand,
)
from app.helpers.i18n import vertaal
from app.services.exchange import (
    ExchangeError,
    ExportEnvelope,
    ExportService,
    ImportDecision,
    ImportPlan,
    ImportPlanner,
    ImportService,
    read_envelope,
)


THEME_COLORS: dict[str, dict[str, str]] = {
    "dark": {
        "state_label": "#C8C8C8",
    },
    "light": {
        "state_label": "#5A5A5A",
    },
}


class ExchangeDialog(QDialog):
    """Dialoog voor export/import tussen toestellen."""

    exchange_completed = Signal()

    def __init__(
        self,
        *,
        taal: str = "nl_NL",
        theme: str = "dark",
        export_service: ExportService | None = None,
        import_planner: ImportPlanner | None = None,
        import_service: ImportService | None = None,
        selected_measurement_ids: list[int] | None = None,
        active_filters: Mapping[str, Any] | None = None,
        initial_tab: str = "export",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self.theme = normaliseer_thema(theme)
        self._export_service = export_service or ExportService()
        self._import_planner = import_planner or ImportPlanner()
        self._import_service = import_service or ImportService()
        self._selected_measurement_ids = list(selected_measurement_ids or [])
        self._active_filters = dict(active_filters or {})

        self._current_plan: ImportPlan | None = None
        self._per_rij_als_kopie: dict[int, bool] = {}

        self.setWindowTitle(self._t("exchange.titel"))
        self.setModal(True)
        self.resize(880, 640)

        self._build_ui()
        self._apply_theme()
        if initial_tab == "import":
            self.tabs.setCurrentIndex(1)

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _colors(self) -> dict[str, str]:
        return THEME_COLORS.get(self.theme, THEME_COLORS["dark"])

    def apply_theme(self, theme: str) -> None:
        nieuw = normaliseer_thema(theme)
        if nieuw == self.theme:
            return
        self.theme = nieuw
        self._apply_theme()

    def _apply_theme(self) -> None:
        colors = self._colors()
        self.state_label.setStyleSheet(
            f"color: {colors['state_label']};"
        )

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_export_tab(), self._t("exchange.tab.exporteren"))
        self.tabs.addTab(self._build_import_tab(), self._t("exchange.tab.importeren"))
        root.addWidget(self.tabs, 1)

        self.state_label = QLabel("")
        self.state_label.setWordWrap(True)
        root.addWidget(self.state_label)

        knoppen = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        knoppen.rejected.connect(self.reject)
        root.addWidget(knoppen)

    def _build_export_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(self._t("exchange.export.uitleg"))
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        self.export_scope_combo = QComboBox()
        self.export_scope_combo.addItem(
            self._t("exchange.export.scope_selectie"), "SELECTED"
        )
        self.export_scope_combo.addItem(
            self._t("exchange.export.scope_filters"), "FILTERED"
        )
        if not self._selected_measurement_ids:
            # Geen selectie: standaard op filters.
            self.export_scope_combo.setCurrentIndex(1)
        if not self._active_filters:
            # Geen filters: selectie-modus forceren.
            self.export_scope_combo.setCurrentIndex(0)
        form.addRow(self._t("exchange.export.scope_label"), self.export_scope_combo)

        self.export_aantal_label = QLabel(self._export_aantal_tekst())
        form.addRow(self._t("exchange.export.aantal_label"), self.export_aantal_label)

        layout.addLayout(form)
        layout.addStretch(1)

        knoppen = QHBoxLayout()
        knoppen.addStretch(1)
        self.export_btn = QPushButton(self._t("exchange.export.knop"))
        self.export_btn.clicked.connect(self._do_export)
        knoppen.addWidget(self.export_btn)
        layout.addLayout(knoppen)
        return tab

    def _build_import_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(self._t("exchange.import.uitleg"))
        info.setWordWrap(True)
        layout.addWidget(info)

        kies_rij = QHBoxLayout()
        self.import_btn = QPushButton(self._t("exchange.import.kies_knop"))
        self.import_btn.clicked.connect(self._kies_import_bestand)
        kies_rij.addWidget(self.import_btn)
        kies_rij.addStretch(1)
        layout.addLayout(kies_rij)

        self.import_bestand_label = QLabel(self._t("exchange.import.geen_bestand"))
        self.import_bestand_label.setWordWrap(True)
        layout.addWidget(self.import_bestand_label)

        self.import_table = QTableWidget(0, 5)
        self.import_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.import_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.import_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.import_table.setAlternatingRowColors(True)
        self.import_table.verticalHeader().setVisible(False)
        self.import_table.setHorizontalHeaderLabels(
            [
                self._t("exchange.import.kolom.index"),
                self._t("exchange.import.kolom.source_id"),
                self._t("exchange.import.kolom.machine"),
                self._t("exchange.import.kolom.beslissing"),
                self._t("exchange.import.kolom.als_kopie"),
            ]
        )
        layout.addWidget(self.import_table, 1)

        self.apply_import_btn = QPushButton(self._t("exchange.import.toepassen_knop"))
        self.apply_import_btn.setEnabled(False)
        self.apply_import_btn.clicked.connect(self._do_import)
        knoppen = QHBoxLayout()
        knoppen.addStretch(1)
        knoppen.addWidget(self.apply_import_btn)
        layout.addLayout(knoppen)
        return tab

    def _export_aantal_tekst(self) -> str:
        if self.export_scope_combo.currentData() == "SELECTED":
            aantal = len(self._selected_measurement_ids)
        else:
            aantal = -1  # onbekend tot we tellen
        if aantal < 0:
            return self._t("exchange.export.aantal_filters")
        return self._t("exchange.export.aantal_selectie", aantal=aantal)

    # ------------------------------------------------------------------
    # Exporteren
    # ------------------------------------------------------------------

    def _do_export(self) -> None:
        scope = self.export_scope_combo.currentData()
        try:
            if scope == "SELECTED":
                if not self._selected_measurement_ids:
                    self.state_label.setText(
                        self._t("exchange.export.geen_selectie")
                    )
                    return
                envelope = self._export_service.export_measurements(
                    list(self._selected_measurement_ids)
                )
            else:
                envelope = self._export_service.export_filters(
                    self._active_filters or None
                )
        except ExchangeError as exc:
            self.state_label.setText(
                self._t("exchange.export.fout", bericht=str(exc))
            )
            return

        standaard = f"exchange_{len(envelope.chains)}metingen.esrexchange.json"
        startpad = startpad_voor_bestand("exchange", standaard)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("exchange.export.dialoog_titel"),
            startpad,
            self._t("exchange.export.bestandsfilter"),
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".esrexchange.json"):
            file_path += ".esrexchange.json"

        try:
            self._export_service.write_envelope(envelope, file_path)
        except ExchangeError as exc:
            self.state_label.setText(
                self._t("exchange.export.fout", bericht=str(exc))
            )
            return

        onthoud_startmap("exchange", Path(file_path))
        self.state_label.setText(
            self._t(
                "exchange.export.geslaagd",
                aantal=len(envelope.chains),
                pad=file_path,
            )
        )
        self.exchange_completed.emit()

    # ------------------------------------------------------------------
    # Importeren
    # ------------------------------------------------------------------

    def _kies_import_bestand(self) -> None:
        startmap = beste_startmap("exchange")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("exchange.import.dialoog_titel"),
            str(startmap) if startmap is not None else "",
            self._t("exchange.import.bestandsfilter"),
        )
        if not file_path:
            return
        self._laad_plan(Path(file_path))

    def _laad_plan(self, path: Path) -> None:
        """Lees het bestand en toon het plan (foutafhandeling inbegrepen)."""
        try:
            envelope = read_envelope(path)
        except ExchangeError as exc:
            self.state_label.setText(
                self._t("exchange.import.fout", bericht=str(exc))
            )
            return
        self._toon_plan(envelope, pad=str(path))

    def _toon_plan(self, envelope: ExportEnvelope, *, pad: str = "") -> None:
        """Toon het plan in de import-tabel; apart van bestand-IO.

        Zo kan de GUI-tests de tabel vullen zonder een echt bestand
        te schrijven, en blijft de scheiding van verantwoordelijkheden
        duidelijk.
        """
        try:
            plan = self._import_planner.plan(envelope)
        except ExchangeError as exc:
            self.state_label.setText(
                self._t("exchange.import.fout", bericht=str(exc))
            )
            return

        self._current_plan = plan
        self._per_rij_als_kopie = {}
        self.import_bestand_label.setText(
            self._t(
                "exchange.import.bestand_gekozen",
                aantal=len(envelope.chains),
                pad=pad,
            )
        )
        self._populate_import_table(plan)
        self.apply_import_btn.setEnabled(bool(envelope.chains))
        self.state_label.setText("")

    def _populate_import_table(self, plan: ImportPlan) -> None:
        self.import_table.blockSignals(True)
        try:
            self.import_table.setRowCount(len(plan.decisions))
            for index, chain in enumerate(plan.envelope.chains):
                decision = plan.decisions[index]
                self.import_table.setItem(
                    index, 0, QTableWidgetItem(str(index + 1))
                )
                self.import_table.setItem(
                    index,
                    1,
                    QTableWidgetItem(str(chain.source_measurement_id)),
                )
                self.import_table.setItem(
                    index,
                    2,
                    QTableWidgetItem(chain.source_machine_id[:8] + "…"),
                )
                self.import_table.setItem(
                    index,
                    3,
                    QTableWidgetItem(self._decision_label(decision)),
                )
                checkbox_item = QTableWidgetItem("")
                checkbox_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                checkbox_item.setData(
                    Qt.ItemDataRole.UserRole, int(chain.source_measurement_id)
                )
                self.import_table.setItem(index, 4, checkbox_item)
        finally:
            self.import_table.blockSignals(False)

    def _decision_label(self, decision: ImportDecision) -> str:
        mapping = {
            ImportDecision.IMPORT_NEW: "exchange.import.decision.nieuw",
            ImportDecision.SKIP_DUPLICATE: "exchange.import.decision.duplicate",
            ImportDecision.IMPORT_AS_CONFLICT_COPY: "exchange.import.decision.kopie",
            ImportDecision.NEEDS_USER_CHOICE: "exchange.import.decision.keuze",
        }
        return self._t(mapping.get(decision, "exchange.import.decision.onbekend"))

    def _do_import(self) -> None:
        if self._current_plan is None:
            return

        per_rij: list[ImportDecision] = []
        for index in range(self.import_table.rowCount()):
            origineel = self._current_plan.decisions[index]
            item = self.import_table.item(index, 4)
            als_kopie = (
                item is not None
                and item.checkState() == Qt.CheckState.Checked
            )
            if als_kopie and origineel in (
                ImportDecision.SKIP_DUPLICATE,
                ImportDecision.NEEDS_USER_CHOICE,
            ):
                per_rij.append(ImportDecision.IMPORT_AS_CONFLICT_COPY)
            else:
                per_rij.append(origineel)

        plan = _dc_replace(
            self._current_plan, decisions=tuple(per_rij)
        )

        try:
            result = self._import_service.apply_plan(plan)
        except ExchangeError as exc:
            self.state_label.setText(
                self._t("exchange.import.fout", bericht=str(exc))
            )
            return

        self.state_label.setText(
            self._t(
                "exchange.import.klaar",
                geimporteerd=result.imported_count,
                kopie=result.conflict_copy_count,
                overgeslagen=result.skipped_duplicate_count,
                fouten=len(result.errors),
            )
        )
        if result.has_errors:
            self.state_label.setText(
                self.state_label.text()
                + "\n"
                + "\n".join(result.errors)
            )
        self.apply_import_btn.setEnabled(False)
        self.exchange_completed.emit()