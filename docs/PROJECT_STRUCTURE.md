# 📁 Projectstructuur

_Automatisch gegenereerd – niet handmatig aanpassen._

- 📁 **capacitor_esr_validator/**
  - 📁 **.pytest_cache/**
    - 📁 **v/**
      - 📁 **cache/**
        - 📄 **/.pytest_cache/v/cache/lastfailed**
        - 📄 **/.pytest_cache/v/cache/nodeids**
    - 📄 **/.pytest_cache/.gitignore**
    - 📄 **/.pytest_cache/CACHEDIR.TAG**
    - 📄 **/.pytest_cache/README.md**
  - 📁 **app/**
    - 📁 **config/**
      - 📄 **/app/config/instrument_profiles.py**
        ```text
        # Bestandsnaam: app/config/instrument_profiles.py
        # Beschrijving: Centrale instrumentprofielen voor meettoestellen. Een profiel
        # Auteur: Ontwikkelaar
        # Applicatie: Condensator- en ESR-validator (Windows)
        # Versie: 1.0.0
        # Datum: 2026-09-26
        ```
      - 📄 **/app/config/settings.py**
        ```text
        # Bestandsnaam: app/config/settings.py
        # Beschrijving: Centrale, aanpasbare instellingen voor de app.
        # Auteur: Ontwikkelaar
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Validator (Windows)
        # Versie: 1.3.0
        # Datum: 2026-09-27
        ```
    - 📁 **data/**
      - 📁 **documentation/**
        - 📄 **/app/data/documentation/catalog.json**
      - 📁 **references/**
        - 📄 **/app/data/references/esr_references.json**
      - 📄 **/app/data/.gitkeep**
    - 📁 **gui/**
      - 📁 **dialogs/**
        - 📄 **/app/gui/dialogs/.gitkeep**
        - 📄 **/app/gui/dialogs/settings_dialog.py**
          ```text
          # Bestandsnaam: app/gui/dialogs/settings_dialog.py
          # Beschrijving: Modale Settings-dialoog met tabs Algemeen, ESR / Condensator en
          # Auteur: Ontwikkelaar
          # Applicatie: Electronics Diagnostic Tool Hub / ESR Validator (Windows)
          # Versie: 1.1.0
          # Datum: 2026-09-27
          ```
      - 📄 **/app/gui/esr_test_screen.py**
        ```text
        # Bestandsnaam: app/gui/esr_test_screen.py
        # Beschrijving: Compact ESR-diagnosescherm voor nominale gegevens, meetcontext,
        # Auteur: Ontwikkelaar
        # Applicatie: Condensator- en ESR-validator (Windows)
        # Versie: 1.8.1
        # Datum: 2026-10-01
        ```
      - 📄 **/app/gui/history_screen.py**
        ```text
        # Bestandsnaam: app/gui/history_screen.py
        # Beschrijving: Compacte centrale read-only weergave van opgeslagen meethistoriek.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.11.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/gui/main_window.py**
        ```text
        # Bestandsnaam: app/gui/main_window.py
        # Beschrijving: Hoofdvenster van de Tool Hub met één-venster-navigatie.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 2.4.1
        # Datum: 2026-10-01
        ```
      - 📄 **/app/gui/styles.py**
        ```text
        # Bestandsnaam: app/gui/styles.py
        # Beschrijving: Centrale stijldefinities voor de Qt6 GUI.
        # Auteur: Ontwikkelaar
        # Applicatie: Condensator- en ESR-validator (Windows)
        # Versie: 1.2.0
        # Datum: 2026-09-27
        ```
    - 📁 **helpers/**
      - 📄 **/app/helpers/history_csv_export.py**
        ```text
        # Bestandsnaam: app/helpers/history_csv_export.py
        # Beschrijving: Kleine GUI- en database-onafhankelijke CSV-writer voor Historiek.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.0.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/helpers/history_detail_export.py**
        ```text
        # Bestandsnaam: app/helpers/history_detail_export.py
        # Beschrijving: Zet één volledige opgeslagen meetketen om naar een stabiele,
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.0.1
        # Datum: 2026-10-02
        ```
      - 📄 **/app/helpers/history_filters.py**
        ```text
        # Bestandsnaam: app/helpers/history_filters.py
        # Beschrijving: GUI-onafhankelijke opbouw van read-only historiekfilters.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.2.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/helpers/history_formatting.py**
        ```text
        # Bestandsnaam: app/helpers/history_formatting.py
        # Beschrijving: Kleine, GUI-onafhankelijke formatters voor centrale historiek en
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.2.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/helpers/i18n.py**
        ```text
        # Bestandsnaam: app/helpers/i18n.py
        # Beschrijving: Eenvoudige vertaalmodule. Leest JSON-vertaalbestanden uit
        # Auteur: Ontwikkelaar
        # Applicatie: Condensator- en ESR-validator (Windows)
        # Versie: 1.1.0
        # Datum: 2026-08-12
        ```
      - 📄 **/app/helpers/units.py**
        ```text
        # Bestandsnaam: app/helpers/units.py
        # Beschrijving: Kleine, herbruikbare hulpfuncties voor het parsen van decimale
        # Auteur: Ontwikkelaar
        # Applicatie: Condensator- en ESR-validator (Windows)
        # Versie: 1.0.0
        # Datum: 2026-08-11
        ```
    - 📁 **services/**
      - 📄 **/app/services/assessment_service.py**
        ```text
        # Bestandsnaam: app/services/assessment_service.py
        # Beschrijving: Kernlogica van de indicatieve beoordeling: capaciteitsvalidatie,
        # Auteur: Ontwikkelaar
        # Applicatie: Condensator- en ESR-validator (Windows)
        # Versie: 1.3.0
        # Datum: 2026-09-29
        ```
      - 📄 **/app/services/history_service.py**
        ```text
        # Bestandsnaam: app/services/history_service.py
        # Beschrijving: Applicatielaag voor read-only meet-historiek.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.1.1
        # Datum: 2026-10-01
        ```
      - 📄 **/app/services/measurement_persistence_service.py**
        ```text
        # Bestandsnaam: app/services/measurement_persistence_service.py
        # Beschrijving: Applicatielaag tussen de ESR-GUI en StorageService.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.1.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/services/repeat_measurement_service.py**
        ```text
        # Bestandsnaam: app/services/repeat_measurement_service.py
        # Beschrijving: Zet één opgeslagen meetdetail om naar een veilige preset voor
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.1.0
        # Datum: 2026-10-01
        ```
    - 📁 **storage/**
      - 📄 **/app/storage/database.py**
        ```text
        # Bestandsnaam: app/storage/database.py
        # Beschrijving: Veilige SQLite-connection- en initialisatielaag voor de lokale
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.1.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/storage/exceptions.py**
        ```text
        # Bestandsnaam: app/storage/exceptions.py
        # Beschrijving: Centrale exceptions voor filesystem-, database- en storageproblemen.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.0.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/storage/migrations.py**
        ```text
        # Bestandsnaam: app/storage/migrations.py
        # Beschrijving: Transactioneel en sequentieel migratieframework voor de lokale
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.1.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/storage/models.py**
        ```text
        # Bestandsnaam: app/storage/models.py
        # Beschrijving: Immutable Python-modellen voor de zeven storage-entiteiten van
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.1.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/storage/paths.py**
        ```text
        # Bestandsnaam: app/storage/paths.py
        # Beschrijving: Bepaalt uitsluitend waar mutable applicatiedata wordt opgeslagen.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.0.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/storage/schema.py**
        ```text
        # Bestandsnaam: app/storage/schema.py
        # Beschrijving: Declaratieve SQLite-DDL voor de lokale meetdatabase.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.1.0
        # Datum: 2026-10-01
        ```
      - 📄 **/app/storage/service.py**
        ```text
        # Bestandsnaam: app/storage/service.py
        # Beschrijving: Publieke storage-service voor de lokale SQLite-meethistoriek.
        # Auteur: Bart Bossuyt
        # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
        # Versie: 1.1.0
        # Datum: 2026-10-01
        ```
    - 📄 **/app/version.py**
      ```text
      # Beschrijving: Centrale versie-informatie van de applicatie.
      # Auteur: GEEN AUTEUR
      # Applicatie: GEEN APPLICATIE
      # Versie: V1.0.0
      ```
  - 📁 **assets/**
    - 📁 **icons/**
      - 📄 **/assets/icons/.gitkeep**
      - 📄 **/assets/icons/ESR.png**
  - 📁 **docs/**
    - 📄 **/docs/changelog.md**
    - 📄 **/docs/context.md**
    - 📄 **/docs/data_model.md**
    - 📄 **/docs/future_tools.md**
    - 📄 **/docs/help.md**
    - 📄 **/docs/PROJECT_STRUCTURE.md**
    - 📄 **/docs/python_header_standard.md**
    - 📄 **/docs/testgevallen_analyse.md**
    - 📄 **/docs/validation_rules.md**
  - 📁 **i18n/**
    - 📁 **locales/**
      - 📄 **/i18n/locales/en_US.json**
      - 📄 **/i18n/locales/nl_NL.json**
  - 📁 **installer/**
    - 📄 **/installer/.gitkeep**
  - 📁 **tests/**
    - 📄 **/tests/test_assessment.py**
      ```text
      # Bestandsnaam: tests/test_assessment.py
      # Beschrijving: Unit tests voor de assessment_service. Test alle 20 testgevallen
      # Auteur: Ontwikkelaar
      # Applicatie: Condensator- en ESR-validator (Windows)
      # Versie: 1.3.0
      # Datum: 2026-09-26
      ```
    - 📄 **/tests/test_esr_screen_settings_regressions.py**
      ```text
      # Bestandsnaam: tests/test_esr_screen_settings_regressions.py
      # Beschrijving: GUI-regressietests voor opgeslagen ESR/Condensator-defaults en
      # Auteur: Ontwikkelaar
      # Applicatie: Condensator- en ESR-validator (Windows)
      # Versie: 1.4.0
      # Datum: 2026-09-28
      ```
    - 📄 **/tests/test_gui_language_switch.py**
      ```text
      # Bestandsnaam: tests/test_gui_language_switch.py
      # Beschrijving: Regressietests voor live taalwissel in Hoofdmenu/Diagnose, ESR en
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_gui_regressions.py**
      ```text
      # Bestandsnaam: tests/test_gui_regressions.py
      # Beschrijving: Regressietests voor GUI-gerelateerde invoerregels die rechtstreeks
      # Auteur: Ontwikkelaar
      # Applicatie: Condensator- en ESR-validator (Windows)
      # Versie: 1.0.0
      # Datum: 2026-09-26
      ```
    - 📄 **/tests/test_history_csv_export.py**
      ```text
      # Bestandsnaam: tests/test_history_csv_export.py
      # Beschrijving: Regressietests voor read-only CSV-export van de volledige
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.2
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_history_date_filter.py**
      ```text
      # Bestandsnaam: tests/test_history_date_filter.py
      # Beschrijving: Regressietests voor de optionele lokale datum/periodefilter
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_history_export_settings.py**
      ```text
      # Bestandsnaam: tests/test_history_export_settings.py
      # Beschrijving: Regressietests voor de koppeling tussen algemene bestandsvoorkeuren
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.1
      # Datum: 2026-10-02
      ```
    - 📄 **/tests/test_history_export_v2.py**
      ```text
      # Bestandsnaam: tests/test_history_export_v2.py
      # Beschrijving: Regressietests voor analysewaardige detail-export, exportscope,
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.1.0
      # Datum: 2026-10-02
      ```
    - 📄 **/tests/test_history_filters.py**
      ```text
      # Bestandsnaam: tests/test_history_filters.py
      # Beschrijving: Regressietests voor de GUI-onafhankelijke historiekfilterbuilder.
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.1.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_history_formatting.py**
      ```text
      # Bestandsnaam: tests/test_history_formatting.py
      # Beschrijving: Regressietests voor centrale historiekformattering, inclusief
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.2.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_history_paging.py**
      ```text
      # Bestandsnaam: tests/test_history_paging.py
      # Beschrijving: Regressietests voor limit/offset paging in centrale Historiek.
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_history_robustness.py**
      ```text
      # Bestandsnaam: tests/test_history_robustness.py
      # Beschrijving: Regressietests voor read-only Historiek-robuustheid:
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_history_service.py**
      ```text
      # Bestandsnaam: tests/test_history_service.py
      # Beschrijving: Regressietests voor de read-only applicatieservice voor historiek.
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.1.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_i18n_history_filter_translations.py**
      ```text
      # Bestandsnaam: tests/test_i18n_history_filter_translations.py
      # Beschrijving: Bewaakt de NL/EN vertalingen voor de historiekfilterbalk.
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.1.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_i18n_history_translations.py**
      ```text
      # Bestandsnaam: tests/test_i18n_history_translations.py
      # Beschrijving: Controleert dat de nieuwe historiekteksten in beide locale-bestanden
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.2.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_i18n_repeat_measurement_translations.py**
      ```text
      # Bestandsnaam: tests/test_i18n_repeat_measurement_translations.py
      # Beschrijving: Controleert NL/EN vertalingen voor "Herhaal meting".
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_i18n_storage_translations.py**
      ```text
      # Bestandsnaam: tests/test_i18n_storage_translations.py
      # Beschrijving: Regressietests voor de NL/EN GUI-vertalingen van de lokale
      # Auteur: Bart Bossuyt
      # Applicatie: Condensator- en ESR-validator (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_instrument_profiles.py**
      ```text
      # Bestandsnaam: tests/test_instrument_profiles.py
      # Beschrijving: Test de toestelprofielen en toegelaten frequenties/testspanningen.
      # Auteur: Ontwikkelaar
      # Applicatie: Condensator- en ESR-validator (Windows)
      # Versie: 1.0.0
      # Datum: 2026-09-26
      ```
    - 📄 **/tests/test_measurement_methods.py**
      ```text
      # Bestandsnaam: tests/test_measurement_methods.py
      # Beschrijving: Geparametriseerde regressietests voor verschillende fysieke
      # Auteur: Ontwikkelaar
      # Applicatie: Condensator- en ESR-validator (Windows)
      # Versie: 1.0.0
      # Datum: 2026-09-26
      ```
    - 📄 **/tests/test_measurement_persistence_service.py**
      ```text
      # Bestandsnaam: tests/test_measurement_persistence_service.py
      # Beschrijving: Gerichte regressietests voor de koppeling van een reeds beoordeelde
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_navigation_regressions.py**
      ```text
      # Bestandsnaam: tests/test_navigation_regressions.py
      # Beschrijving: Regressietests voor Tool Hub -> Diagnose -> ESR navigatie.
      # Auteur: Bart Bossuyt
      # Applicatie: Condensator- en ESR-validator (Windows)
      # Versie: 1.0.0
      # Datum: 2026-09-27
      ```
    - 📄 **/tests/test_repeat_measurement_service.py**
      ```text
      # Bestandsnaam: tests/test_repeat_measurement_service.py
      # Beschrijving: Regressietests voor veilige voorbereiding van "Herhaal meting".
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_settings.py**
      ```text
      # Bestandsnaam: tests/test_settings.py
      # Beschrijving: Regressietests voor laden, opslaan en achterwaartse compatibiliteit
      # Auteur: Ontwikkelaar
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Validator (Windows)
      # Versie: 1.1.0
      # Datum: 2026-09-27
      ```
    - 📄 **/tests/test_settings_dialog.py**
      ```text
      # Bestandsnaam: tests/test_settings_dialog.py
      # Beschrijving: GUI-regressietests voor de Settings-dialoog.
      # Auteur: Ontwikkelaar
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Validator (Windows)
      # Versie: 1.1.0
      # Datum: 2026-09-27
      ```
    - 📄 **/tests/test_settings_main_window.py**
      ```text
      # Bestandsnaam: tests/test_settings_main_window.py
      # Beschrijving: Regressietests voor de koppeling tussen ToolHubWindow en Settings.
      # Auteur: Ontwikkelaar
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Validator (Windows)
      # Versie: 1.0.1
      # Datum: 2026-09-27
      ```
    - 📄 **/tests/test_storage_database.py**
      ```text
      # Bestandsnaam: tests/test_storage_database.py
      # Beschrijving: Gerichte regressietests voor SQLite connection- en database-
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_storage_migrations.py**
      ```text
      # Bestandsnaam: tests/test_storage_migrations.py
      # Beschrijving: Gerichte regressietests voor het transactionele migratieframework.
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_storage_multitool_v2.py**
      ```text
      # Bestandsnaam: tests/test_storage_multitool_v2.py
      # Beschrijving: Regressietests voor schema v2 multitool-discriminator en veilige
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_storage_paths.py**
      ```text
      # Bestandsnaam: tests/test_storage_paths.py
      # Beschrijving: Tests voor de Windows/runtime PathService.
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_storage_schema.py**
      ```text
      # Bestandsnaam: tests/test_storage_schema.py
      # Beschrijving: Gerichte regressietests voor storage models en SQLite schema v1.
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.1.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_storage_service.py**
      ```text
      # Bestandsnaam: tests/test_storage_service.py
      # Beschrijving: Gerichte regressietests voor StorageService v1.
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.0.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_storage_v1_completion.py**
      ```text
      # Bestandsnaam: tests/test_storage_v1_completion.py
      # Beschrijving: Afrondende regressietests voor de oorspronkelijke Storage v1-definitie
      # Auteur: Bart Bossuyt
      # Applicatie: Electronics Diagnostic Tool Hub / ESR Tester (Windows)
      # Versie: 1.1.0
      # Datum: 2026-10-01
      ```
    - 📄 **/tests/test_units.py**
      ```text
      # Beschrijving: Tests voor app/helpers/units.py — decimaalparsing en
      # Auteur: GEEN AUTEUR
      # Applicatie: GEEN APPLICATIE
      # Versie: V1.0.0
      ```
  - 📄 **/.gitattributes**
  - 📄 **/.gitignore**
  - 📄 **/LICENSE**
  - 📄 **/main.py**
    ```text
    # Bestandsnaam: main.py
    # Beschrijving: Entry point. Start de Qt6 GUI met donker thema en ToolHubWindow.
    # Auteur: Bart Bossuyt
    # Applicatie: Condensator- en ESR-validator (Windows)
    # Versie: 1.1.0
    # Datum: 2026-08-13
    ```
  - 📄 **/pyproject.toml**
  - 📄 **/README.md**
  - 📄 **/README_PATCH.md**
  - 📄 **/requirements.txt**
    ```text
    # Beschrijving: GEEN BESCHRIJVING
    # Auteur: GEEN AUTEUR
    # Applicatie: GEEN APPLICATIE
    # Versie: V1.0.0
    ```
  - 📄 **/settings.json**
