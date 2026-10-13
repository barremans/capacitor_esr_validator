"""
================================================================================
Module:     tests/test_i18n_app_translations.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.4.0
Datum:      2026-10-13
Auteur:     Bart Bossuyt

Doel:       Regressietests voor algemene app-, menu-, dialoog-, tool- en
            knopvertalingen.

Wijzigingen:
  v1.3.0 (2026-10-03)  Bestaande algemene appvertalingen.
  v1.4.0 (2026-10-13)  Fase 9A: dialog.over_tekst bevat nu de placeholder
                        {versie}. Verwachte waarde bijgewerkt voor NL en EN.
                        Nieuwe test toegevoegd die controleert dat de
                        placeholder in beide talen werkt. Let op: de
                        verwachte waarde gebruikt echte newlines (\n), niet
                        de letterlijke backslash-n. De oude JSON gebruikte
                        \\n, wat in de GUI letterlijk als "\n" werd getoond;
                        dat is met deze wijziging opgelost.
================================================================================
"""

from app.helpers.i18n import vertaal, wis_cache


def _assert_translations(taal: str, expected: dict[str, str]) -> None:
    wis_cache()
    for key, value in expected.items():
        assert vertaal(key, taal=taal) == value


def test_nederlandse_algemene_appvertalingen() -> None:
    _assert_translations("nl_NL", {
        "app.titel": "Electronics Diagnostic Tool Hub",
        "app.hoofdmenu": "Hoofdmenu",
        "menu.bestand": "Bestand",
        "menu.diagnose": "Diagnose",
        "menu.instellingen": "Instellingen",
        "menu.help": "Help",
        "menu.open_diagnose": "Diagnose openen",
        "menu.esr_test": "ESR-test",
        "menu.talen": "Talen",
        "menu.changelog": "Wijzigingslog",
        "menu.over": "Over",
        "menu.afsluiten": "Afsluiten",
        "tool.diagnose": "Diagnose",
        "tool.historiek": "Historiek",
        "tool.documentatie": "Documentatie",
        "knop.terug": "Terug",
        "knop.meting_opslaan": "Meting opslaan",
        "knop.veiligheidsinstructies": "Veiligheidsinstructies",
        "knop.beoordeel": "Beoordelen",
        "knop.wissen": "Wissen",
        "knop.verversen": "Verversen",
        "knop.herhaal_meting": "Meting herhalen",
        "knop.details": "Details",
        "dialog.over_title": "Over",
        "dialog.over_tekst": "Electronics Diagnostic Tool Hub\nCondensator- en ESR-validator\n\nVersie: {versie}",
        "dialog.changelog_title": "Wijzigingslog",
        "dialog.help_title": "Help",
        "tool_type.ESR_CAPACITOR": "ESR / Condensator",
    })


def test_engelse_algemene_appvertalingen() -> None:
    _assert_translations("en_US", {
        "app.titel": "Electronics Diagnostic Tool Hub",
        "app.hoofdmenu": "Main menu",
        "menu.bestand": "File",
        "menu.diagnose": "Diagnostics",
        "menu.instellingen": "Settings",
        "menu.help": "Help",
        "menu.open_diagnose": "Open diagnostics",
        "menu.esr_test": "ESR test",
        "menu.talen": "Languages",
        "menu.changelog": "Changelog",
        "menu.over": "About",
        "menu.afsluiten": "Exit",
        "tool.diagnose": "Diagnostics",
        "tool.historiek": "History",
        "tool.documentatie": "Documentation",
        "knop.terug": "Back",
        "knop.meting_opslaan": "Save measurement",
        "knop.veiligheidsinstructies": "Safety instructions",
        "knop.beoordeel": "Assess",
        "knop.wissen": "Clear",
        "knop.verversen": "Refresh",
        "knop.herhaal_meting": "Repeat measurement",
        "knop.details": "Details",
        "dialog.over_title": "About",
        "dialog.over_tekst": "Electronics Diagnostic Tool Hub\nCapacitor and ESR validator\n\nVersion: {versie}",
        "dialog.changelog_title": "Changelog",
        "dialog.help_title": "Help",
        "tool_type.ESR_CAPACITOR": "ESR / Capacitor",
    })


def test_over_tekst_placeholder_werkt_in_beide_talen() -> None:
    """De {versie}-placeholder moet in NL én EN worden ingevuld."""
    wis_cache()

    nl = vertaal("dialog.over_tekst", taal="nl_NL", versie="9.9.9")
    assert "9.9.9" in nl, f"NL Over-tekst bevat geen versie: {nl!r}"
    assert "{versie}" not in nl, "NL Over-tekst heeft de placeholder niet ingevuld."

    en = vertaal("dialog.over_tekst", taal="en_US", versie="9.9.9")
    assert "9.9.9" in en, f"EN Over-tekst bevat geen versie: {en!r}"
    assert "{versie}" not in en, "EN Over-tekst heeft de placeholder niet ingevuld."