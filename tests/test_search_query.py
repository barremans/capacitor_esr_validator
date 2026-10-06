"""
================================================================================
Module:     tests/test_search_query.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de GUI-onafhankelijke zoektaal.

            Dekt parsen, evalueren en alle operatoren:
              - default substring
              - '-' exact-woord
              - '!' uitsluiten
              - '%' wildcard
              - ',' en spatie = AND
              - '|' = OR
              - lege query = alles matcht
              - combinatie '-' + '%' wordt genegeerd (Fase 4I.1.b)

Wijzigingen:
  v1.0.0 (2026-10-04)  Eerste versie.
  v1.0.1 (2026-10-06)  Fase 4I.1.b: vier tests toegevoegd voor het stil
                        negeren van termen met prefix '-' én wildcard '%'.
                        Bewijst dat '!%...' blijft werken en dat de rest
                        van de query onaangeroerd blijft.
================================================================================
"""

from __future__ import annotations

import pytest

from app.documentation.search_query import (
    SearchAndGroup,
    SearchClause,
    SearchQuery,
    SearchTerm,
    matches_query,
    parse_search_query,
)


BLOB = (
    "esr-lcr-meter\n"
    "esr en capaciteit meten met een lcr-meter\n"
    "meettechniek\n"
    "panasonic\n"
    "fm\n"
    "internal/nl_nl/lcr_meter_measurement.md\n"
)


# ---------------------------------------------------------------------------
# Parsing — structuur
# ---------------------------------------------------------------------------


def test_parse_empty_returns_empty_query():
    query = parse_search_query("")
    assert query.is_empty() is True
    assert query.clauses == ()


def test_parse_whitespace_only_returns_empty_query():
    query = parse_search_query("    \t\n   ")
    assert query.is_empty() is True


def test_parse_none_returns_empty_query():
    query = parse_search_query(None)
    assert query.is_empty() is True


def test_parse_single_term_creates_one_clause_one_group():
    query = parse_search_query("esr")
    assert query.is_empty() is False
    assert len(query.clauses) == 1
    clause = query.clauses[0]
    assert len(clause.or_groups) == 1
    group = clause.or_groups[0]
    assert len(group.terms) == 1
    assert group.terms[0].text == "esr"
    assert group.terms[0].exact_word is False
    assert group.terms[0].excluded is False
    assert group.terms[0].wildcard is False


def test_parse_comma_creates_and_group_with_two_terms():
    query = parse_search_query("esr,meter")
    assert len(query.clauses) == 1
    group = query.clauses[0].or_groups[0]
    assert len(group.terms) == 2
    assert group.terms[0].text == "esr"
    assert group.terms[1].text == "meter"


def test_parse_pipe_creates_or_groups():
    query = parse_search_query("esr|meter")
    assert len(query.clauses) == 1
    clause = query.clauses[0]
    assert len(clause.or_groups) == 2
    assert clause.or_groups[0].terms[0].text == "esr"
    assert clause.or_groups[1].terms[0].text == "meter"


def test_parse_pipe_with_and_inside_group():
    query = parse_search_query("esr,meter|capaciteit")
    assert len(query.clauses) == 1
    clause = query.clauses[0]
    assert len(clause.or_groups) == 2
    assert len(clause.or_groups[0].terms) == 2  # esr AND meter
    assert len(clause.or_groups[1].terms) == 1  # capaciteit


def test_parse_spaces_create_multiple_clauses():
    query = parse_search_query("esr meter")
    assert len(query.clauses) == 2


def test_parse_term_is_casefolded():
    query = parse_search_query("ESR")
    assert query.clauses[0].or_groups[0].terms[0].text == "esr"


# ---------------------------------------------------------------------------
# Parsing — prefixen
# ---------------------------------------------------------------------------


def test_parse_minus_prefix_marks_exact_word():
    query = parse_search_query("-esr")
    term = query.clauses[0].or_groups[0].terms[0]
    assert term.text == "esr"
    assert term.exact_word is True
    assert term.excluded is False


