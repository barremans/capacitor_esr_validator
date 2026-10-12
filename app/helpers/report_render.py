"""
================================================================================
Module:     app/helpers/report_render.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.4.0
Datum:      2026-10-12
Auteur:     Bart Bossuyt

Doel:       Pure, GUI- en database-onafhankelijke HTML-renderer voor
            meetrapporten.

            De renderer accepteert een ReportBundle (of een object met
            dezelfde attributen) en levert een volledige HTML-string op.
            Er wordt niets herberekend: alle waarden komen uit de opgeslagen
            snapshots. Geen Qt, geen database, geen netwerk.

            Multitool: de renderer dispatcht per meting op tool_key. Voor
            ESR_CAPACITOR gebruikt hij de specifieke secties; voor andere
            tools een generieke fallback, net zoals de historiek-viewer dat
            vandaag doet. Meerdere metingen komen in één rapport terecht,
            in de volgorde die de service aanlevert (oplopend op tijd).

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: vaste secties (kop, component,
                        meetcontext, meetwaarden, assessments, referenties,
                        voetnoot), NL/EN via vertaal(), read-only bewijs in
                        de voetnoot.
  v1.1.0 (2026-10-10)  Multitool: renderer accepteert een tuple van details.
                        Per meting een blok; generieke fallback voor tools
                        zonder specifieke secties. Nieuwe optionele parameter
                        chart_png_base64_per_meting: dict[int, str] voor de
                        grafieksectie (8B.2 vult die).
  v1.2.0 (2026-10-11)  Fase 8D: optionele auteur wordt in de rapportkop
                        getoond als die niet leeg is. Backward-compatible:
                        een ReportBundle zonder auteur-attribuut werkt nog
                        (getattr met default "").
  v1.3.0 (2026-10-11)  Bugfix: _bool() gebruikte de niet-bestaande keys
                        'algemeen.ja' en 'algemeen.nee'. Vervangen door
                        'app.ja' en 'app.nee', die in app.json bestaan.
                        Zonder deze fix lekten de i18n-keys letterlijk in
                        de rapport-HTML.
  v1.4.0 (2026-10-12)  Bugfix: capacitance_status, esr_status en
                        consistency_status werden als ruwe enum-codes
                        getoond (bv. 'binnen_tolerantie' in plaats van
                        'binnen tolerantie'). Nu vertaald via de nieuwe
                        helper _status_code_label, met dezelfde keys als
                        de GUI gebruikt (status.capaciteit.*, status.esr.*,
                        status.consistentie.*). Backward-compatible:
                        onbekende codes vallen terug op de ruwe waarde.
================================================================================
"""

from __future__ import annotations

from html import escape
from typing import Any

from app.helpers.history_formatting import (
    decode_json_list,
    format_bool,
    format_capacitance_f,
    format_esr_ohm,
    format_local_datetime,
    format_optional_number,
    measurement_method_translation_key,
)
from app.helpers.i18n import vertaal


# ---------------------------------------------------------------------------
# Interne helpers
# ---------------------------------------------------------------------------

def _t(taal: str, sleutel: str, **kwargs: Any) -> str:
    return vertaal(sleutel, taal=taal, **kwargs)


def _e(value: Any) -> str:
    """HTML-escape; None wordt het onbekend-teken."""
    if value is None or value == "":
        return "—"
    return escape(str(value))


def _row(taal: str, label_key: str, value: Any) -> str:
    return (
        f"<tr><td class=\"label\">{escape(_t(taal, label_key))}</td>"
        f"<td class=\"value\">{_e(value)}</td></tr>"
    )


def _bool(taal: str, value: bool | None) -> str:
    return format_bool(
        value,
        yes=_t(taal, "app.ja"),
        no=_t(taal, "app.nee"),
    )


def _status_label(taal: str, value: Any) -> str:
    if not value:
        return "—"
    sleutel = f"status.eindstatus.{value}"
    vertaald = _t(taal, sleutel)
    return value if vertaald == sleutel else vertaald


def _betrouwbaarheid_label(taal: str, value: Any) -> str:
    if not value:
        return "—"
    sleutel = f"status.betrouwbaarheid.{value}"
    vertaald = _t(taal, sleutel)
    return value if vertaald == sleutel else vertaald


