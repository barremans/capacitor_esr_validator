# Limitations of in-circuit capacitor measurements

In-circuit measurement is fast and useful for screening, but parallel circuit paths can strongly affect capacitance and ESR.

## Possible parallel paths

These include:

- multiple capacitors in parallel;
- ceramic bypass capacitors;
- resistors;
- inductors;
- transformer windings;
- semiconductors;
- other loads on the same rail.

## ESR

### Clearly too high

A clearly excessive ESR in-circuit is suspicious. Parallel paths usually make the measured ESR lower rather than higher.

Practical next step:

`ESR too high → disconnect one lead → measure again`

### Normal or low

A normal or low ESR does not prove that the individual capacitor is good.

Possible explanations:

- parallel good capacitor;
- low resistance;
- shorted component;
- other low impedance on the rail.

## Capacitance

In-circuit capacitance measurement can be wrong because of parallel capacitors, semiconductors and resistors. A much too high measured capacitance is often a parallel-path effect.

## Capacitor banks

With parallel banks:

- total capacitance is the sum;
- total ESR decreases;
- one bad capacitor can be masked.

## Confirmation

When the result matters or does not match circuit behavior, disconnect at least one terminal or completely remove the component and measure again under known conditions.

## Source justification per section

| Section | Source ID | Locator | Supports |
|---|---|---|---|
| Possible parallel paths | `master_02` | H6 | parallel_paths |
| ESR | `master_02` | H6 | masking; high_esr_confirmation |
| Capacitance | `master_02` | H6 | parallel_capacitance |
| Capacitor banks | `master_02` | H66 | capacitor_banks |
| Confirmation | `master_02` | H6/H7 | confirm_one_leg; confirm_ex_situ |

### Source register

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Internal technical project reference; the locator above identifies the relevant chapter or project rule.
