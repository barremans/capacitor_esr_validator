"""
================================================================================
Module:     app/gui/history_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.13.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Compacte centrale read-only weergave van opgeslagen meethistoriek.

            Toont per meting datum/tijd, componentidentiteit, meetmethode,
            instrument, gemeten capaciteit, ESR, eindstatus en betrouwbaarheid.
            De pagina blijft read-only en biedt daarnaast een detaildialoog
            voor de volledige opgeslagen meetketen, assessments en referenties.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste compacte historiekpagina met verversen, lege-state
                        en foutmelding; gekoppeld aan MeasurementHistoryService.
  v1.1.0 (2026-10-01)  Read-only detaildialoog toegevoegd.
  v1.2.0 (2026-10-01)  "Herhaal meting" toegevoegd.
  v1.3.0 (2026-10-01)  Compacte read-only filterbalk.
  v1.4.0 (2026-10-01)  Multitool-historiek: Tool/Testtype-filter en tabelkolom.
  v1.5.0 (2026-10-01)  Tabel tool-neutraal met één kolom Meetwaarden.
  v1.5.1 (2026-10-01)  Live taalwissel vervolledigd.
  v1.5.2 (2026-10-01)  Fout-refresh maakt selectie-afhankelijke acties inactief.
  v1.6.0 (2026-10-01)  Optionele Van/Tot-datumfilter.
  v1.6.1 (2026-10-01)  Initialisatievolgorde datumvelden gecorrigeerd.
  v1.6.2 (2026-10-01)  Filtervalidatiefouten vertaald getoond.
  v1.7.0 (2026-10-01)  Historiekpaging via limit/offset-contract.
  v1.8.0 (2026-10-01)  Read-only CSV-export van de volledige filterselectie.
  v1.9.0 (2026-10-02)  Export v2: compact inklapbaar filterpaneel, exportscope,
                        aparte overzicht- en detail-CSV.
  v1.10.0 (2026-10-02) Exportdialoog gebruikt de ingestelde standaard exportmap.
  v1.11.0 (2026-10-02) Laatste export-UX: checkboxselectie, exporttype-DDL,
                        één Exporteren-knop, leesbare timestamp.
  v1.12.0 (2026-10-05) Sneltoetsen toegevoegd (Fase 4F).
  v1.13.0 (2026-10-07) Fase 5D'.3: exportdialoog start in laatste_exportmap
                        (indien geldig), anders standaard_exportmap. Na een
                        geslaagde export wordt laatste_exportmap bijgewerkt
                        en opgeslagen.
================================================================================
"""

from __future__ import annotations

from dataclasses import replace as _dc_replace
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import (
    AppInstellingen,
    laad_instellingen,
    sla_instellingen_op,
)
from app.helpers.i18n import vertaal
from app.helpers.history_csv_export import write_history_csv
from app.helpers.history_detail_export import (
    DETAIL_EXPORT_HEADERS,
    detail_row_values,
)
from app.helpers.history_filters import (
    build_history_filters,
    parse_local_date_start_ms,
    parse_local_date_end_ms,
)
from app.services.history_service import MeasurementHistoryService
from app.services.repeat_measurement_service import build_repeat_measurement_preset


from app.helpers.history_formatting import (
    component_label,
    format_capacitance_f,
    format_esr_ohm,
    format_local_datetime,
    format_bool,
    format_optional_number,
    decode_json_list,
    format_measurement_values,
    measurement_method_translation_key,
)


