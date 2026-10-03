# Safely discharge a capacitor before measurement

> Internal measurement instruction. Not a formal safety approval.

A capacitor can remain charged after equipment has been switched off. The stored energy is given by:

`E = 1/2 × C × V²`

where `E` is expressed in joules, `C` in farads and `V` in volts.

## Fixed sequence before ESR, LCR or resistance measurement

1. Switch off the equipment.
2. Disconnect all power sources.
3. Wait if the equipment has internal discharge circuits.
4. Measure the remaining voltage with a suitable instrument.
5. Discharge in a controlled way through a suitable resistor.
6. Check the voltage again.
7. Only then start the ESR, LCR or resistance measurement.

## Do not

- Do not short a charged electrolytic capacitor directly with tools.
- Do not touch an unknown high-voltage capacitor.
- Do not perform a leakage test without current limiting.
- Do not reverse the polarity of polarized capacitors.
- Do not replace safety capacitors with ordinary capacitors.

## Additional attention

Large capacitors can rebuild voltage after discharge. Therefore, check again before touching the terminals or changing the measurement setup.

## Source justification per section

| Section | Source ID | Locator | Supports |
|---|---|---|---|
| Fixed sequence before ESR, LCR or resistance measurement | `master_02` | H1 | power_off; discharge_resistor; recheck_voltage |
| Do not | `master_02` | H1 | safe_discharge; polarity; safety_capacitors |
| Additional attention | `master_02` | H1 | rebound_voltage |

### Source register

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Internal technical project reference; the locator above identifies the relevant chapter or project rule.
