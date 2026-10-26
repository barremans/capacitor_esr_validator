## Settings — open punten na chat 2 (2026-10-26)

### OV-S1: `language: null` geeft `taal=None` door
- **Status:** open, bewust niet gefixt in chat 2.
- **Effect:** `AppInstellingen.taal = None`. `i18n.vertaal` valt stil
  terug op de sleutel. `SettingsDialog._select` toont combo op index 0.
  GUI self-healt bij Toepassen (schrijft `"nl_NL"`).
- **Routering:** chat 8 (i18n).
- **Mogelijke fix:** `normaliseer_taal()` analoog aan `normaliseer_thema()`.

### OV-S2: geen `conftest.py`
- **Status:** open, bewust niet gefixt in chat 2.
- **Effect:** `tests/test_settings_main_window.py` leest de echte
  repo-`settings.json`. Verborgen afhankelijkheid.
- **Routering:** chat 7 (release / testinfrastructuur).
- **Mogelijke fix:** autouse-fixture in `tests/conftest.py`.

### OV-S4: scalaire velden niet type-gevalideerd
- **Status:** open, bewust niet gefixt in chat 2.
- **Effect:** `meetfrequentie_hz="hoog"` wordt opgeslagen als string.
  Downstream kan dit crashen (`"hoog" + 1` → TypeError). De GUI
  negeert het stil (`_select` → index 0) en self-healt bij Toepassen.
- **Routering:** chat 4 (schema v4), waar type-validatie onderdeel is
  van het nieuwe schema.
- **Mogelijke fix:** `typing.get_type_hints()` per veld in
  `_dataclass_from_dict`, of een aparte `valideer_instellingen()`-helper.

### OV-S3 (ingetrokken): dubbele `settings.json` in i18n-map
- **Status:** geen issue. Vertaalbestanden, geen app-settings.