def _status_code_label(taal: str, namespace: str, value: Any) -> str:
    """Vertaal een statuscode uit assessment_service naar het label.

    Gebruikt dezelfde i18n-keys als de GUI (status.capaciteit.*,
    status.esr.*, status.consistentie.*). Valt terug op de ruwe code als
    de key niet bestaat, zodat het rapport ook werkt voor onbekende
    statussen.

    Werkt zowel voor een enum (met .value) als voor een string, zodat
    het zowel met het live assessment-resultaat als met een opgeslagen
    snapshot werkt.
    """
    if not value:
        return "—"
    code = str(getattr(value, "value", value))
    sleutel = f"{namespace}.{code}"
    vertaald = _t(taal, sleutel)
    return code if vertaald == sleutel else vertaald


def _tool_label(taal: str, tool_key: str | None) -> str:
    if not tool_key:
        return "—"
    sleutel = f"tool_type.{tool_key}"
    vertaald = _t(taal, sleutel)
    return tool_key if vertaald == sleutel else vertaald


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #1A1A1A;
    background-color: #FFFFFF;
    font-size: 11pt;
    line-height: 1.4;
}
h1 {
    font-size: 18pt;
    margin: 0 0 4px 0;
    color: #0D3B66;
}
h1.meting-kop {
    font-size: 15pt;
    margin-top: 22px;
    padding-top: 10px;
    border-top: 2px solid #0D3B66;
}
h2 {
    font-size: 13pt;
    margin: 18px 0 6px 0;
    color: #0D3B66;
    border-bottom: 1px solid #B0BEC5;
    padding-bottom: 2px;
}
h3 {
    font-size: 11pt;
    margin: 12px 0 4px 0;
    color: #1A1A1A;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 8px;
}
td {
    padding: 3px 8px;
    vertical-align: top;
    border-bottom: 1px solid #ECEFF1;
}
td.label {
    color: #546E7A;
    width: 34%;
    white-space: nowrap;
}
td.value {
    color: #1A1A1A;
}
ul {
    margin: 4px 0 8px 18px;
    padding: 0;
}
li {
    margin-bottom: 2px;
}
.kop-meta {
    color: #546E7A;
    font-size: 9pt;
    margin-bottom: 12px;
}
.voetnoot {
    margin-top: 20px;
    padding-top: 8px;
    border-top: 1px solid #B0BEC5;
    color: #546E7A;
    font-size: 9pt;
    font-style: italic;
}
img.chart {
    max-width: 100%;
    height: auto;
    border: 1px solid #B0BEC5;
    margin: 6px 0 12px 0;
}
.geen-renderer {
    color: #546E7A;
    font-style: italic;
    margin: 6px 0 12px 0;
}
"""


# ---------------------------------------------------------------------------
# Kop en voetnoot
# ---------------------------------------------------------------------------

def _render_kop(bundle: Any, taal: str) -> str:
    app_versie = getattr(bundle, "app_versie", "")
    rapportdatum = getattr(bundle, "rapportdatum", "")
    werkplaats = getattr(bundle, "werkplaats", "")
    auteur = getattr(bundle, "auteur", "")
    scope = getattr(bundle, "scope", "")
    titel = _t(taal, "report.titel")

    meta_parts = [
        f"{escape(_t(taal, 'report.kop.rapportdatum'))}: {escape(str(rapportdatum))}",
        f"{escape(_t(taal, 'report.kop.app_versie'))}: {escape(str(app_versie))}",
        f"{escape(_t(taal, 'report.kop.taal'))}: {escape(taal)}",
    ]
    if werkplaats:
        meta_parts.append(
            f"{escape(_t(taal, 'report.kop.werkplaats'))}: {escape(str(werkplaats))}"
        )
    if auteur:
        meta_parts.append(
            f"{escape(_t(taal, 'report.kop.auteur'))}: {escape(str(auteur))}"
        )
    if scope:
        meta_parts.append(
            f"{escape(_t(taal, 'report.kop.scope'))}: {escape(str(scope))}"
        )

    aantal = getattr(bundle, "aantal_metingen", 1)
    if aantal > 1:
        meta_parts.append(
            escape(_t(taal, "report.meerdere_metingen", aantal=aantal))
        )

    html = [f"<h1>{escape(titel)}</h1>"]
    html.append(
        f"<div class=\"kop-meta\">{' &nbsp;|&nbsp; '.join(meta_parts)}</div>"
    )
    return "".join(html)


def _render_voetnoot(taal: str) -> str:
    opgeslagen = escape(_t(taal, "report.voetnoot.opgeslagen_waarden"))
    read_only = escape(_t(taal, "report.voetnoot.read_only"))
    return f"<div class=\"voetnoot\">{opgeslagen}<br>{read_only}</div>"


# ---------------------------------------------------------------------------
# Generieke fallback (elke tool zonder specifieke renderer)
# ---------------------------------------------------------------------------

def _render_generic_detail(detail: dict[str, Any], taal: str) -> str:
    measurement = detail["measurement"]
    html = [
        f"<h2>{escape(_t(taal, 'report.sectie.component'))}</h2>"
        f"<table>"
        f"{_row(taal, 'historiek.detail.tool', _tool_label(taal, measurement.tool_key))}"
        f"{_row(taal, 'historiek.detail.datum_tijd', format_local_datetime(measurement.measured_at_ms))}"
        f"</table>",
        f"<p class=\"geen-renderer\">{escape(_t(taal, 'report.geen_renderer'))}</p>",
    ]
    return "".join(html)


# ---------------------------------------------------------------------------
# ESR_CAPACITOR-specifieke secties
# ---------------------------------------------------------------------------

def _render_component(detail: dict[str, Any], taal: str) -> str:
    model = detail["component_model"]
    sample = detail["component_sample"]

    html = [f"<h2>{escape(_t(taal, 'report.sectie.component'))}</h2><table>"]
    html.append(_row(taal, "historiek.detail.fabrikant", model.manufacturer))
    html.append(_row(taal, "historiek.detail.serie", model.series))
    html.append(_row(taal, "historiek.detail.part_number", model.part_number))
    html.append(_row(taal, "historiek.detail.technologie", model.technology))

    nominale_c = (
        f"{model.nominal_capacitance_value:g} {model.nominal_capacitance_unit}"
        if model.nominal_capacitance_value is not None
        and model.nominal_capacitance_unit
        else format_capacitance_f(model.nominal_capacitance_f)
    )
    html.append(_row(taal, "historiek.detail.nominale_capaciteit", nominale_c))
    html.append(
        _row(
            taal,
            "historiek.detail.nominale_spanning",
            format_optional_number(model.rated_voltage_v, suffix=" V"),
        )
    )
    html.append(
        _row(
            taal,
            "historiek.detail.tolerantie",
            f"{format_optional_number(model.tolerance_lower_pct, suffix='%')} / "
            f"{format_optional_number(model.tolerance_upper_pct, suffix='%')}",
        )
    )
    html.append(_row(taal, "historiek.detail.sample_state", sample.sample_state.value))
    html.append("</table>")
    return "".join(html)


def _render_meetcontext(detail: dict[str, Any], taal: str) -> str:
    measurement = detail["measurement"]
    session = detail["measurement_session"]

    html = [f"<h2>{escape(_t(taal, 'report.sectie.meetcontext'))}</h2><table>"]
    html.append(
        _row(taal, "historiek.detail.tool", _tool_label(taal, measurement.tool_key))
    )
    html.append(
        _row(taal, "historiek.detail.datum_tijd", format_local_datetime(measurement.measured_at_ms))
    )
    html.append(
        _row(
            taal,
            "historiek.detail.meetmethode",
            _t(taal, measurement_method_translation_key(measurement.measurement_method)),
        )
    )
    html.append(
        _row(
            taal,
            "historiek.detail.instrument",
            measurement.instrument_name or measurement.instrument_key,
        )
    )
    html.append(
        _row(
            taal,
            "historiek.detail.frequentie",
            format_optional_number(measurement.frequency_hz, suffix=" Hz"),
        )
    )
    html.append(
        _row(
            taal,
            "historiek.detail.testspanning",
            format_optional_number(measurement.test_voltage_vrms, suffix=" Vrms"),
        )
    )
    html.append(
        _row(
            taal,
            "historiek.detail.temperatuur",
            format_optional_number(measurement.temperature_c, suffix=" °C"),
        )
    )
    html.append(
        _row(
            taal,
            "historiek.detail.spanningsloos",
            _bool(taal, measurement.power_off_confirmed),
        )
    )
    html.append(
        _row(
            taal,
            "historiek.detail.ontladen",
            _bool(taal, measurement.discharged_confirmed),
        )
    )
    html.append(
        _row(taal, "historiek.detail.sessie_start", format_local_datetime(session.started_at_ms))
    )
    html.append(
        _row(taal, "historiek.detail.sessie_einde", format_local_datetime(session.ended_at_ms))
    )
    html.append("</table>")
    return "".join(html)


def _render_meetwaarden(detail: dict[str, Any], taal: str) -> str:
    measurement = detail["measurement"]

    html = [f"<h2>{escape(_t(taal, 'report.sectie.meetwaarden'))}</h2><table>"]
    html.append(_row(taal, "historiek.detail.capaciteit", format_capacitance_f(measurement.capacitance_f)))
    html.append(_row(taal, "historiek.detail.esr", format_esr_ohm(measurement.esr_ohm)))
    html.append(_row(taal, "historiek.detail.d", format_optional_number(measurement.dissipation_factor_d)))
    html.append(_row(taal, "historiek.detail.out_of_range", _bool(taal, measurement.out_of_range)))
    html.append(_row(taal, "historiek.detail.open_suspected", _bool(taal, measurement.open_suspected)))
    html.append(_row(taal, "historiek.detail.short_suspected", _bool(taal, measurement.short_suspected)))
    html.append("</table>")
    return "".join(html)


def _render_lijst(taal: str, label_key: str, waarden: tuple[str, ...]) -> str:
    html = [f"<p><b>{escape(_t(taal, label_key))}</b></p>"]
    if waarden:
        html.append(
            "<ul>"
            + "".join(f"<li>{escape(item)}</li>" for item in waarden)
            + "</ul>"
        )
    else:
        html.append("<p>—</p>")
    return "".join(html)


def _render_assessments(detail: dict[str, Any], taal: str) -> str:
    assessments = detail.get("assessment_snapshots") or []
    references_by_assessment = detail.get("reference_snapshots_by_assessment_id") or {}

    if not assessments:
        return (
            f"<h2>{escape(_t(taal, 'report.sectie.assessment', nummer=1))}</h2>"
            f"<p>{escape(_t(taal, 'report.sectie.geen_assessment'))}</p>"
        )

    html: list[str] = []
    for index, assessment in enumerate(assessments, start=1):
        html.append(
            f"<h2>{escape(_t(taal, 'report.sectie.assessment', nummer=index))}</h2>"
        )
        html.append("<table>")
        html.append(
            _row(taal, "historiek.detail.assessed_at", format_local_datetime(assessment.assessed_at_ms))
        )
        html.append(_row(taal, "historiek.detail.engine_version", assessment.engine_version))
        html.append(
            _row(
                taal,
                "historiek.detail.capacitance_status",
                _status_code_label(taal, "status.capaciteit", assessment.capacitance_status),
            )
        )
        html.append(
            _row(
                taal,
                "historiek.detail.capacitance_deviation",
                format_optional_number(assessment.capacitance_deviation_pct, suffix=" %"),
            )
        )
        html.append(
            _row(
                taal,
                "historiek.detail.esr_status",
                _status_code_label(taal, "status.esr", assessment.esr_status),
            )
        )
        html.append(
            _row(
                taal,
                "historiek.detail.esr_factor",
                format_optional_number(assessment.esr_factor, suffix="×"),
            )
        )
        html.append(
            _row(
                taal,
                "historiek.detail.consistency_status",
                _status_code_label(
                    taal, "status.consistentie", assessment.consistency_status
                ),
            )
        )
        html.append(
            _row(
                taal,
                "historiek.detail.reliability",
                _betrouwbaarheid_label(taal, assessment.reliability_level),
            )
        )
        html.append(
            _row(
                taal,
                "historiek.detail.final_status",
                _status_label(taal, assessment.final_status),
            )
        )
        html.append("</table>")

        html.append(_render_lijst(taal, "report.detail.redenen", decode_json_list(assessment.reasons_json)))
        html.append(_render_lijst(taal, "report.detail.waarschuwingen", decode_json_list(assessment.warnings_json)))
        html.append(_render_lijst(taal, "report.detail.advies", decode_json_list(assessment.advice_json)))

        references = references_by_assessment.get(assessment.id, [])
        if not references:
            html.append(
                f"<p>{escape(_t(taal, 'report.sectie.geen_referenties'))}</p>"
            )
        for ref_index, reference in enumerate(references, start=1):
            html.append(
                f"<h3>{escape(_t(taal, 'report.sectie.referentie', nummer=ref_index))}</h3>"
            )
            html.append("<table>")
            html.append(_row(taal, "historiek.detail.reference_role", reference.reference_role))
            html.append(_row(taal, "historiek.detail.reference_level", reference.reference_level))
            html.append(_row(taal, "historiek.detail.reference_type", reference.reference_type))
            html.append(
                _row(
                    taal,
                    "historiek.detail.reference_value",
                    f"{format_optional_number(reference.reference_value)} "
                    f"{reference.reference_unit or ''}".strip(),
                )
            )
            html.append(
                _row(
                    taal,
                    "historiek.detail.reference_frequency",
                    format_optional_number(reference.frequency_hz, suffix=" Hz"),
                )
            )
            html.append(
                _row(
                    taal,
                    "historiek.detail.reference_temperature",
                    format_optional_number(reference.temperature_c, suffix=" °C"),
                )
            )
            html.append(_row(taal, "historiek.detail.value_kind", reference.value_kind))
            html.append(_row(taal, "historiek.detail.source_name", reference.source_name))
            html.append(_row(taal, "historiek.detail.source_document", reference.source_document))
            html.append("</table>")

    return "".join(html)


# ---------------------------------------------------------------------------
# Per-meting dispatch
# ---------------------------------------------------------------------------

def _render_meting_blok(
    detail: dict[str, Any],
    taal: str,
    *,
    meting_kop: bool,
    chart_png_base64: str | None,
) -> str:
    """Render één meetblok; dispatch op tool_key."""
    measurement = detail["measurement"]
    tool_key = str(getattr(measurement, "tool_key", "") or "")

    html: list[str] = []
    if meting_kop:
        html.append(
            f"<h1 class=\"meting-kop\">"
            f"{escape(_t(taal, 'report.meting_kop', measurement_id=measurement.id))}"
            f"</h1>"
        )

    if tool_key == "ESR_CAPACITOR":
        html.append(_render_component(detail, taal))
        html.append(_render_meetcontext(detail, taal))
        html.append(_render_meetwaarden(detail, taal))
        html.append(_render_assessments(detail, taal))
    else:
        html.append(_render_generic_detail(detail, taal))

    if chart_png_base64:
        html.append(f"<h2>{escape(_t(taal, 'report.sectie.grafiek'))}</h2>")
        html.append(
            f"<img class=\"chart\" alt=\"chart\" "
            f"src=\"data:image/png;base64,{escape(chart_png_base64)}\">"
        )

    return "".join(html)


# ---------------------------------------------------------------------------
# Publieke API
# ---------------------------------------------------------------------------

def render_measurement_report_html(
    bundle: Any,
    *,
    extra_css: str = "",
    chart_png_base64_per_meting: dict[int, str] | None = None,
) -> str:
    """Render een meetrapport als volledige HTML-string.

    ``bundle`` moet de attributen ``details`` (tuple), ``taal``,
    ``rapportdatum``, ``app_versie`` en ``werkplaats`` hebben (zie
    ReportBundle). Voor één meting is ``details`` een tuple van lengte 1.

    ``chart_png_base64_per_meting`` is optioneel: een mapping van
    measurement_id naar base64-PNG-string. Metingen zonder chart worden
    zonder grafieksectie gerenderd.
    """
    taal = getattr(bundle, "taal", "nl_NL")
    details = getattr(bundle, "details", None)
    if details is None:
        # Backward-compatible: oude ReportBundle had 'detail'.
        enkel = getattr(bundle, "detail", None)
        if enkel is None:
            raise ValueError("ReportBundle heeft geen 'details'.")
        details = (enkel,)
    details = tuple(details)
    if not details:
        raise ValueError("ReportBundle bevat geen details.")

    chart_map = chart_png_base64_per_meting or {}

    css = _CSS + ("\n" + extra_css if extra_css else "")
    meerdere = len(details) > 1

    secties: list[str] = [_render_kop(bundle, taal)]
    for detail in details:
        measurement_id = int(detail["measurement"].id)
        secties.append(
            _render_meting_blok(
                detail,
                taal,
                meting_kop=meerdere,
                chart_png_base64=chart_map.get(measurement_id),
            )
        )
    secties.append(_render_voetnoot(taal))

    return (
        "<!DOCTYPE html>"
        "<html><head>"
        "<meta charset=\"utf-8\">"
        f"<title>{escape(_t(taal, 'report.titel'))}</title>"
        f"<style>{css}</style>"
        "</head><body>"
        + "".join(secties)
        + "</body></html>"
    )