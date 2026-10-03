"""
================================================================================
Module:     tests/test_i18n_modular.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Regressietests voor modulaire vertalingen, dynamische taalontdekking,
            fallback en duplicate-key detectie.

Wijzigingen:
  v1.0.0 (2026-10-03)  Eerste tests voor de modulaire i18n-architectuur.
================================================================================
"""

from __future__ import annotations

import json

import app.helpers.i18n as i18n


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _language(root, code, native_name, *, enabled=True, sort_order=100):
    language_dir = root / code
    _write_json(
        language_dir / "language.json",
        {
            "_meta": {
                "code": code,
                "name": native_name,
                "native_name": native_name,
                "enabled": enabled,
                "sort_order": sort_order,
            }
        },
    )
    return language_dir


def test_modulaire_taal_wordt_automatisch_ontdekt(tmp_path, monkeypatch):
    nl = _language(tmp_path, "nl_NL", "Nederlands", sort_order=10)
    de = _language(tmp_path, "de_DE", "Deutsch", sort_order=20)
    _write_json(nl / "app.json", {"app": {"titel": "Titel"}})
    _write_json(de / "app.json", {"app": {"titel": "Titel DE"}})

    monkeypatch.setattr(i18n, "I18N_ROOT", tmp_path)
    i18n.wis_cache()

    infos = i18n.beschikbare_taalinfos()

    assert [info.code for info in infos] == ["nl_NL", "de_DE"]
    assert [info.native_name for info in infos] == ["Nederlands", "Deutsch"]
    assert i18n.beschikbare_talen() == ["nl_NL", "de_DE"]


def test_uitgeschakelde_taal_verschijnt_niet(tmp_path, monkeypatch):
    nl = _language(tmp_path, "nl_NL", "Nederlands")
    fr = _language(tmp_path, "fr_FR", "Français", enabled=False)
    _write_json(nl / "app.json", {"app": {"titel": "Titel"}})
    _write_json(fr / "app.json", {"app": {"titel": "Titre"}})

    monkeypatch.setattr(i18n, "I18N_ROOT", tmp_path)
    i18n.wis_cache()

    assert i18n.beschikbare_talen() == ["nl_NL"]


def test_modules_worden_samengevoegd_zonder_gui_api_wijziging(tmp_path, monkeypatch):
    nl = _language(tmp_path, "nl_NL", "Nederlands")
    _write_json(nl / "app.json", {"app": {"titel": "Applicatie"}})
    _write_json(
        nl / "documentation.json",
        {"documentatie": {"titel": "Documentatie"}},
    )

    monkeypatch.setattr(i18n, "I18N_ROOT", tmp_path)
    i18n.wis_cache()

    assert i18n.vertaal("app.titel", taal="nl_NL") == "Applicatie"
    assert i18n.vertaal("documentatie.titel", taal="nl_NL") == "Documentatie"


def test_ontbrekende_module_of_sleutel_valt_terug_op_nederlands(tmp_path, monkeypatch):
    nl = _language(tmp_path, "nl_NL", "Nederlands")
    de = _language(tmp_path, "de_DE", "Deutsch")
    _write_json(
        nl / "documentation.json",
        {"documentatie": {"openen": "Openen"}},
    )
    _write_json(de / "app.json", {"app": {"titel": "Anwendung"}})

    monkeypatch.setattr(i18n, "I18N_ROOT", tmp_path)
    i18n.wis_cache()

    assert i18n.vertaal("documentatie.openen", taal="de_DE") == "Openen"
    assert i18n.vertaal("bestaat.niet", taal="de_DE") == "bestaat.niet"


def test_dubbele_sleutel_tussen_modules_wordt_geweigerd(tmp_path, monkeypatch):
    nl = _language(tmp_path, "nl_NL", "Nederlands")
    _write_json(nl / "app.json", {"knop": {"terug": "Terug"}})
    _write_json(nl / "documentation.json", {"knop": {"terug": "Nogmaals terug"}})

    monkeypatch.setattr(i18n, "I18N_ROOT", tmp_path)
    i18n.wis_cache()

    try:
        i18n.vertaal("knop.terug", taal="nl_NL")
    except ValueError as exc:
        assert "Dubbele vertaalsleutel" in str(exc)
        assert "knop.terug" in str(exc)
    else:
        raise AssertionError("Dubbele sleutel had geweigerd moeten worden.")
