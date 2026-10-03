# Choose measurement frequency and test level

ESR, impedance and some capacitance measurements depend on the measurement conditions.

## Measurement frequency

Always record the frequency.

An ESR value must not be compared directly with a limit at another frequency without a substantiated frequency characteristic.

Example:

`ESR @ 1 kHz` is not automatically comparable with `ESR max @ 100 kHz`.

Preferably use the same frequency as the datasheet or reference source.

## AC test level / test voltage

For characterization, follow the test conditions from the datasheet and the capabilities of the instrument.

For certain capacitor technologies, the measured capacitance can depend on the AC test level. A measurement result without an appropriate test condition therefore does not necessarily represent the datasheet value.

## No hidden corrections

When measurement and reference frequency differ:

- record the difference;
- do not perform automatic conversion without a validated model or manufacturer curve;
- treat the comparison as context-dependent.

## Practical recording

Record at least:

- instrument;
- measurement frequency;
- test level/test voltage;
- measurement method;
- temperature when relevant.

## Source justification per section

| Section | Source ID | Locator | Supports |
|---|---|---|---|
| Measurement frequency | `master_02` | H9/H61 | frequency_context; no_hidden_conversion |
| AC test level / test voltage | `master_02` | H58/H63 | test_level; datasheet_conditions |
| No hidden corrections | `master_02` | H9 | no_hidden_conversion |
| Practical recording | `master_02` | H58/H63 | traceable_conditions |

### Source register

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Internal technical project reference; the locator above identifies the relevant chapter or project rule.