class HistoryScreen(QWidget):
    """Read-only historiekpagina binnen het hoofdvenster."""

    back_requested = Signal()
    repeat_requested = Signal(object)

    def __init__(
        self,
        taal: str = "nl_NL",
        *,
        history_service: MeasurementHistoryService | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self._history_service = history_service or MeasurementHistoryService()
        self._page_size = 100
        self._page_index = 0
        self._has_next_page = False
        self._current_rows: list[dict[str, Any]] = []
        self._build_ui()
        self._install_shortcuts()

    def _install_shortcuts(self) -> None:
        """Lokale sneltoetsen voor de historiekpagina (Fase 4F)."""
        ctx = Qt.ShortcutContext.WidgetWithChildrenShortcut

        self.sc_back = QShortcut(QKeySequence("Esc"), self)
        self.sc_back.setContext(ctx)
        self.sc_back.activated.connect(self.back_requested.emit)

        self.sc_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        self.sc_refresh.setContext(ctx)
        self.sc_refresh.activated.connect(self.refresh)

        self.sc_focus_filter = QShortcut(QKeySequence("Ctrl+F"), self)
        self.sc_focus_filter.setContext(ctx)
        self.sc_focus_filter.activated.connect(self._focus_filters)

        self.sc_detail = QShortcut(QKeySequence("Ctrl+D"), self)
        self.sc_detail.setContext(ctx)
        self.sc_detail.activated.connect(self._on_detail_shortcut)

        self.sc_repeat = QShortcut(QKeySequence("Ctrl+H"), self)
        self.sc_repeat.setContext(ctx)
        self.sc_repeat.activated.connect(self._on_repeat_shortcut)

    def _focus_filters(self) -> None:
        """Open filterpaneel en zet focus op het eerste filterveld."""
        self.filter_group.setChecked(True)
        self.filter_body.setVisible(True)
        self.filter_tool.setFocus()

    def _on_detail_shortcut(self) -> None:
        if not self.detail_btn.isEnabled():
            return
        self._show_selected_detail()

    def _on_repeat_shortcut(self) -> None:
        if not self.repeat_btn.isEnabled():
            return
        self._repeat_selected_measurement()

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.back_btn = QPushButton(self._t("knop.terug"))
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.back_requested.emit)
        top.addWidget(self.back_btn)

        self.title_label = QLabel(self._t("scherm.historiek"))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top.addWidget(self.title_label)
        top.addStretch(1)

        self.export_scope = QComboBox()
        self._fill_export_scope()
        self.export_scope.setMinimumWidth(190)
        top.addWidget(self.export_scope)

        self.selection_count_label = QLabel("")
        top.addWidget(self.selection_count_label)

        self.export_type_combo = QComboBox()
        self._fill_export_type()
        self.export_type_combo.setMinimumWidth(165)
        top.addWidget(self.export_type_combo)

        self.export_btn = QPushButton(self._t("historiek.export.knop"))
        self.export_btn.clicked.connect(self._export_selected_type)
        top.addWidget(self.export_btn)

        # Compatibiliteitsalias voor bestaande tests/aanroepers.
        self.export_csv_btn = self.export_btn

        self.refresh_btn = QPushButton(self._t("knop.verversen"))
        self.refresh_btn.clicked.connect(self.refresh)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        self.filter_group = QGroupBox(self._t("historiek.filter.titel"))
        self.filter_group.setCheckable(True)
        self.filter_group.setChecked(False)
        filter_layout = QVBoxLayout(self.filter_group)

        self.filter_body = QWidget()
        filter_body_layout = QVBoxLayout(self.filter_body)
        filter_body_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_form = QFormLayout()
        self.filter_form.setHorizontalSpacing(10)
        self.filter_form.setVerticalSpacing(6)

        self.filter_tool = QComboBox()
        self._fill_tool_filter()
        self.filter_tool_label = QLabel(self._t("historiek.filter.tool"))
        self.filter_form.addRow(self.filter_tool_label, self.filter_tool)

        self.filter_manufacturer = QLineEdit()
        self.filter_manufacturer.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.filter_manufacturer_label = QLabel(self._t("historiek.filter.fabrikant"))
        self.filter_form.addRow(self.filter_manufacturer_label, self.filter_manufacturer)

        self.filter_series = QLineEdit()
        self.filter_series.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.filter_series_label = QLabel(self._t("historiek.filter.serie"))
        self.filter_form.addRow(self.filter_series_label, self.filter_series)

        self.filter_date_from = QLineEdit()
        self.filter_date_from.setPlaceholderText(
            self._t("historiek.filter.datum_placeholder")
        )
        self.filter_date_from_label = QLabel(self._t("historiek.filter.datum_van"))
        self.filter_form.addRow(self.filter_date_from_label, self.filter_date_from)

        self.filter_date_to = QLineEdit()
        self.filter_date_to.setPlaceholderText(
            self._t("historiek.filter.datum_placeholder")
        )
        self.filter_date_to_label = QLabel(self._t("historiek.filter.datum_tot"))
        self.filter_form.addRow(self.filter_date_to_label, self.filter_date_to)

        self.filter_method = QComboBox()
        self._fill_method_filter()
        self.filter_method_label = QLabel(self._t("historiek.filter.meetmethode"))
        self.filter_form.addRow(self.filter_method_label, self.filter_method)

        self.filter_instrument = QLineEdit()
        self.filter_instrument.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.filter_instrument_label = QLabel(self._t("historiek.filter.instrument"))
        self.filter_form.addRow(self.filter_instrument_label, self.filter_instrument)

        self.filter_frequency = QComboBox()
        self._fill_frequency_filter()
        self.filter_frequency_label = QLabel(self._t("historiek.filter.frequentie"))
        self.filter_form.addRow(self.filter_frequency_label, self.filter_frequency)

        self.filter_status = QComboBox()
        self._fill_status_filter()
        self.filter_status_label = QLabel(self._t("historiek.filter.status"))
        self.filter_form.addRow(self.filter_status_label, self.filter_status)

        self.filter_reliability = QComboBox()
        self._fill_reliability_filter()
        self.filter_reliability_label = QLabel(self._t("historiek.filter.betrouwbaarheid"))
        self.filter_form.addRow(self.filter_reliability_label, self.filter_reliability)

        filter_body_layout.addLayout(self.filter_form)

        filter_buttons = QHBoxLayout()
        filter_buttons.addStretch(1)
        self.clear_filters_btn = QPushButton(self._t("historiek.filter.wissen"))
        self.clear_filters_btn.clicked.connect(self._clear_filters)
        filter_buttons.addWidget(self.clear_filters_btn)
        self.apply_filters_btn = QPushButton(self._t("historiek.filter.toepassen"))
        self.apply_filters_btn.clicked.connect(self._apply_filters)
        filter_buttons.addWidget(self.apply_filters_btn)
        filter_body_layout.addLayout(filter_buttons)
        filter_layout.addWidget(self.filter_body)
        self.filter_body.setVisible(False)
        self.filter_group.toggled.connect(self.filter_body.setVisible)
        root.addWidget(self.filter_group)

        self.state_label = QLabel("")
        self.state_label.setWordWrap(True)
        self.state_label.setStyleSheet("color: #C8C8C8;")
        root.addWidget(self.state_label)

        self.table = QTableWidget(0, 9)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.itemSelectionChanged.connect(self._update_detail_button)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.itemDoubleClicked.connect(lambda _item: self._show_selected_detail())
        root.addWidget(self.table, 1)

        bottom = QHBoxLayout()

        self.previous_page_btn = QPushButton(self._t("historiek.paging.vorige"))
        self.previous_page_btn.clicked.connect(self._previous_page)
        bottom.addWidget(self.previous_page_btn)

        self.page_label = QLabel("")
        bottom.addWidget(self.page_label)

        self.next_page_btn = QPushButton(self._t("historiek.paging.volgende"))
        self.next_page_btn.clicked.connect(self._next_page)
        bottom.addWidget(self.next_page_btn)

        bottom.addStretch(1)

        self.repeat_btn = QPushButton(self._t("knop.herhaal_meting"))
        self.repeat_btn.setEnabled(False)
        self.repeat_btn.clicked.connect(self._repeat_selected_measurement)
        bottom.addWidget(self.repeat_btn)

        self.detail_btn = QPushButton(self._t("knop.details"))
        self.detail_btn.setEnabled(False)
        self.detail_btn.clicked.connect(self._show_selected_detail)
        bottom.addWidget(self.detail_btn)
        root.addLayout(bottom)

        self._apply_headers()
        self._update_selection_count()
        self._update_paging_controls()

    def _column_headers(self) -> list[str]:
        """Mensleesbare overzicht-CSV-kolommen; bevat geen GUI-selectiekolom."""
        return [
            self._t("historiek.kolom.datum_tijd"),
            self._t("historiek.kolom.tool"),
            self._t("historiek.kolom.component"),
            self._t("historiek.kolom.meetmethode"),
            self._t("historiek.kolom.instrument"),
            self._t("historiek.kolom.meetwaarden"),
            self._t("historiek.kolom.status"),
            self._t("historiek.kolom.betrouwbaarheid"),
        ]

    def _table_headers(self) -> list[str]:
        return [self._t("historiek.kolom.selectie"), *self._column_headers()]

    def _apply_headers(self) -> None:
        self.table.setHorizontalHeaderLabels(self._table_headers())
        header = self.table.horizontalHeader()
        for column in range(self.table.columnCount()):
            header.setStretchLastSection(False)
            self.table.resizeColumnToContents(column)
        self.table.setColumnWidth(0, max(48, self.table.columnWidth(0)))
        header.setStretchLastSection(True)

    def _fill_export_scope(self) -> None:
        current = self.export_scope.currentData() if self.export_scope.count() else "FILTERED"
        self.export_scope.clear()
        self.export_scope.addItem(
            self._t("historiek.export.scope_gefilterd"),
            "FILTERED",
        )
        self.export_scope.addItem(
            self._t("historiek.export.scope_geselecteerd"),
            "SELECTED",
        )
        self.export_scope.addItem(
            self._t("historiek.export.scope_pagina"),
            "PAGE",
        )
        index = self.export_scope.findData(current)
        self.export_scope.setCurrentIndex(index if index >= 0 else 0)

    def _fill_export_type(self) -> None:
        current = (
            self.export_type_combo.currentData()
            if hasattr(self, "export_type_combo") and self.export_type_combo.count()
            else "OVERVIEW"
        )
        self.export_type_combo.clear()
        self.export_type_combo.addItem(
            self._t("historiek.export.type_overzicht"),
            "OVERVIEW",
        )
        self.export_type_combo.addItem(
            self._t("historiek.export.type_detail"),
            "DETAIL",
        )
        self.export_type_combo.addItem(
            self._t("historiek.export.type_beide"),
            "BOTH",
        )
        index = self.export_type_combo.findData(current)
        self.export_type_combo.setCurrentIndex(index if index >= 0 else 0)

    def _fill_tool_filter(self) -> None:
        current = self.filter_tool.currentData() if self.filter_tool.count() else None
        self.filter_tool.clear()
        self.filter_tool.addItem(self._t("historiek.filter.alle"), None)
        self.filter_tool.addItem(self._tool_label("ESR_CAPACITOR"), "ESR_CAPACITOR")
        index = self.filter_tool.findData(current)
        self.filter_tool.setCurrentIndex(index if index >= 0 else 0)

    def _tool_label(self, tool_key: str | None) -> str:
        if not tool_key:
            return "—"
        translated = self._t(f"tool_type.{tool_key}")
        return tool_key if translated == f"tool_type.{tool_key}" else translated

    def _fill_method_filter(self) -> None:
        current = self.filter_method.currentData() if self.filter_method.count() else None
        self.filter_method.clear()
        self.filter_method.addItem(self._t("historiek.filter.alle"), None)
        for value in ("EX_SITU", "ONE_LEG", "IN_CIRCUIT"):
            self.filter_method.addItem(
                self._t(measurement_method_translation_key(value)), value
            )
        index = self.filter_method.findData(current)
        self.filter_method.setCurrentIndex(index if index >= 0 else 0)

    def _fill_frequency_filter(self) -> None:
        current = self.filter_frequency.currentData() if self.filter_frequency.count() else None
        self.filter_frequency.clear()
        self.filter_frequency.addItem(self._t("historiek.filter.alle"), None)
        for frequency in (100.0, 1000.0, 10000.0):
            label = f"{frequency:g} Hz" if frequency < 1000 else f"{frequency / 1000:g} kHz"
            self.filter_frequency.addItem(label, frequency)
        index = self.filter_frequency.findData(current)
        self.filter_frequency.setCurrentIndex(index if index >= 0 else 0)

    def _fill_status_filter(self) -> None:
        current = self.filter_status.currentData() if self.filter_status.count() else None
        self.filter_status.clear()
        self.filter_status.addItem(self._t("historiek.filter.alle"), None)
        for value in (
            "niet_beoordeeld",
            "waarschijnlijk_goed",
            "aandachtspunt",
            "twijfelachtig",
            "waarschijnlijk_defect",
            "niet_te_beoordelen",
        ):
            self.filter_status.addItem(self._t(f"status.eindstatus.{value}"), value)
        index = self.filter_status.findData(current)
        self.filter_status.setCurrentIndex(index if index >= 0 else 0)

    def _fill_reliability_filter(self) -> None:
        current = self.filter_reliability.currentData() if self.filter_reliability.count() else None
        self.filter_reliability.clear()
        self.filter_reliability.addItem(self._t("historiek.filter.alle"), None)
        for value in ("hoog", "middel", "laag"):
            self.filter_reliability.addItem(
                self._t(f"status.betrouwbaarheid.{value}"), value
            )
        index = self.filter_reliability.findData(current)
        self.filter_reliability.setCurrentIndex(index if index >= 0 else 0)

    def _active_filters(self) -> dict[str, Any]:
        try:
            measured_from_ms = parse_local_date_start_ms(
                self.filter_date_from.text()
            )
            measured_to_ms = parse_local_date_end_ms(
                self.filter_date_to.text()
            )
        except ValueError as exc:
            raise ValueError(
                self._t("historiek.filter.datum_formaat_fout")
            ) from exc

        if (
            measured_from_ms is not None
            and measured_to_ms is not None
            and measured_from_ms > measured_to_ms
        ):
            raise ValueError(self._t("historiek.filter.datum_volgorde_fout"))

        return build_history_filters(
            tool_key=self.filter_tool.currentData(),
            manufacturer=self.filter_manufacturer.text(),
            series=self.filter_series.text(),
            measurement_method=self.filter_method.currentData(),
            instrument_key=self.filter_instrument.text(),
            frequency_hz=self.filter_frequency.currentData(),
            final_status=self.filter_status.currentData(),
            reliability_level=self.filter_reliability.currentData(),
            measured_from_ms=measured_from_ms,
            measured_to_ms=measured_to_ms,
        )

    def _clear_filters(self) -> None:
        self.filter_tool.setCurrentIndex(0)
        self.filter_manufacturer.clear()
        self.filter_series.clear()
        self.filter_date_from.clear()
        self.filter_date_to.clear()
        self.filter_method.setCurrentIndex(0)
        self.filter_instrument.clear()
        self.filter_frequency.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(0)
        self.filter_reliability.setCurrentIndex(0)
        self._page_index = 0
        self.refresh()

    def apply_language(self, taal: str) -> None:
        self.taal = taal
        self.back_btn.setText(self._t("knop.terug"))
        self.title_label.setText(self._t("scherm.historiek"))
        self.refresh_btn.setText(self._t("knop.verversen"))
        self.export_btn.setText(self._t("historiek.export.knop"))
        self.detail_btn.setText(self._t("knop.details"))
        self.repeat_btn.setText(self._t("knop.herhaal_meting"))
        self.previous_page_btn.setText(self._t("historiek.paging.vorige"))
        self.next_page_btn.setText(self._t("historiek.paging.volgende"))
        self.filter_group.setTitle(self._t("historiek.filter.titel"))
        self.filter_tool_label.setText(self._t("historiek.filter.tool"))
        self.filter_manufacturer_label.setText(self._t("historiek.filter.fabrikant"))
        self.filter_series_label.setText(self._t("historiek.filter.serie"))
        self.filter_date_from_label.setText(self._t("historiek.filter.datum_van"))
        self.filter_date_to_label.setText(self._t("historiek.filter.datum_tot"))
        self.filter_method_label.setText(self._t("historiek.filter.meetmethode"))
        self.filter_instrument_label.setText(self._t("historiek.filter.instrument"))
        self.filter_frequency_label.setText(self._t("historiek.filter.frequentie"))
        self.filter_status_label.setText(self._t("historiek.filter.status"))
        self.filter_reliability_label.setText(self._t("historiek.filter.betrouwbaarheid"))
        self.filter_manufacturer.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.filter_series.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.filter_date_from.setPlaceholderText(self._t("historiek.filter.datum_placeholder"))
        self.filter_date_to.setPlaceholderText(self._t("historiek.filter.datum_placeholder"))
        self.filter_instrument.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.clear_filters_btn.setText(self._t("historiek.filter.wissen"))
        self.apply_filters_btn.setText(self._t("historiek.filter.toepassen"))
        self._fill_export_scope()
        self._fill_export_type()
        self._fill_tool_filter()
        self._fill_method_filter()
        self._fill_frequency_filter()
        self._fill_status_filter()
        self._fill_reliability_filter()
        self._apply_headers()
        self._update_paging_controls()

    def refresh(self) -> None:
        try:
            filters = self._active_filters()
        except ValueError as exc:
            self._update_detail_button()
            self.state_label.setText(str(exc))
            return

        offset = self._page_index * self._page_size
        try:
            rows_with_lookahead = self._history_service.list_measurements(
                filters,
                limit=self._page_size + 1,
                offset=offset,
            )
        except Exception as exc:
            self.table.setRowCount(0)
            self._current_rows = []
            self._has_next_page = False
            self._update_detail_button()
            self._update_paging_controls()
            self.state_label.setText(self._t("historiek.fout", bericht=str(exc)))
            return

        self._has_next_page = len(rows_with_lookahead) > self._page_size
        rows = rows_with_lookahead[: self._page_size]
        self._current_rows = list(rows)

        self._populate(rows)
        self._update_detail_button()
        self._update_paging_controls()
        if rows:
            self.state_label.setText(self._t("historiek.aantal", aantal=len(rows)))
        else:
            self.state_label.setText(self._t("historiek.leeg"))

    def _apply_filters(self) -> None:
        self._page_index = 0
        self.refresh()

    def _previous_page(self) -> None:
        if self._page_index <= 0:
            return
        self._page_index -= 1
        self.refresh()

    def _next_page(self) -> None:
        if not self._has_next_page:
            return
        self._page_index += 1
        self.refresh()

    def _update_paging_controls(self) -> None:
        self.previous_page_btn.setEnabled(self._page_index > 0)
        self.next_page_btn.setEnabled(self._has_next_page)
        self.page_label.setText(
            self._t("historiek.paging.pagina", pagina=self._page_index + 1)
        )

    def _load_all_filtered_rows_for_export(
        self,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        chunk_size = 500
        offset = 0

        while True:
            chunk = self._history_service.list_measurements(
                filters,
                limit=chunk_size,
                offset=offset,
            )
            rows.extend(chunk)
            if len(chunk) < chunk_size:
                break
            offset += len(chunk)

        return rows

    def _selected_measurement_ids(self) -> list[int]:
        """Exportselectie komt uitsluitend uit de expliciete checkboxkolom."""
        ids: list[int] = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None or item.checkState() != Qt.CheckState.Checked:
                continue
            value = item.data(Qt.ItemDataRole.UserRole)
            if value is not None:
                ids.append(int(value))
        return ids

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == 0:
            self._update_selection_count()

    def _update_selection_count(self) -> None:
        aantal = len(self._selected_measurement_ids()) if hasattr(self, "table") else 0
        self.selection_count_label.setText(
            self._t("historiek.export.geselecteerd_aantal", aantal=aantal)
        )

    def _rows_for_export(
        self,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]] | None:
        scope = self.export_scope.currentData()

        if scope == "PAGE":
            return list(self._current_rows)

        if scope == "SELECTED":
            selected_ids = set(self._selected_measurement_ids())
            if not selected_ids:
                self.state_label.setText(
                    self._t("historiek.export.geen_selectie")
                )
                return None
            return [
                row
                for row in self._current_rows
                if row["measurement"].id in selected_ids
            ]

        return self._load_all_filtered_rows_for_export(filters)

    # ------------------------------------------------------------------ export-mappen

    @staticmethod
    def _map_bestaat(pad: str) -> bool:
        """Controleer of pad een bestaande map is."""
        if not pad:
            return False
        try:
            return Path(pad).expanduser().is_dir()
        except (OSError, ValueError):
            return False

    def _laatste_export_directory(self) -> Path | None:
        """Lees laatste_exportmap uit settings als die een geldige map is."""
        try:
            instellingen = laad_instellingen()
        except (OSError, ValueError):
            return None
        laatste = instellingen.algemeen.laatste_exportmap
        if not self._map_bestaat(laatste):
            return None
        return Path(laatste).expanduser()

    def _configured_export_directory(self) -> Path | None:
        """Lees standaard_exportmap uit settings als die een geldige map is."""
        instellingen = laad_instellingen()
        configured = instellingen.algemeen.standaard_exportmap.strip()
        if not configured:
            return None
        directory = Path(configured).expanduser()
        return directory if directory.is_dir() else None

    def _beste_export_start_directory(self) -> Path | None:
        """Beste startmap voor exportdialogen.

        Voorkeur:
          1. laatste_exportmap als die een bestaande map is
          2. standaard_exportmap als die een bestaande map is
          3. None (Qt's standaard startlocatie)
        """
        laatste = self._laatste_export_directory()
        if laatste is not None:
            return laatste
        return self._configured_export_directory()

    def _onthoud_laatste_exportmap(self, doel_pad: Path) -> None:
        """Werk laatste_exportmap bij na een geslaagde export.

        doel_pad mag een bestand of een map zijn. Voor een bestand nemen
        we de parent. Faalt stil: het onthouden van de map is een
        gemaksfunctie, geen kernfunctionaliteit.
        """
        try:
            if doel_pad.is_dir():
                nieuwe_map = str(doel_pad)
            else:
                nieuwe_map = str(doel_pad.parent)

            instellingen = laad_instellingen()
            if instellingen.algemeen.laatste_exportmap == nieuwe_map:
                return
            bijgewerkt = _dc_replace(
                instellingen,
                algemeen=_dc_replace(
                    instellingen.algemeen,
                    laatste_exportmap=nieuwe_map,
                ),
            )
            sla_instellingen_op(bijgewerkt)
        except (OSError, ValueError):
            pass

    # ------------------------------------------------------------------ export

    def _export_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def _default_export_filename(
        self,
        export_type: str,
        *,
        timestamp: str | None = None,
    ) -> str:
        stamp = timestamp or self._export_timestamp()
        if export_type == "DETAIL":
            return self._t(
                "historiek.export.bestandsnaam_detail",
                timestamp=stamp,
            )
        return self._t(
            "historiek.export.bestandsnaam_overzicht",
            timestamp=stamp,
        )

    def _export_start_path(self, default_filename: str) -> str:
        directory = self._beste_export_start_directory()
        if directory is not None:
            return str(directory / default_filename)
        return default_filename

    def _open_export_directory_if_enabled(self, file_path: str) -> None:
        instellingen = laad_instellingen()
        if not instellingen.algemeen.exportmap_openen_na_export:
            return
        directory = str(Path(file_path).resolve().parent)
        QDesktopServices.openUrl(QUrl.fromLocalFile(directory))

    def _choose_export_csv_path(self) -> str | None:
        default_filename = self._default_export_filename("OVERVIEW")
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            self._t("historiek.export.dialoog_titel"),
            self._export_start_path(default_filename),
            self._t("historiek.export.bestandsfilter"),
        )
        if not file_path:
            return None
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"
        return file_path

    def _choose_export_detail_csv_path(self) -> str | None:
        default_filename = self._default_export_filename("DETAIL")
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            self._t("historiek.export.detail_dialoog_titel"),
            self._export_start_path(default_filename),
            self._t("historiek.export.bestandsfilter"),
        )
        if not file_path:
            return None
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"
        return file_path

    def _choose_export_both_directory(self) -> str | None:
        start_directory = self._beste_export_start_directory()
        chosen = QFileDialog.getExistingDirectory(
            self,
            self._t("historiek.export.beide_dialoog_titel"),
            str(start_directory) if start_directory is not None else "",
        )
        return chosen or None

    def _export_selected_type(self) -> None:
        export_type = self.export_type_combo.currentData()
        if export_type == "DETAIL":
            self._export_detail_csv()
        elif export_type == "BOTH":
            self._export_both_csv()
        else:
            self._export_csv()

    def _export_csv(self) -> None:
        """Mensleesbare overzicht-export; bestaande kolommen blijven behouden."""
        try:
            filters = self._active_filters()
        except ValueError as exc:
            self.state_label.setText(str(exc))
            return

        try:
            rows = self._rows_for_export(filters)
        except Exception as exc:
            self.state_label.setText(
                self._t("historiek.export.fout", bericht=str(exc))
            )
            return

        if rows is None:
            return
        if not rows:
            self.state_label.setText(self._t("historiek.export.leeg"))
            return

        file_path = self._choose_export_csv_path()
        if file_path is None:
            return

        try:
            write_history_csv(
                file_path,
                self._column_headers(),
                (self._row_values(row) for row in rows),
            )
        except Exception as exc:
            self.state_label.setText(
                self._t("historiek.export.fout", bericht=str(exc))
            )
            return

        self.state_label.setText(
            self._t(
                "historiek.export.geslaagd",
                aantal=len(rows),
                pad=file_path,
            )
        )
        self._onthoud_laatste_exportmap(Path(file_path))
        self._open_export_directory_if_enabled(file_path)

    def _export_detail_csv(self) -> None:
        """Machineleesbare detail-export vanuit opgeslagen snapshots."""
        try:
            filters = self._active_filters()
        except ValueError as exc:
            self.state_label.setText(str(exc))
            return

        try:
            rows = self._rows_for_export(filters)
        except Exception as exc:
            self.state_label.setText(
                self._t("historiek.export.detail_fout", bericht=str(exc))
            )
            return

        if rows is None:
            return
        if not rows:
            self.state_label.setText(self._t("historiek.export.leeg"))
            return

        details: list[dict[str, Any]] = []
        try:
            for row in rows:
                measurement_id = row["measurement"].id
                detail = self._history_service.get_measurement_detail(measurement_id)
                if detail is None:
                    raise ValueError(
                        self._t(
                            "historiek.export.detail_ontbreekt",
                            measurement_id=measurement_id,
                        )
                    )
                details.append(detail)
        except Exception as exc:
            self.state_label.setText(
                self._t("historiek.export.detail_fout", bericht=str(exc))
            )
            return

        file_path = self._choose_export_detail_csv_path()
        if file_path is None:
            return

        try:
            write_history_csv(
                file_path,
                DETAIL_EXPORT_HEADERS,
                (detail_row_values(detail) for detail in details),
            )
        except Exception as exc:
            self.state_label.setText(
                self._t("historiek.export.detail_fout", bericht=str(exc))
            )
            return

        self.state_label.setText(
            self._t(
                "historiek.export.detail_geslaagd",
                aantal=len(details),
                pad=file_path,
            )
        )
        self._onthoud_laatste_exportmap(Path(file_path))
        self._open_export_directory_if_enabled(file_path)

    def _export_both_csv(self) -> None:
        """Schrijf overzicht en detail met dezelfde scope en dezelfde timestamp."""
        try:
            filters = self._active_filters()
        except ValueError as exc:
            self.state_label.setText(str(exc))
            return

        try:
            rows = self._rows_for_export(filters)
        except Exception as exc:
            self.state_label.setText(
                self._t("historiek.export.fout", bericht=str(exc))
            )
            return

        if rows is None:
            return
        if not rows:
            self.state_label.setText(self._t("historiek.export.leeg"))
            return

        details: list[dict[str, Any]] = []
        try:
            for row in rows:
                measurement_id = row["measurement"].id
                detail = self._history_service.get_measurement_detail(measurement_id)
                if detail is None:
                    raise ValueError(
                        self._t(
                            "historiek.export.detail_ontbreekt",
                            measurement_id=measurement_id,
                        )
                    )
                details.append(detail)
        except Exception as exc:
            self.state_label.setText(
                self._t("historiek.export.detail_fout", bericht=str(exc))
            )
            return

        directory = self._choose_export_both_directory()
        if directory is None:
            return

        timestamp = self._export_timestamp()
        overview_path = str(
            Path(directory)
            / self._default_export_filename("OVERVIEW", timestamp=timestamp)
        )
        detail_path = str(
            Path(directory)
            / self._default_export_filename("DETAIL", timestamp=timestamp)
        )

        try:
            write_history_csv(
                overview_path,
                self._column_headers(),
                (self._row_values(row) for row in rows),
            )
            write_history_csv(
                detail_path,
                DETAIL_EXPORT_HEADERS,
                (detail_row_values(detail) for detail in details),
            )
        except Exception as exc:
            self.state_label.setText(
                self._t("historiek.export.fout", bericht=str(exc))
            )
            return

        self.state_label.setText(
            self._t(
                "historiek.export.beide_geslaagd",
                aantal=len(rows),
                pad=directory,
            )
        )
        self._onthoud_laatste_exportmap(Path(directory))
        self._open_export_directory_if_enabled(overview_path)

    def _row_values(self, row: dict[str, Any]) -> list[str]:
        measurement = row["measurement"]
        return [
            format_local_datetime(measurement.measured_at_ms),
            self._tool_label(measurement.tool_key),
            component_label(row),
            self._t(measurement_method_translation_key(measurement.measurement_method)),
            measurement.instrument_name or measurement.instrument_key or "—",
            format_measurement_values(measurement.tool_key, measurement),
            (
                self._t(f"status.eindstatus.{row['final_status']}")
                if row.get("final_status")
                else "—"
            ),
            (
                self._t(f"status.betrouwbaarheid.{row['reliability_level']}")
                if row.get("reliability_level")
                else "—"
            ),
        ]

    def _populate(self, rows: list[dict[str, Any]]) -> None:
        self.table.blockSignals(True)
        try:
            self.table.setRowCount(len(rows))
            for row_index, row in enumerate(rows):
                measurement = row["measurement"]

                select_item = QTableWidgetItem("")
                select_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
                select_item.setCheckState(Qt.CheckState.Unchecked)
                select_item.setData(Qt.ItemDataRole.UserRole, measurement.id)
                select_item.setData(
                    Qt.ItemDataRole.UserRole + 1,
                    measurement.tool_key,
                )
                select_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, 0, select_item)

                values = self._row_values(row)
                for value_index, value in enumerate(values):
                    column = value_index + 1
                    item = QTableWidgetItem(str(value))
                    if value_index == 0:
                        item.setData(Qt.ItemDataRole.UserRole, measurement.id)
                        item.setData(
                            Qt.ItemDataRole.UserRole + 1,
                            measurement.tool_key,
                        )
                    if value_index == 5:
                        item.setTextAlignment(
                            Qt.AlignmentFlag.AlignLeft
                            | Qt.AlignmentFlag.AlignVCenter
                        )
                    self.table.setItem(row_index, column, item)
        finally:
            self.table.blockSignals(False)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, max(48, self.table.columnWidth(0)))
        self.table.horizontalHeader().setStretchLastSection(True)
        self._update_selection_count()

    def _update_detail_button(self) -> None:
        has_selection = self._selected_measurement_id() is not None
        self.detail_btn.setEnabled(has_selection)
        self.repeat_btn.setEnabled(
            has_selection and self._selected_tool_key() == "ESR_CAPACITOR"
        )

    def _selected_measurement_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 1)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def _selected_tool_key(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 1)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole + 1)
        return str(value) if value else None

    def _repeat_selected_measurement(self) -> None:
        measurement_id = self._selected_measurement_id()
        if measurement_id is None:
            return
        try:
            detail = self._history_service.get_measurement_detail(measurement_id)
            if detail is None:
                self.state_label.setText(self._t("historiek.detail_niet_gevonden"))
                return
            preset = build_repeat_measurement_preset(detail)
        except Exception as exc:
            self.state_label.setText(self._t("historiek.herhalen_fout", bericht=str(exc)))
            return
        self.repeat_requested.emit(preset)

    def _show_selected_detail(self) -> None:
        measurement_id = self._selected_measurement_id()
        if measurement_id is None:
            return
        try:
            detail = self._history_service.get_measurement_detail(measurement_id)
        except Exception as exc:
            self.state_label.setText(self._t("historiek.detail_fout", bericht=str(exc)))
            return
        if detail is None:
            self.state_label.setText(self._t("historiek.detail_niet_gevonden"))
            return
        self._show_detail_dialog(detail)

    def _show_detail_dialog(self, detail: dict[str, Any]) -> None:
        measurement = detail["measurement"]
        dialog = QDialog(self)
        dialog.setWindowTitle(
            self._t("historiek.detail_titel", measurement_id=measurement.id)
        )
        dialog.resize(820, 680)

        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.document().setDefaultStyleSheet(
            "body { color: #F0F0F0; background-color: #1E1E1E; font-family: 'Segoe UI'; } "
            "h2, h3, b { color: #FFFFFF; } table { border-collapse: collapse; width: 100%; } "
            "td { padding: 3px 8px; vertical-align: top; } td:first-child { color: #BDBDBD; width: 34%; } "
            "li, p { color: #F0F0F0; }"
        )
        browser.setHtml(self._build_detail_html(detail))
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _build_detail_html(self, detail: dict[str, Any]) -> str:
        measurement = detail["measurement"]
        if measurement.tool_key == "ESR_CAPACITOR":
            return self._build_esr_capacitor_detail_html(detail)
        return self._build_generic_detail_html(detail)

    def _build_generic_detail_html(self, detail: dict[str, Any]) -> str:
        measurement = detail["measurement"]
        return (
            f"<h2>{escape(self._t('historiek.detail_kop'))}</h2>"
            f"<p><b>{escape(self._t('historiek.detail.tool'))}:</b> "
            f"{escape(self._tool_label(measurement.tool_key))}</p>"
            f"<p><b>{escape(self._t('historiek.detail.datum_tijd'))}:</b> "
            f"{escape(format_local_datetime(measurement.measured_at_ms))}</p>"
            f"<p>{escape(self._t('historiek.detail_geen_renderer'))}</p>"
        )

    def _build_esr_capacitor_detail_html(self, detail: dict[str, Any]) -> str:
        model = detail["component_model"]
        sample = detail["component_sample"]
        session = detail["measurement_session"]
        measurement = detail["measurement"]
        assessments = detail["assessment_snapshots"]
        references_by_assessment = detail["reference_snapshots_by_assessment_id"]

        yes = self._t("algemeen.ja")
        no = self._t("algemeen.nee")

        def e(value: Any) -> str:
            return escape("—" if value is None or value == "" else str(value))

        def row(label_key: str, value: Any) -> str:
            return f"<tr><td>{escape(self._t(label_key))}</td><td>{e(value)}</td></tr>"

        html = [f"<h2>{escape(self._t('historiek.detail_kop'))}</h2>"]
        html.append(f"<h3>{escape(self._t('historiek.sectie.component'))}</h3><table>")
        html.extend([
            row("historiek.detail.fabrikant", model.manufacturer),
            row("historiek.detail.serie", model.series),
            row("historiek.detail.part_number", model.part_number),
            row("historiek.detail.technologie", model.technology),
            row(
                "historiek.detail.nominale_capaciteit",
                f"{model.nominal_capacitance_value:g} {model.nominal_capacitance_unit}"
                if model.nominal_capacitance_value is not None
                and model.nominal_capacitance_unit
                else format_capacitance_f(model.nominal_capacitance_f),
            ),
            row(
                "historiek.detail.nominale_spanning",
                format_optional_number(model.rated_voltage_v, suffix=" V"),
            ),
            row(
                "historiek.detail.tolerantie",
                f"{format_optional_number(model.tolerance_lower_pct, suffix='%')} / "
                f"{format_optional_number(model.tolerance_upper_pct, suffix='%')}",
            ),
            row("historiek.detail.sample_state", sample.sample_state.value),
        ])
        html.append("</table>")

        html.append(f"<h3>{escape(self._t('historiek.sectie.meetcontext'))}</h3><table>")
        html.extend([
            row("historiek.detail.tool", self._tool_label(measurement.tool_key)),
            row("historiek.detail.datum_tijd", format_local_datetime(measurement.measured_at_ms)),
            row(
                "historiek.detail.meetmethode",
                self._t(measurement_method_translation_key(measurement.measurement_method)),
            ),
            row(
                "historiek.detail.instrument",
                measurement.instrument_name or measurement.instrument_key,
            ),
            row(
                "historiek.detail.frequentie",
                format_optional_number(measurement.frequency_hz, suffix=" Hz"),
            ),
            row(
                "historiek.detail.testspanning",
                format_optional_number(measurement.test_voltage_vrms, suffix=" Vrms"),
            ),
            row(
                "historiek.detail.temperatuur",
                format_optional_number(measurement.temperature_c, suffix=" °C"),
            ),
            row(
                "historiek.detail.spanningsloos",
                format_bool(measurement.power_off_confirmed, yes, no),
            ),
            row(
                "historiek.detail.ontladen",
                format_bool(measurement.discharged_confirmed, yes, no),
            ),
            row("historiek.detail.sessie_start", format_local_datetime(session.started_at_ms)),
            row("historiek.detail.sessie_einde", format_local_datetime(session.ended_at_ms)),
        ])
        html.append("</table>")

        html.append(f"<h3>{escape(self._t('historiek.sectie.meetwaarden'))}</h3><table>")
        html.extend([
            row("historiek.detail.capaciteit", format_capacitance_f(measurement.capacitance_f)),
            row("historiek.detail.esr", format_esr_ohm(measurement.esr_ohm)),
            row("historiek.detail.d", format_optional_number(measurement.dissipation_factor_d)),
            row(
                "historiek.detail.out_of_range",
                format_bool(measurement.out_of_range, yes, no),
            ),
            row(
                "historiek.detail.open_suspected",
                format_bool(measurement.open_suspected, yes, no),
            ),
            row(
                "historiek.detail.short_suspected",
                format_bool(measurement.short_suspected, yes, no),
            ),
        ])
        html.append("</table>")

        if not assessments:
            html.append(f"<p>{escape(self._t('historiek.geen_assessment'))}</p>")

        for index, assessment in enumerate(assessments, start=1):
            html.append(
                f"<h3>{escape(self._t('historiek.sectie.assessment', nummer=index))}</h3><table>"
            )
            html.extend([
                row(
                    "historiek.detail.assessed_at",
                    format_local_datetime(assessment.assessed_at_ms),
                ),
                row("historiek.detail.engine_version", assessment.engine_version),
                row("historiek.detail.capacitance_status", assessment.capacitance_status),
                row(
                    "historiek.detail.capacitance_deviation",
                    format_optional_number(
                        assessment.capacitance_deviation_pct, suffix=" %"
                    ),
                ),
                row("historiek.detail.esr_status", assessment.esr_status),
                row(
                    "historiek.detail.esr_factor",
                    format_optional_number(assessment.esr_factor, suffix="×"),
                ),
                row("historiek.detail.consistency_status", assessment.consistency_status),
                row("historiek.detail.reliability", assessment.reliability_level),
                row("historiek.detail.final_status", assessment.final_status),
            ])
            html.append("</table>")

            for key, value in (
                ("historiek.detail.redenen", decode_json_list(assessment.reasons_json)),
                (
                    "historiek.detail.waarschuwingen",
                    decode_json_list(assessment.warnings_json),
                ),
                ("historiek.detail.advies", decode_json_list(assessment.advice_json)),
            ):
                html.append(f"<p><b>{escape(self._t(key))}</b></p>")
                if value:
                    html.append(
                        "<ul>"
                        + "".join(f"<li>{escape(item)}</li>" for item in value)
                        + "</ul>"
                    )
                else:
                    html.append("<p>—</p>")

            references = references_by_assessment.get(assessment.id, [])
            if not references:
                html.append(
                    f"<p><b>{escape(self._t('historiek.sectie.referenties'))}</b>: —</p>"
                )
            for ref_index, reference in enumerate(references, start=1):
                html.append(
                    f"<h3>{escape(self._t('historiek.sectie.referentie', nummer=ref_index))}</h3><table>"
                )
                html.extend([
                    row("historiek.detail.reference_role", reference.reference_role),
                    row("historiek.detail.reference_level", reference.reference_level),
                    row("historiek.detail.reference_type", reference.reference_type),
                    row(
                        "historiek.detail.reference_value",
                        f"{format_optional_number(reference.reference_value)} "
                        f"{reference.reference_unit or ''}".strip(),
                    ),
                    row(
                        "historiek.detail.reference_frequency",
                        format_optional_number(reference.frequency_hz, suffix=" Hz"),
                    ),
                    row(
                        "historiek.detail.reference_temperature",
                        format_optional_number(reference.temperature_c, suffix=" °C"),
                    ),
                    row("historiek.detail.value_kind", reference.value_kind),
                    row("historiek.detail.source_name", reference.source_name),
                    row("historiek.detail.source_document", reference.source_document),
                ])
                html.append("</table>")

        html.append(
            f"<p><i>{escape(self._t('historiek.detail_opmerking_opgeslagen_waarden'))}</i></p>"
        )
        return "\n".join(html)