# =============================================================================
# Electronics Diagnostic Tool Hub / ESR Tester
# File:    github_feedback_config.py
# Role:    App-specifieke instellingen voor het uniforme GitHub-
#          feedbackpakket (github_feedback.py / bug_report_dialog.py /
#          github_cases.py): naam van de app, doelrepo voor de meldingen,
#          en hoe de naam van de melder en de app-versie bepaald worden.
#          Dit is het ENIGE bestand van het pakket dat per app verschilt
#          (naast github_secret_local.py, dat het token bevat). Bevat geen
#          token en mag dus gewoon in git.
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 (2026-10-14) - Fase 9G. Eerste versie voor ESR Tester,
#                              afgeleid van het ArticleSearch-sjabloon.
#                              Verschillen:
#                                - APP_NAME = "ESR Tester"
#                                - GITHUB_REPO = "capacitor_esr_validator"
#                                - get_reporter_name(): geen Azure AD-login
#                                  in deze app, dus Windows-gebruikersnaam
#                                  via getpass (§5.3 van het uitrolpakket).
#                                - get_app_version(): versie staat in
#                                  app/version.py (mappenstructuur), niet
#                                  in version.py in de root (§5.2).
# =============================================================================
#
# LET OP: importeer hier bovenaan GEEN app-modules (version, ...).
# check_github_secret.py leest dit bestand ook buiten de app om, tijdens
# de build. App-modules horen enkel BINNEN de functies hieronder.

APP_NAME = "ESR Tester"
GITHUB_OWNER = "barremans"
GITHUB_REPO = "capacitor_esr_validator"


def get_reporter_name() -> str:
    """
    Naam voor het veld "Je naam" in het meldscherm. Een niet-lege waarde
    wordt vooringevuld en read-only gemaakt; een lege waarde laat het veld
    leeg en bewerkbaar (zelfde gedrag als bug_report_dialog.py v2.0.0).

    ESR Tester heeft geen Azure AD-login, dus gebruiken we de Windows-
    gebruikersnaam (§5.3 van GITHUB_FEEDBACK_UITROL.md). Dat is de naam
    die de melder toch al kent en die IT kan herleiden naar een persoon.
    """
    import getpass
    try:
        return (getpass.getuser() or "").strip()
    except Exception:
        return ""


def get_app_version() -> str:
    """Versie van de app, vermeld in de kopregel van elke melding."""
    try:
        from app.version import __version__
        return str(__version__)
    except Exception:
        return ""