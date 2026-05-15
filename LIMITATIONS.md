# Limitations

## Surrogate limitations

- The model is nondimensional and reduced.
- It is not calibrated to a spacecraft, payload, orbit, material stack, or thermal-vacuum experiment.
- Radiative heat rejection is represented by a simplified fourth-power proxy.
- The model does not include detailed view factors, orbital beta-angle histories, multi-node geometry, spacecraft attitude dynamics, or material-stack validation.
- Storage is represented by a scalar margin rather than a phase-change material model or detailed heat-capacity network.
- Power margin is represented as a scalar reserve.

## Control limitations

- The delay predictor is intentionally simple and should not be confused with a flight-ready estimator.
- CVaR is used as a diagnostic tail-risk metric, not as a formal stochastic optimality guarantee.
- Harsh combined stress remains unsolved and is explicitly excluded from the mission-feasible claim.
- The high-resource requirement is part of the claim boundary.

## Repository limitations

- Large phase-output archives are not included in the GitHub body.
- Virtual environments and compiled dependencies are excluded.
- This archive is a paper companion, not a certified one-command validation package.