def test_parse_bang_prefix_marks_excluded():
    query = parse_search_query("!lcr")
    term = query.clauses[0].or_groups[0].terms[0]
    assert term.text == "lcr"
    assert term.excluded is True
    assert term.exact_word is False


def test_parse_percent_marks_wildcard():
    query = parse_search_query("%meter")
    term = query.clauses[0].or_groups[0].terms[0]
    assert term.text == "%meter"
    assert term.wildcard is True


def test_parse_leading_minus_only_is_dropped():
    query = parse_search_query("-")
    assert query.is_empty() is True


def test_parse_leading_bang_only_is_dropped():
    query = parse_search_query("!")
    assert query.is_empty() is True


# ---------------------------------------------------------------------------
# Parsing — lege termen
# ---------------------------------------------------------------------------


def test_parse_repeated_comma_ignores_empty_terms():
    query = parse_search_query("esr,,meter")
    group = query.clauses[0].or_groups[0]
    assert len(group.terms) == 2


def test_parse_repeated_pipe_ignores_empty_groups():
    query = parse_search_query("esr||meter")
    clause = query.clauses[0]
    assert len(clause.or_groups) == 2


def test_parse_leading_comma_ignored():
    query = parse_search_query(",esr")
    group = query.clauses[0].or_groups[0]
    assert len(group.terms) == 1
    assert group.terms[0].text == "esr"


# ---------------------------------------------------------------------------
# Parsing — '-' gecombineerd met '%' wordt genegeerd (Fase 4I.1.b)
# ---------------------------------------------------------------------------


def test_parse_minus_with_wildcard_is_dropped():
    """'-%meter' heeft geen eenduidige betekenis en wordt stil genegeerd."""
    query = parse_search_query("-%meter")
    assert query.is_empty() is True


def test_parse_minus_with_wildcard_inside_is_dropped():
    """'-me%ter' wordt om dezelfde reden genegeerd."""
    query = parse_search_query("-me%ter")
    assert query.is_empty() is True


def test_parse_minus_with_wildcard_between_valid_terms():
    """'esr,-%meter' behoudt 'esr', negeert '-%meter'."""
    query = parse_search_query("esr,-%meter")
    assert query.is_empty() is False
    group = query.clauses[0].or_groups[0]
    assert len(group.terms) == 1
    assert group.terms[0].text == "esr"


def test_parse_bang_with_wildcard_still_works():
    """'!%meter' blijft geldig: substring-uitsluiting met wildcard."""
    query = parse_search_query("!%meter")
    assert query.is_empty() is False
    term = query.clauses[0].or_groups[0].terms[0]
    assert term.text == "%meter"
    assert term.excluded is True
    assert term.exact_word is False
    assert term.wildcard is True


# ---------------------------------------------------------------------------
# Evalueren — default substring
# ---------------------------------------------------------------------------


def test_substring_matches_inside_blob():
    query = parse_search_query("capa")
    assert matches_query(BLOB, query) is True


def test_substring_no_match():
    query = parse_search_query("xyz")
    assert matches_query(BLOB, query) is False


def test_substring_is_case_insensitive():
    query = parse_search_query("PANASONIC")
    assert matches_query(BLOB, query) is True


# ---------------------------------------------------------------------------
# Evalueren — AND
# ---------------------------------------------------------------------------


def test_and_via_comma_requires_all_terms():
    query = parse_search_query("esr,lcr")
    assert matches_query(BLOB, query) is True

    query2 = parse_search_query("esr,xyz")
    assert matches_query(BLOB, query2) is False


def test_and_via_space_requires_all_terms():
    query = parse_search_query("esr lcr")
    assert matches_query(BLOB, query) is True

    query2 = parse_search_query("esr xyz")
    assert matches_query(BLOB, query2) is False


