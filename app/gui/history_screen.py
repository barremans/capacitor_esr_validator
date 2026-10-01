"""
================================================================================
Module:     app/gui/history_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.5.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Compacte centrale read-only weergave van opgeslagen meethistoriek.

            Toont per meting datum/tijd, componentidentiteit, meetmethode,
            instrument, gemeten capaciteit, ESR, eindstatus en betrouwbaarheid.
            De pagina blijft read-only en biedt daarnaast een detaildialoog
            voor de volledige opgeslagen meetketen, assessments en referenties.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste compacte historiekpagina met verversen, lege-state
                        en foutmelding; gekoppeld aan MeasurementHistoryService.
  v1.1.0 (2026-10-01)  Read-only detaildialoog toegevoegd; detail opent via
                        selectie + knop of dubbelklik en toont alle snapshots.
  v1.2.0 (2026-10-01)  "Herhaal meting" toegevoegd. Alleen component- en
                        meetcontext wordt als nieuwe invoerpreset uitgezonden;
                        historische meetwaarden/assessment worden niet gekopieerd.
  v1.3.0 (2026-10-01)  Compacte read-only filterbalk toegevoegd voor fabrikant,
                        serie, meetmethode, instrument, frequentie, eindstatus en
                        betrouwbaarheid. Filters gebruiken het bestaande storage-
                        read-contract; geen schemawijziging.
  v1.4.0 (2026-10-01)  Multitool-historiek: Tool/Testtype-filter en tabelkolom
                        toegevoegd. Herhalen is alleen actief voor ondersteunde
                        ESR_CAPACITOR-records; detail blijft voor alle tools leesbaar.
  v1.5.0 (2026-10-01)  Tabel tool-neutraal gemaakt met één kolom Meetwaarden.
                        Meetmethode-labels zijn gecentraliseerd en detailopbouw
                        dispatcht expliciet per tool_key met generieke fallback.
================================================================================
"""

from __future__ import annotations

from html import escape
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
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

