# Next Validation Plan: A10-STMS

## 0. Purpose of this document

This document defines the next validation steps for A10-STMS.

This is **not** a spacecraft deployment plan, not a thermal-vacuum qualification plan, not a flight-controller implementation plan, and not a certified cooling-system development plan. It is a staged validation roadmap for a nondimensional reduced-surrogate thermal-control audit.

## V0. Repository-level verification

Goal: confirm that the public archive is internally consistent.

Tasks:

- check `CLAIM_BOUNDARY.md` against README wording,
- check `LIMITATIONS.md` against manuscript conclusions,
- verify `results_summary/summary.json` matches the CSV summaries,
- verify selected figures and source scripts are traceable through `FILE_MANIFEST.csv`,
- confirm that no text implies spacecraft-ready cooling, thermal-vacuum validation, flight control, certified safety, or solution of harsh combined stress.

Exit criterion:

- repository can be reviewed as a bounded paper companion archive.

## V1. Reduced-surrogate reproduction

Goal: independently reproduce the reported table-level results inside the nondimensional surrogate.

Tasks:

- rerun selected source scripts where feasible,
- regenerate compact table outputs,
- confirm Phase 2E manageable metrics,
- confirm out-of-sample, frontier, and harsh-family results,
- record random seeds, solver settings, and parameter grids.

Exit criterion:

- table-level results are reproducible or differences are explained.

## V2. Manageable-stress expansion

Goal: test whether the manageable-stress separation remains stable under a wider but still nondimensional envelope.

Tasks:

- expand heat-load profiles,
- expand radiative-environment proxies,
- expand storage-margin variation,
- expand power-margin variation,
- add time-varying mission-throughput demand,
- test stress-onset timing sensitivity.

Exit criterion:

- the manageable regime remains meaningful without overfitting to the original stress families.

## V3. Delay and observation robustness

Goal: check whether conclusions survive imperfect observation.

Tasks:

- sensor noise tests,
- latency tests,
- dropout tests,
- bias and calibration-drift tests,
- partial-observation tests,
- false-positive and false-negative audits,
- threshold sensitivity analysis.

Exit criterion:

- diagnostic conclusions are not dependent on unrealistically clean observation channels.

## V4. Actuator-authority and degradation audit

Goal: clarify the boundary where actuator authority becomes the dominant limitation.

Tasks:

- sweep actuator authority below and above 0.6 / 0.8,
- test saturation and rate limits,
- separate radiator-like, pump-like, storage-like, and routing-like authority limits,
- report failure and throughput tradeoff,
- identify conditions where A10-v4-safe is no longer mission-feasible even in the surrogate.

Exit criterion:

- actuator-limited regimes are explicitly marked and not overclaimed.

## V5. Model-form audit

Goal: test whether the result is an artifact of the selected reduced model form.

Tasks:

- alter thermal accumulation law,
- alter radiative rejection proxy,
- add alternative storage-margin models,
- add alternative power-margin models,
- add alternative gradient-risk definitions,
- include null and intentionally weakened controllers,
- include overfitting checks.

Exit criterion:

- A10-STMS claims are either robust within a defined reduced-surrogate class or explicitly limited to the original model.

## V6. Higher-fidelity benchmark bridge

Goal: create a safe bridge to higher-fidelity public benchmark models without claiming spacecraft validation.

Tasks:

- identify non-proprietary thermal-control benchmark models,
- compare with a multi-node thermal network,
- introduce simple orbital environment forcing,
- include view-factor-like approximations,
- test power-system coupling,
- document all mismatches and non-correspondences.

Exit criterion:

- A10-STMS can be compared with a higher-fidelity model as a research diagnostic, not as spacecraft thermal validation.

## V7. Thermal-vacuum and hardware discussion gate

Goal: define what would be required before any hardware-relevant discussion.

Tasks:

- consult spacecraft thermal-control experts,
- identify required thermal-vacuum test conditions,
- identify instrumentation requirements,
- define safe non-flight laboratory validation steps,
- preserve the boundary against flight readiness and certified safety.

Exit criterion:

- hardware-relevant discussion remains expert-led and does not emerge from the reduced surrogate alone.

## V8. Expert review package

Goal: prepare a review package for thermal-control, spacecraft-systems, control, and safety experts.

Package contents:

- `REVIEWER_START_HERE.md`,
- `CLAIM_BOUNDARY.md`,
- `LIMITATIONS.md`,
- `FIELD_VALUE_en.md`,
- `NEXT_VALIDATION_PLAN.md`,
- result-summary tables,
- manuscript PDF,
- selected source-material inventory,
- explicit list of forbidden interpretations.

Exit criterion:

- experts can evaluate the framework without mistaking it for a spacecraft cooling-system proposal.

## Summary

A10-STMS should proceed through staged validation as a reduced-surrogate thermal-control audit. The next validation work should strengthen reproducibility, robustness, model-form sensitivity, and benchmark comparison while preserving the explicit boundary against spacecraft-ready cooling, thermal-vacuum validation, flight control, certified safety, and harsh-combined-stress solution claims.
