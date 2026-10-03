# Measure ESR with an ESR meter

An ESR meter is especially useful for aluminum electrolytic capacitors, low-ESR types and an initial in-circuit screening.

## Before measuring

- Make the circuit voltage-free.
- Discharge the capacitor in a controlled way and verify the voltage again.
- Record the measurement method: `EX_SITU`, `ONE_LEG` or `IN_CIRCUIT`.
- Check the test frequency of the instrument.
- Check the test voltage or test signal of the instrument.
- For very low ESR, use suitable probes; cable and contact resistance can dominate the measurement.

## During the measurement

Pay attention to:

- measurement frequency;
- test voltage;
- instrument resolution;
- contact resistance;
- parallel paths in the circuit.

An instrument resolution of `0.01 Ω`, for example, cannot reliably distinguish values of only a few milliohms from one another.

## In-circuit interpretation

A clearly excessive ESR in-circuit is meaningful and should be confirmed by disconnecting at least one terminal.

A low ESR is **not automatically proof that the capacitor is good**. A parallel good capacitor, low resistance, short circuit or other rail impedance can reduce the measured ESR.

## Comparing with a reference

Compare the measured value only with an appropriate reference. For example, do not directly compare `ESR @ 1 kHz` with `ESR max @ 100 kHz` without a valid frequency characteristic.

## Source justification per section

| Section | Source ID | Locator | Supports |
|---|---|---|---|
| Before measuring | `master_02` | H5/H58 | frequency; test_signal; probes |
| During the measurement | `master_02` | H58–61 | resolution; contact_resistance |
| In-circuit interpretation | `master_02` | H6 | parallel_paths; masking |
| Comparing with a reference | `master_02` | H9/H61 | frequency_context; no_hidden_conversion |

### Source register

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Internal technical project reference; the locator above identifies the relevant chapter or project rule.
