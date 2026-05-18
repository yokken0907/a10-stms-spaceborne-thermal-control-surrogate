# Claim-to-Evidence Map: A10-STMS

This document maps allowed claims to evidence currently present in the repository. It also identifies claims that are not supported and must not be made.

## 1. Allowed claim: A10-STMS is a nondimensional reduced-surrogate thermal-control audit

Evidence:

- `README.md`
- `README_ja.md`
- `CLAIM_BOUNDARY.md`
- `LIMITATIONS.md`
- manuscript PDF
- `results_summary/summary.json`

Boundary:

- does not imply spacecraft-ready cooling,
- does not imply thermal-vacuum validation,
- does not imply flight-controller readiness,
- does not imply certified aerospace safety.

## 2. Allowed claim: the final locked status is PASS-PHASE2E-DELAY-DEGRADE-ROBUSTNESS

Evidence:

- `results_summary/summary.json`
- `results_summary/table3_validation_sequence.csv`
- manuscript PDF

Boundary:

- this is a surrogate-validation status,
- not a hardware qualification status,
- not a thermal-vacuum test status.

## 3. Allowed claim: manageable Phase 2E conditions show A10-v4 separation from Pump+Radiator baseline

Evidence:

- `results_summary/table5_phase2E_manageable_metrics.csv`
- `results_summary/summary.json`

Selected reported values:

- Baseline / A10-v4-safe: `failure = 0.03125`, `CVaR0.95 = 4.6976e-05`, `unsafe_frac = 0.003051`, `throughput = 0.964707`
- Baseline / Pump+Radiator: `failure = 0.325893`, `CVaR0.95 = 0.943606`, `unsafe_frac = 0.099892`
- Delay 1.0 / A10-v4-balanced: `failure = 0.008929`
- Delay 1.0 / Pump+Radiator: `failure = 1.0`

Boundary:

- only inside the tested nondimensional reduced surrogate,
- not universal superiority over existing spacecraft architectures,
- not real thermal-control hardware performance.

## 4. Allowed claim: actuator authority remains an important boundary

Evidence:

- `results_summary/table5_phase2E_manageable_metrics.csv`

Selected reported values:

- Actuator 0.8 / A10-v4-safe: `failure = 0.084821`
- Actuator 0.6 / A10-v4-safe: `failure = 0.21875`

Boundary:

- do not claim actuator degradation is solved,
- do not claim hardware robustness,
- mark this as a model-bounded limitation.

## 5. Allowed claim: out-of-sample family remains favorable but nonzero failure persists

Evidence:

- `results_summary/table6_oos_frontier_harsh_metrics.csv`

Selected reported values:

- Out-of-sample / A10-v4-safe: `failure = 0.06875`
- Out-of-sample / Pump+Radiator: `failure = 0.99375`

Boundary:

- out-of-sample here means the tested surrogate family,
- not external spacecraft validation,
- not real environmental validation.

## 6. Allowed claim: harsh combined stress remains unresolved

Evidence:

- `results_summary/table6_oos_frontier_harsh_metrics.csv`
- `CLAIM_BOUNDARY.md`
- `LIMITATIONS.md`

Selected reported values:

- Harsh / A10-v4-safe: `failure = 0.96875`
- Harsh / Pump+Radiator: `failure = 1.0`

Boundary:

- harsh combined stress is excluded from mission-feasible claims,
- do not present the method as solving all stress regimes,
- preserve the unresolved result.

## 7. Unsupported claims

The current repository does not support the following claims:

- spacecraft-ready cooling technology,
- thermal-vacuum validation,
- flight-controller readiness,
- certified aerospace safety system,
- spacecraft hardware design,
- radiator / heat-pipe / pumped-loop / PCM implementation,
- new heat-transfer mechanism,
- formal control-barrier-function proof,
- universal superiority over existing thermal-control architectures,
- solution of harsh combined stress.

## 8. Safe evidence wording

Use:

> The reported results support a feasibility-diagnostic interpretation within the tested nondimensional reduced surrogate.

Avoid:

> The controller is safe for spacecraft.

Use:

> Harsh combined stress remains unresolved and is excluded from mission-feasible claims.

Avoid:

> The method solves harsh thermal-control stress.