# ---------------------------------------------------------------------------
# Evalueren — OR
# ---------------------------------------------------------------------------


def test_or_matches_when_at_least_one_group_matches():
    query = parse_search_query("xyz|panasonic")
    assert matches_query(BLOB, query) is True


def test_or_fails_when_no_group_matches():
    query = parse_search_query("xyz|abc")
    assert matches_query(BLOB, query) is False


def test_or_and_and_combined():
    # (esr AND meter) OR (panasonic)
    query = parse_search_query("esr,meter|panasonic")
    assert matches_query(BLOB, query) is True

    # (esr AND meter) OR (abc) — eerste groep matcht
    query2 = parse_search_query("esr,meter|abc")
    assert matches_query(BLOB, query2) is True

    # (xyz) OR (abc) — geen matcht
    query3 = parse_search_query("xyz|abc")
    assert matches_query(BLOB, query3) is False


# ---------------------------------------------------------------------------
# Evalueren — exact-woord
# ---------------------------------------------------------------------------


def test_exact_word_matches_standalone_word():
    query = parse_search_query("-panasonic")
    assert matches_query(BLOB, query) is True


def test_exact_word_does_not_match_inside_larger_word():
    # 'meter' komt voor als los woord EN als deel van 'lcr-meter'.
    # Exact-woord moet de losse versie vinden via woordgrens.
    blob = "micrometer en meter"
    query = parse_search_query("-meter")
    assert matches_query(blob, query) is True

    # 'met' zit in 'meter' maar is geen los woord.
    query2 = parse_search_query("-met")
    assert matches_query(blob, query2) is False


def test_exact_word_does_not_match_when_glued_to_letters():
    blob = "mesr en lcr"
    query = parse_search_query("-esr")
    assert matches_query(blob, query) is False


def test_exact_word_hyphen_is_boundary():
    blob = "esr-meter"
    query = parse_search_query("-esr")
    assert matches_query(blob, query) is True


# ---------------------------------------------------------------------------
# Evalueren — uitsluiten
# ---------------------------------------------------------------------------


def test_exclusion_fails_when_term_present():
    query = parse_search_query("!panasonic")
    assert matches_query(BLOB, query) is False


def test_exclusion_passes_when_term_absent():
    query = parse_search_query("!xyz")
    assert matches_query(BLOB, query) is True


def test_exclusion_combined_with_required_term():
    query = parse_search_query("esr !lcr")
    assert matches_query(BLOB, query) is False  # lcr zit in blob

    query2 = parse_search_query("esr !xyz")
    assert matches_query(BLOB, query2) is True


# ---------------------------------------------------------------------------
# Evalueren — wildcard
# ---------------------------------------------------------------------------


def test_wildcard_matches_prefix():
    query = parse_search_query("%meter")
    assert matches_query("micrometer", query) is True
    assert matches_query("meter", query) is True
    assert matches_query("para", query) is False


def test_wildcard_matches_suffix():
    query = parse_search_query("meter%")
    assert matches_query("meterx", query) is True
    assert matches_query("meter", query) is True
    assert matches_query("para", query) is False


def test_wildcard_matches_inside():
    query = parse_search_query("es%r")
    assert matches_query("esr", query) is True
    assert matches_query("eer", query) is False


# ---------------------------------------------------------------------------
# Evalueren — lege query
# ---------------------------------------------------------------------------


def test_empty_query_matches_anything():
    query = parse_search_query("")
    assert matches_query(BLOB, query) is True
    assert matches_query("", query) is True


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_search_query_is_immutable():
    from dataclasses import FrozenInstanceError

    query = parse_search_query("esr")
    with pytest.raises(FrozenInstanceError):
        query.empty = True  # type: ignore[misc]


def test_search_term_is_immutable():
    from dataclasses import FrozenInstanceError

    term = SearchTerm(text="esr")
    with pytest.raises(FrozenInstanceError):
        term.text = "lcr"  # type: ignore[misc]