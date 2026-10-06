# Zoektaal voor de documentatiebibliotheek — ontwikkelaarsreferentie

**Versie:** 1.1.0
**Datum:** 2026-10-06
**Auteur:** Bart Bossuyt
**Doelgroep:** ontwikkelaars die zoekgedrag willen begrijpen, testen of uitbreiden.

**Wijzigingen:**
- v1.0.0 (2026-10-06)  Eerste versie.
- v1.1.0 (2026-10-06)  Fase 4I.1.c: `-%...%` beschreven als "stil genegeerd"
                        (§4.4, §6); §8 uitgebreid met motivatie per
                        uitbreidingspunt; nieuwe §8.1 "Bewust niet aanwezig
                        in versie 1.x" met alternatief per item.

Dit document beschrijft de **zoektaal** van de centrale documentatiebibliotheek
zoals geïmplementeerd in `app/documentation/search_query.py`, en hoe die taal
door `app/documentation/service.py` op de catalogus wordt toegepast.

Het is een **ontwikkelaarsdocument**. De eindgebruiker krijgt een lichtere,
meertalige uitleg via `app/gui/dialogs/search_help_dialog.py`
(i18n-keys onder `documentatie.help.*`).

---

## 1. Scope en verantwoordelijkheden

De zoektaal is bewust klein en GUI-onafhankelijk:

| Module | Verantwoordelijkheid |
|---|---|
| `app/documentation/search_query.py` | Parsen en evalueren van de zoektaal op een reeds opgebouwde tekstblob. Geen GUI, geen service, geen i18n, geen storage. |
| `app/documentation/service.py` | Catalogus laden, validatie, filters, opbouw van de **zoekblob** per document, en het aanroepen van `matches_query()`. |
| `app/gui/documentation_screen.py` | Verzamelt het zoekveld en de filterkeuzes, toont resultaten. Bevat zelf geen zoeklogica. |
| `app/gui/dialogs/search_help_dialog.py` | Toont eindgebruikersuitleg. Bevat geen zoeklogica. |

De zoektaal werkt **case-insensitief** en uitsluitend op tekst. Ze kent geen
datums, geen numerieke bereiken, geen veldnamen en geen haakjes.

---

## 2. Operatoren in één oogopslag

| Teken | Betekenis | Bindt | Voorbeeld | Matcht |
|---|---|---|---|---|
| (spatie) | AND tussen **clauses** | losse termen, geen haakjes | `esr meter` | blob bevat `esr` én `meter` |
| `,` | AND binnen één clause | strakker dan `\|` | `esr,meter` | idem, expliciet gegroepeerd |
| `\|` | OR tussen AND-groepen binnen één clause | losser dan `,` | `esr\|meter` | blob bevat `esr` **of** `meter` |
| `-` (prefix) | exact-woord match | per term | `-esr` | `esr` als los woord, niet als deel van `mesr` of `esrxyz` |
| `!` (prefix) | uitsluiten | per term | `!lcr` | blob bevat `lcr` **niet** |
| `%` | wildcard (één of meerdere tekens) | per term | `%meter` | `meter`, `micrometer`, `esr-meter` |
| (geen) | substring match | per term | `capa` | `capa` komt voor, waar dan ook |

**Precedentie (vast, geen haakjes):**

1. Binnen een term: prefix (`-` of `!`) en eventueel `%`-wildcard.
2. Binnen een AND-groep: `,` (alle termen moeten matchen).
3. Binnen een clause: `|` (minstens één AND-groep moet matchen).
4. Tussen clauses: spatie (alle clauses moeten matchen).

Deze volgorde is vastgelegd in de parser (`_parse_clause` → `_parse_and_group`
→ `_parse_term`) en in de evaluator (`matches_query` itereert over clauses en
eist dat **elke** clause matcht).

---

## 3. Formele grammatica

