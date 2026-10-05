"""
================================================================================
Module:     app/documentation/search_query.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-04
Auteur:     Bart Bossuyt

Doel:       Kleine, GUI-onafhankelijke zoektaal voor de documentatiebibliotheek.

            Ondersteunt:
              - spaties en komma's        = AND (alle termen moeten matchen)
              - pijp (|)                  = OR (minstens één term moet matchen)
              - prefix '-'                = exact-woord match
              - prefix '!'                = uitsluiten (mag niet voorkomen)
              - wildcard '%'              = één of meerdere tekens
              - default                   = substring match

            Precedentie: AND bindt strakker dan OR. Geen haakjes.

            Deze module bevat geen GUI-, service-, database- of i18n-logica.
            Ze werkt uitsluitend op een reeds opgebouwde tekstblob.

Wijzigingen:
  v1.0.0 (2026-10-04)  Eerste versie met parsen en evalueren van zoekquery's.
================================================================================
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True, slots=True)
class SearchTerm:
    """Eén term binnen een AND-groep."""

    text: str
    exact_word: bool = False
    excluded: bool = False
    wildcard: bool = False


@dataclass(frozen=True, slots=True)
class SearchAndGroup:
    """Eén AND-groep: alle termen moeten matchen."""

    terms: tuple[SearchTerm, ...]


@dataclass(frozen=True, slots=True)
class SearchClause:
    """Eén clause: minstens één AND-groep moet matchen (OR tussen groepen)."""

    or_groups: tuple[SearchAndGroup, ...]


@dataclass(frozen=True, slots=True)
class SearchQuery:
    """Geparseerde zoekquery: alle clauses moeten matchen (AND tussen clauses)."""

    clauses: tuple[SearchClause, ...]
    raw: str
    empty: bool = field(default=False)

    def is_empty(self) -> bool:
        return self.empty


def parse_search_query(text: str | None) -> SearchQuery:
    """Parseer een zoekterm naar een immutable SearchQuery.

    Lege of whitespace-only invoer levert een lege query op die alles matcht.
    Lege termen binnen een clause worden genegeerd.
    """
    raw = text if isinstance(text, str) else ""
    stripped = raw.strip()
    if not stripped:
        return SearchQuery(clauses=(), raw=raw, empty=True)

    clauses: list[SearchClause] = []
    for raw_clause in stripped.split():
        clause = _parse_clause(raw_clause)
        if clause is not None:
            clauses.append(clause)

    if not clauses:
        return SearchQuery(clauses=(), raw=raw, empty=True)

    return SearchQuery(clauses=tuple(clauses), raw=raw, empty=False)


def matches_query(text_blob: str, query: SearchQuery) -> bool:
    """Evalueer een query tegen een reeds opgebouwde (casefold) tekstblob.

    De caller is verantwoordelijk voor het casefolden van de blob en het
    aanleveren van een stabiele, voorspelbare tekstinhoud.
    """
    if query.empty:
        return True

    blob = text_blob if isinstance(text_blob, str) else ""
    blob_casefold = blob.casefold()

    for clause in query.clauses:
        if not _clause_matches(blob_casefold, clause):
            return False
    return True


def _parse_clause(raw_clause: str) -> SearchClause | None:
    or_groups: list[SearchAndGroup] = []
    for raw_or_group in raw_clause.split("|"):
        and_group = _parse_and_group(raw_or_group)
        if and_group is not None:
            or_groups.append(and_group)

    if not or_groups:
        return None
    return SearchClause(or_groups=tuple(or_groups))


def _parse_and_group(raw_and_group: str) -> SearchAndGroup | None:
    terms: list[SearchTerm] = []
    for raw_term in raw_and_group.split(","):
        term = _parse_term(raw_term)
        if term is not None:
            terms.append(term)

    if not terms:
        return None
    return SearchAndGroup(terms=tuple(terms))


def _parse_term(raw_term: str) -> SearchTerm | None:
    text = raw_term.strip()
    if not text:
        return None

    exact_word = False
    excluded = False

    if text.startswith("-"):
        exact_word = True
        text = text[1:]
    elif text.startswith("!"):
        excluded = True
        text = text[1:]

    if not text:
        return None

    wildcard = "%" in text
    return SearchTerm(
        text=text.casefold(),
        exact_word=exact_word,
        excluded=excluded,
        wildcard=wildcard,
    )


def _clause_matches(blob_casefold: str, clause: SearchClause) -> bool:
    for and_group in clause.or_groups:
        if _and_group_matches(blob_casefold, and_group):
            return True
    return False


def _and_group_matches(blob_casefold: str, and_group: SearchAndGroup) -> bool:
    for term in and_group.terms:
        if not _term_matches(blob_casefold, term):
            return False
    return True


def _term_matches(blob_casefold: str, term: SearchTerm) -> bool:
    if term.excluded:
        return not _substring_matches(blob_casefold, term.text)
    if term.exact_word:
        return _exact_word_matches(blob_casefold, term.text)
    if term.wildcard:
        return _wildcard_matches(blob_casefold, term.text)
    return _substring_matches(blob_casefold, term.text)


def _substring_matches(blob_casefold: str, needle: str) -> bool:
    if not needle:
        return True
    return needle in blob_casefold


_WORD_BOUNDARY = re.compile(r"(?<![0-9a-z])", re.IGNORECASE)


def _exact_word_matches(blob_casefold: str, needle: str) -> bool:
    if not needle:
        return True
    # Woordgrens = niet-[a-z0-9] aan beide kanten.
    pattern = re.compile(
        r"(?<![0-9a-z])" + re.escape(needle) + r"(?![0-9a-z])",
        re.IGNORECASE,
    )
    return pattern.search(blob_casefold) is not None


def _wildcard_matches(blob_casefold: str, pattern: str) -> bool:
    if not pattern:
        return True
    parts = [re.escape(p) for p in pattern.split("%")]
    regex = "(?s)" + ".*".join(parts)
    return re.search(regex, blob_casefold) is not None