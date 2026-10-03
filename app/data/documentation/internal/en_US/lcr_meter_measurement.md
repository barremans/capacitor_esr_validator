# Measure ESR and capacitance with an LCR meter

An LCR meter can measure, among other things, `C`, `ESR`, `D`, `Q`, `tanδ` and impedance. The result is useful only when the measurement model and measurement conditions suit the component and the reference.

## Preparation

1. Make the circuit voltage-free and discharge the capacitor.
2. Choose the physical measurement method: preferably out of circuit for a final assessment.
3. Perform open/short calibration according to the instrument.
4. Keep test leads short; use Kelvin/4-wire where low ESR requires it.
5. Record temperature and measurement frequency.

## Settings

Check:

- the correct measurement frequency;
- the AC test level/test voltage;
- the series or parallel model (`Cs/Rs` or `Cp/Rp`);
- the same measurement conditions as the datasheet when comparing with a manufacturer limit.

## Interpretation

An LCR measurement does not automatically test:

- leakage current;
- insulation resistance;
- breakdown voltage;
- behavior at nominal DC voltage.

A good ESR or capacitance value alone therefore does not prove that the capacitor is good or safe in every respect.

## In case of deviations

When C, ESR and D are not mutually plausible:

- check units;
- check frequency;
- check the series/parallel model;
- repeat calibration;
- measure out of circuit where possible.

## Source justification per section

| Section | Source ID | Locator | Supports |
|---|---|---|---|
| Preparation | `master_02` | H58/H63–65 | open_short_calibration; probes |
| Settings | `master_02` | H36/H63 | series_parallel_model; frequency; test_level |
| Interpretation | `master_02` | H5/H36 | measurement_scope; limitations |
| In case of deviations | `master_02` | H3.7/H63–65 | C_ESR_D_consistency; calibration |

### Source register

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Internal technical project reference; the locator above identifies the relevant chapter or project rule.