```
query       := clause (SPACE clause)*
clause      := and_group ('|' and_group)*
and_group   := term (',' term)*
term        := prefix? body
prefix      := '-' | '!'
body        := (TEXT | '%')+
```

- Witruimte rond `|` en `,` is toegestaan en wordt gestript.
- Lege termen (bv. `esr,,meter` of `,esr`) worden **stil genegeerd**.
- Lege clauses (bv. `esr||meter`) worden **stil genegeerd**.
- Een term die met `-` begint én `%` bevat (bv. `-%meter`) wordt **stil
  genegeerd** (zie §4.4 en §6).
- Een query die enkel uit prefixen bestaat (`-`, `!`) levert een **lege query**
  op; die matcht alles (zie §7).
- Casefolden gebeurt op de term én op de blob, zodat matching
  case-insensitief is.

---

## 4. Semantiek per operator

### 4.1 Substring (default)

Zonder prefix of `%` doet de term een **substring match** op de volledig
casefolden tekstblob:

```python
"_substring_matches(blob_casefold, term.text) -> term.text in blob_casefold
```

Er is geen woordgrens. `capa` matcht `capaciteit`, `capabel`, `meetcapa`, ...

### 4.2 Exact-woord (`-` prefix)

`-term` matcht alleen wanneer `term` als **los woord** voorkomt. De
woordgrens is gedefinieerd met een regex:

```python
r"(?<![0-9a-z])" + re.escape(needle) + r"(?![0-9a-z])"
```

- Voorloop- of volgtekens die geen `[0-9a-z]` zijn, gelden als grens.
- Dus `esr-meter`, `(esr)` en `esr.` bevatten allemaal het losse woord `esr`.
- `mesr` of `esrxyz` bevatten het **niet** (letters grenzen niet af).

Let op: het koppelteken `-` **binnen** een term wordt niet als operator
gezien. `-esr-meter` is één term met prefix `-` en body `esr-meter`; die
matcht alleen als de letterlijke tekst `esr-meter` als los woord voorkomt.

### 4.3 Uitsluiten (`!` prefix)

`!term` eist dat `term` **niet** als substring voorkomt. De evaluator keert
het resultaat van de substring-match om:

```python
if term.excluded:
    return not _substring_matches(blob_casefold, term.text)
```

Er is geen exact-woord-variant van uitsluiten: `!` werkt altijd als
substring-uitsluiting. Wil je een exact woord uitsluiten, dan moet dat via
een andere constructie (zie §6 en §8.1).

### 4.4 Wildcard (`%`)

`%` wordt geïnterpreteerd als "één of meerdere tekens" via een regex:

```python
parts = [re.escape(p) for p in pattern.split("%")]
regex = "(?s)" + ".*".join(parts)
re.search(regex, blob_casefold)
```

- Meerdere `%`-tekens in één term zijn toegestaan: `a%b%c` → `a.*b.*c`.
- `%` matcht ook een lege reeks, dus `%meter` matcht ook `meter`.
- De regex wordt op de **hele blob** toegepast (`re.search`, niet `fullmatch`),
  dus de wildcard-term matcht als het patroon ergens in de blob voorkomt.

#### Combinatie van prefix en wildcard

| Combinatie | Gedrag | Sinds |
|---|---|---|
| `%...%` | geldig, wildcard-substring | v1.0.0 |
| `!%...%` | geldig, substring-uitsluiting met wildcard | v1.0.0 |
| `-%...%` | **stil genegeerd** als lege term | v1.0.1 (Fase 4I.1.b) |

Reden voor het negeren van `-%...%`: de combinatie van "exact-woord" en
"wildcard" heeft binnen de huidige AST geen eenduidige, voorspelbare
betekenis. In plaats van een ambigu resultaat te produceren, wordt zo'n
term behandeld als een lege term — consistent met hoe de parser ook met
lege termen na een komma omgaat.