from app.helpers.i18n import vertaal
from app.helpers.history_filters import build_history_filters
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
        self._build_ui()

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

        self.refresh_btn = QPushButton(self._t("knop.verversen"))
        self.refresh_btn.clicked.connect(self.refresh)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        self.filter_group = QGroupBox(self._t("historiek.filter.titel"))
        filter_layout = QVBoxLayout(self.filter_group)

        filter_form = QFormLayout()
        filter_form.setHorizontalSpacing(10)
        filter_form.setVerticalSpacing(6)

        self.filter_tool = QComboBox()
        self._fill_tool_filter()
        filter_form.addRow(self._t("historiek.filter.tool"), self.filter_tool)

        self.filter_manufacturer = QLineEdit()
        self.filter_manufacturer.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        filter_form.addRow(self._t("historiek.filter.fabrikant"), self.filter_manufacturer)

        self.filter_series = QLineEdit()
        self.filter_series.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        filter_form.addRow(self._t("historiek.filter.serie"), self.filter_series)

        self.filter_method = QComboBox()
        self._fill_method_filter()
        filter_form.addRow(self._t("historiek.filter.meetmethode"), self.filter_method)

        self.filter_instrument = QLineEdit()
        self.filter_instrument.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        filter_form.addRow(self._t("historiek.filter.instrument"), self.filter_instrument)

        self.filter_frequency = QComboBox()
        self._fill_frequency_filter()
        filter_form.addRow(self._t("historiek.filter.frequentie"), self.filter_frequency)

        self.filter_status = QComboBox()
        self._fill_status_filter()
        filter_form.addRow(self._t("historiek.filter.status"), self.filter_status)

        self.filter_reliability = QComboBox()
        self._fill_reliability_filter()
        filter_form.addRow(self._t("historiek.filter.betrouwbaarheid"), self.filter_reliability)

        filter_layout.addLayout(filter_form)

        filter_buttons = QHBoxLayout()
        filter_buttons.addStretch(1)
        self.clear_filters_btn = QPushButton(self._t("historiek.filter.wissen"))
        self.clear_filters_btn.clicked.connect(self._clear_filters)
        filter_buttons.addWidget(self.clear_filters_btn)
        self.apply_filters_btn = QPushButton(self._t("historiek.filter.toepassen"))
        self.apply_filters_btn.clicked.connect(self.refresh)
        filter_buttons.addWidget(self.apply_filters_btn)
        filter_layout.addLayout(filter_buttons)
        root.addWidget(self.filter_group)

        self.state_label = QLabel("")
        self.state_label.setWordWrap(True)
        self.state_label.setStyleSheet("color: #C8C8C8;")
        root.addWidget(self.state_label)

        self.table = QTableWidget(0, 8)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.itemSelectionChanged.connect(self._update_detail_button)
        self.table.itemDoubleClicked.connect(lambda _item: self._show_selected_detail())
        root.addWidget(self.table, 1)

        bottom = QHBoxLayout()
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

    def _apply_headers(self) -> None:
        headers = [
            self._t("historiek.kolom.datum_tijd"),
            self._t("historiek.kolom.tool"),
            self._t("historiek.kolom.component"),
            self._t("historiek.kolom.meetmethode"),
            self._t("historiek.kolom.instrument"),
            self._t("historiek.kolom.meetwaarden"),
            self._t("historiek.kolom.status"),
            self._t("historiek.kolom.betrouwbaarheid"),
        ]
        self.table.setHorizontalHeaderLabels(headers)
        header = self.table.horizontalHeader()
        for column in range(self.table.columnCount()):
            header.setStretchLastSection(False)
            self.table.resizeColumnToContents(column)
        header.setStretchLastSection(True)

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
        return build_history_filters(
            tool_key=self.filter_tool.currentData(),
            manufacturer=self.filter_manufacturer.text(),
            series=self.filter_series.text(),
            measurement_method=self.filter_method.currentData(),
            instrument_key=self.filter_instrument.text(),
            frequency_hz=self.filter_frequency.currentData(),
            final_status=self.filter_status.currentData(),
            reliability_level=self.filter_reliability.currentData(),
        )

    def _clear_filters(self) -> None:
        self.filter_tool.setCurrentIndex(0)
        self.filter_manufacturer.clear()
        self.filter_series.clear()
        self.filter_method.setCurrentIndex(0)
        self.filter_instrument.clear()
        self.filter_frequency.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(0)
        self.filter_reliability.setCurrentIndex(0)
        self.refresh()

    def apply_language(self, taal: str) -> None:
        self.taal = taal
        self.back_btn.setText(self._t("knop.terug"))
        self.title_label.setText(self._t("scherm.historiek"))
        self.refresh_btn.setText(self._t("knop.verversen"))
        self.detail_btn.setText(self._t("knop.details"))
        self.repeat_btn.setText(self._t("knop.herhaal_meting"))
        self.filter_group.setTitle(self._t("historiek.filter.titel"))
        self.filter_manufacturer.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.filter_series.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.filter_instrument.setPlaceholderText(self._t("historiek.filter.exact_placeholder"))
        self.clear_filters_btn.setText(self._t("historiek.filter.wissen"))
        self.apply_filters_btn.setText(self._t("historiek.filter.toepassen"))
        self._fill_tool_filter()
        self._fill_method_filter()
        self._fill_frequency_filter()
        self._fill_status_filter()
        self._fill_reliability_filter()
        self._apply_headers()

    def refresh(self) -> None:
        try:
            rows = self._history_service.list_measurements(
                self._active_filters(), limit=100, offset=0
            )
        except Exception as exc:
            self.table.setRowCount(0)
            self.state_label.setText(self._t("historiek.fout", bericht=str(exc)))
            return

        self._populate(rows)
        self._update_detail_button()
        if rows:
            self.state_label.setText(self._t("historiek.aantal", aantal=len(rows)))
        else:
            self.state_label.setText(self._t("historiek.leeg"))

    def _populate(self, rows: list[dict[str, Any]]) -> None:
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            measurement = row["measurement"]
            values = [
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
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, measurement.id)
                    item.setData(Qt.ItemDataRole.UserRole + 1, measurement.tool_key)
                if column == 5:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(row_index, column, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

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
        item = self.table.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return int(value) if value is not None else None

    def _selected_tool_key(self) -> str | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
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
