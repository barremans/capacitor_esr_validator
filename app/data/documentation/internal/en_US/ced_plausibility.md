# C–ESR–D plausibility check

Capacitance `C`, ESR and dissipation factor `D` do not describe exactly the same property, but they can be used together to signal input or measurement problems.

For an appropriate series model:

`ESR ≈ D / (2πfC)`

where `D = tanδ`.

## Purpose of the check

The check is intended to ask:

> Are the entered C, ESR, D and frequency mutually plausible?

A strong deviation can indicate:

- confusion between `mΩ` and `Ω`;
- wrong capacitance unit;
- wrong measurement frequency;
- wrong series/parallel model;
- rounding;
- influence from the circuit;
- incorrect or unstable measurement.

## Procedure when values are inconsistent

1. Check capacitance and unit.
2. Check ESR and unit.
3. Check the actual measurement frequency used.
4. Check the LCR model.
5. Repeat open/short calibration where applicable.
6. Repeat the measurement using a more reliable physical setup.

## Important

Do not use this relationship as an automatic correction of a measured value. An inconsistency is a signal to verify the measurement.

## Source justification per section

| Section | Source ID | Locator | Supports |
|---|---|---|---|
| Purpose of the check | `master_02` | H3.7 | C_ESR_D_consistency |
| Procedure when values are inconsistent | `master_02` | H3.7/H63–65 | units; frequency; model; calibration |
| Important | `master_02` | project rule | no_auto_correction |

### Source register

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Internal technical project reference; the locator above identifies the relevant chapter or project rule.