De gebruiker merkt hier niets van: de rest van de query blijft gewoon
werken. `esr,-%meter` gedraagt zich dus hetzelfde als `esr`.

### 4.5 AND via `,` en via spatie

- **Binnen één clause** met `,`: alle termen moeten matchen.
- **Tussen clauses** met een spatie: alle clauses moeten matchen.

Beide zijn dus AND, maar op een ander niveau:

```
"esr,meter"      → 1 clause, 1 AND-groep met 2 termen
"esr meter"      → 2 clauses, elk 1 AND-groep met 1 term
```

Semantisch equivalent in de evaluator (`elke clause moet matchen`), maar
structureel anders in de AST. Tests in `tests/test_search_query.py`
controleren dat verschil expliciet.

### 4.6 OR via `|`

- **Binnen één clause** met `|`: minstens één AND-groep moet matchen.
- `|` heeft **lagere** precedentie dan `,`.

Voorbeeld:

```
"esr,meter|panasonic"  → 1 clause:
                            AND-groep 1: esr AND meter
                            AND-groep 2: panasonic
                          matcht als (esr AND meter) OF (panasonic)
```

---

## 5. Doorzoekbare velden

De zoektaal werkt op een **tekstblob** die door de service per document wordt
opgebouwd. Alleen **menselijke, beschrijvende metadata** komt in de blob.
Technische identificatie en contextkoppelingen worden bewust uitgesloten
(`service.py::_search_blob`).

### 5.1 Wel in de blob

| Veld | Bron |
|---|---|
| `title` | catalogus (`DocumentMetadata.title`) |
| `category` | catalogus (enum-waarde, bv. `MEASUREMENT_TECHNIQUE`) |
| `manufacturer` | catalogus |
| `series` | catalogus |
| `part_number` | catalogus |
| `document_version` | catalogus |
| `document_date` | catalogus |
| `notes` | catalogus |
| `source_url` | catalogus |

Alle waarden worden `casefold()` doorlopen en met `\n` verbonden. Lege of
`None`-waarden worden overgeslagen.

### 5.2 Bewust NIET in de blob

| Veld | Waarom niet | Waar dan wel |
|---|---|---|
| `document_id` | technische identifier | directe lookup via `get_document()` |
| `title_key` | i18n-sleutel | GUI lost de titel op via `title` |
| `source_path` | intern pad | niet doorzoekbaar |
| `tool_keys` | context-ID | filter `tool_key=...` |
| `component_types` | context-ID | filter `component_type=...` |
| `test_keys` | context-ID | filter `test_key=...` |
| `measurement_methods` | context-ID | filter `measurement_method=...` |
| `instrument_keys` | context-ID | filter `instrument_key=...` |
| `topics` | context-ID | filter `topic=...` |
| `provenance.*` | metadata *over* het document | niet doorzoekbaar |

Reden: het vrije zoekveld is bedoeld voor menselijke zoekwoorden
(concepten, fabrikant, serie). Contextkoppelingen horen bij de filters,
zodat de gebruiker die expliciet kan combineren.

### 5.3 Combinatie met filters

`DocumentationService.list_documents()` past **eerst** de metadatafilters
toe (`category`, `tool_key`, `component_type`, ...) en **daarna** de
zoektaal. Documenten die een filter niet halen, worden nooit aan
`matches_query()` aangeboden.

Filters combineren onderling met AND. Binnen één filter is de match
"waarde zit in de betreffende tuple" — er is geen OR of negatie op
filterniveau.

---

## 6. Fallback- en randgevallen

