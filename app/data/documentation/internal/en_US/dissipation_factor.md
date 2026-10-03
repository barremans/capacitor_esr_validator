# Interpret D / tanδ

`D` or `tanδ` is the dissipation factor of the capacitor. A higher value means more loss.

For an appropriate series model, the following approximation applies:

`ESR ≈ tanδ / (2πfC)`

Use this relationship only when measurement model and frequency correspond.

## Checkpoints

For a D/tanδ measurement, at least these conditions must be correct:

- test frequency;
- temperature;
- series/parallel equivalent model;
- capacitance and units.

## What D does not automatically indicate

A D value is not an independent safety approval and does not replace relevant leakage, insulation or voltage tests.

## When comparing with a datasheet

Use the specified:

- frequency;
- temperature;
- model/test condition;
- maximum or typical nature of the reference value.

## Source justification per section

| Section | Source ID | Locator | Supports |
|---|---|---|---|
| Interpret D / tanδ | `master_02` | H3.7/H36 | tan_delta; ESR_relation |
| Checkpoints | `master_02` | H36 | frequency; temperature; model |
| When comparing with a datasheet | `master_02` | H36 | datasheet_conditions |

### Source register

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Internal technical project reference; the locator above identifies the relevant chapter or project rule.
