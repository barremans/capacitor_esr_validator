# Measurement methods: EX_SITU, ONE_LEG and IN_CIRCUIT

The physical measurement setup strongly determines how much confidence can be placed in capacitance and ESR measurements.

## EX_SITU — fully removed

The capacitor is fully isolated from the circuit.

Advantages:

- parallel paths are removed;
- capacitance, ESR and D can be attributed more reliably to one component;
- this is generally the best setup for a final assessment.

## ONE_LEG — one terminal disconnected

One terminal of the capacitor has been disconnected.

This is a useful practical intermediate step:

- many parallel paths are interrupted;
- less soldering than complete removal;
- more reliable than fully in-circuit;
- still context-dependent.

## IN_CIRCUIT — fully connected in the circuit

Advantages:

- fast;
- little soldering work;
- useful as an initial screening method.

Limitations:

- parallel capacitors, resistors, inductors, transformer windings and semiconductors can affect the measurement;
- a low ESR can be masked by parallel paths;
- an excessively high measured capacitance can be a parallel-path effect.

## Practical choice

Use in-circuit measurement as screening when appropriate. If ESR is clearly too high or the measurement is doubtful, disconnect at least one terminal and measure again. For a final assessment, preferably use an isolated component.

## Source justification per section

| Section | Source ID | Locator | Supports |
|---|---|---|---|
| EX_SITU | `master_02` | H6/H7 | isolated_component; reliability |
| ONE_LEG | `master_02` | H6/H7 | parallel_paths_reduced |
| IN_CIRCUIT | `master_02` | H6 | screening; parallel_paths |
| Practical choice | `master_02` | H6/H7 | confirm_one_leg; confirm_ex_situ |

### Source register

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Internal technical project reference; the locator above identifies the relevant chapter or project rule.