| Situatie | Gedrag |
|---|---|
| `search_text` is `None` | lege query, matcht alles |
| `search_text` is lege string of enkel witruimte | lege query, matcht alles |
| `search_text` bestaat enkel uit `-` of `!` | lege query, matcht alles |
| Lege term na `,` of `\|` | wordt genegeerd |
| Lege AND-groep na `\|` | wordt genegeerd |
| Term met prefix `-` én `%` (bv. `-%meter`) | wordt **stil genegeerd** (sinds v1.0.1 / Fase 4I.1.b) |
| Term met prefix `!` én `%` (bv. `!%meter`) | geldig: substring-uitsluiting met wildcard |
| Onbekend teken (bv. `(`, `)`, `*`) | geen speciale betekenis; wordt letterlijk als tekst gematcht |
| Blob is `None` of geen string | wordt behandeld als lege string; alleen lege query matcht dan |

**Belangrijke beperking:** er is **geen** manier om een exact-woord
uitsluiting te combineren (`!-term` wordt geparseerd als `!` prefix
gevolgd door body `-term`). Wie dat nodig heeft, moet de zoektaal
uitbreiden (zie §8 en §8.1).

---

## 7. Voorbeelden met verwacht resultaat

Uitgaande van een blob met daarin onder meer `esr-lcr-meter`,
`esr en capaciteit meten met een lcr-meter`, `meettechniek`, `panasonic`,
`fm`, `internal/nl_nl/lcr_meter_measurement.md`:

| Query | Matcht? | Waarom |
|---|---|---|
| `capa` | ja | substring `capa` in `capaciteit` |
| `xyz` | nee | komt nergens voor |
| `esr,lcr` | ja | beide aanwezig |
| `esr,xyz` | nee | `xyz` ontbreekt |
| `esr lcr` | ja | twee clauses, elk aanwezig |
| `xyz\|panasonic` | ja | tweede OR-groep matcht |
| `xyz\|abc` | nee | geen van beide OR-groepen matcht |
| `esr,meter\|panasonic` | ja | eerste AND-groep matcht |
| `-panasonic` | ja | `panasonic` staat op een woordgrens |
| `-met` | nee | `met` zit binnen `meter`, geen los woord |
| `-esr` in `mesr en lcr` | nee | `esr` is geen los woord (m zit ervoor) |
| `-esr` in `esr-meter` | ja | koppelteken is woordgrens |
| `!panasonic` | nee | `panasonic` komt voor |
| `!xyz` | ja | `xyz` komt niet voor |
| `esr !lcr` | nee | `lcr` komt voor |
| `%meter` | ja | matcht o.a. `lcr-meter` |
| `meter%` | ja | matcht o.a. `meter` (leeg staartdeel) |
| `es%r` | ja | matcht `esr` |
| `-%meter` | n.v.t. | term wordt stil genegeerd; `-%meter` gedraagt zich als lege query (matcht alles) |
| `esr,-%meter` | ja | `esr` blijft, `-%meter` wordt genegeerd → matcht als `esr` |
| `!%meter` | nee | `meter` komt voor → uitsluiting faalt |

Deze voorbeelden zijn 1-op-1 terug te vinden in `tests/test_search_query.py`.

---

## 8. Uitbreidingspunten

De zoektaal is expliciet klein gehouden. Uitbreiden betekent: **parser
aanpassen, AST uitbreiden, evaluator aanpassen, tests toevoegen**. Enkele
mogelijke richtingen, met motivatie waarom ze nu **niet** aanwezig zijn:

- **Haakjes** voor expliciete precedentie (`(a|b),c`).
  *Waarom niet:* de huidige vaste precedentie (`-`/`!` → `,` → `|` → spatie)
  dekt de meeste praktijkgevallen en houdt de parser klein. Haakjes vragen
  een echte tokenizer en een geneste AST; dat is een onevenredig grote
  stap voor de huidige schaal van de bibliotheek.
- **Frase-match** met aanhalingstekens (`"lcr meter"` als vaste reeks).
  *Waarom niet:* de bibliotheek heeft nu 8 documenten; substring-zoeken op
  losse woorden is voldoende. Frase-match zou een aparte AST-vorm en
  eigen evaluatie vragen.
- **Veldscoped zoeken** (`title:panasonic`, `manufacturer:fm`).
  *Waarom niet:* de zoektaal werkt op één vlakke tekstblob, zonder
  veldscheiding. Veldscheiding toevoegen zou `_search_blob()` moeten
  herstructureren — en dat raakt de Documentatie-service, die bewust
  read-only en eenvoudig is.
- **Numerieke of datumfilters** (`date>=2024`, `version>1.2`).
  *Waarom niet:* de blob is tekst; numerieke vergelijkingen vereisen
  getypeerde velden en een aparte filterlaag. De Documentatie-service
  heeft daar nu geen infrastructuur voor.
- **Exact-woord uitsluiten** (nieuw prefix, bv. `^-term`).
  *Waarom niet:* de huidige prefixen (`-`, `!`) dekken exact-woord-match
  en substring-uitsluiting. Een derde prefix voor de combinatie zou de
  grammatica nodeloos complex maken voor een randgeval.

Bij elke uitbreiding gelden de kernregels van het project:
- zoektaal blijft GUI-onafhankelijk;
- de AST blijft immutable (`frozen=True, slots=True`);
- de evaluator blijft vrij van I/O;
- nieuwe operatoren krijgen **eigen tests** in `tests/test_search_query.py`;
- de eindgebruikersuitleg in `search_help_dialog.py` wordt bijgewerkt
  wanneer een operator voor gebruikers zichtbaar wordt.

### 8.1 Bewust niet aanwezig in versie 1.x

Onderstaande tabel vat samen wat een gebruiker **niet** kan met de
zoektaal in versie 1.x, en wat het dichtstbijzijnde alternatief is.

| Niet mogelijk | Alternatief binnen 1.x |
|---|---|
| Haakjes voor expliciete precedentie | Herformuleer de query in meerdere clauses; de vaste precedentie (`-`/`!` → `,` → `\|` → spatie) is meestal voldoende. |
| Frase-match (`"lcr meter"` als vaste reeks) | Combineer losse woorden met een komma (`lcr,meter`); dat matcht documenten waarin beide woorden voorkomen, niet per se als reeks. |
| Veldscoped zoeken (`title:...`, `manufacturer:...`) | Gebruik het vrije zoekveld voor menselijke metadata; gebruik de filter-dropdowns voor categorie en tool. |
| Numerieke of datumfilters (`date>=2024`) | Sorteer of filter visueel op de datum-/versiekolom; de zoektaal filtert niet op getallen of datums. |
| Exact-woord uitsluiten (`!-term` werkt niet) | Sluit breder uit (`!term` sluit ook `mesr` uit) en verfijn daarna handmatig in de resultatenlijst. |
| `-%...%` (exact-woord + wildcard) | Wordt sinds v1.0.1 stil genegeerd. Gebruik in plaats daarvan `-%term` zonder wildcard, of `!%term` voor uitsluiting met wildcard. |
| Wildcard midden in een exact-woord | Niet mogelijk; de combinatie `-%...%` is bewust genegeerd. Splits op in twee queries of gebruik substring met `%` zonder exact-woord-prefix. |

---

## 9. Verwijzingen

| Bestand | Rol |
|---|---|
| `app/documentation/search_query.py` | parser + evaluator |
| `app/documentation/service.py` | blobopbouw, filters, aanroep van de zoektaal |
| `app/documentation/models.py` | metadata- en enumdefinities |
| `app/gui/documentation_screen.py` | GUI-koppeling (zoekveld + filters) |
| `app/gui/dialogs/search_help_dialog.py` | eindgebruikersuitleg (i18n) |
| `tests/test_search_query.py` | regressietests voor de zoektaal |
| `tests/test_documentation_service.py` | regressietests voor blob + filters |
| `i18n/locales/nl_NL/documentation.json` | NL-uitleg `documentatie.help.*` |
| `i18n/locales/en_US/documentation.json` | EN-uitleg `documentatie.help.*` |