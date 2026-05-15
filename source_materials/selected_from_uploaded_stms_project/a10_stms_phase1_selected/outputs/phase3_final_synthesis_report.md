# A10-STMS Phase 3 Final Synthesis Report

## 1. Locked status

**Final numerical status:** `PASS-PHASE2E-DELAY-DEGRADE-ROBUSTNESS`

This closes the reduced-surrogate numerical validation sequence for Paper M.

## 2. Confirmed resource regime

- Radiator scale: `24`
- Transport scale: `12`
- Storage scale: `1` to `4.0` was tested; Phase 2/2E uses `4.0`.
- Best Phase 1R2C mode: `a10_hybrid_v2`
- Phase 1R2C manageable failure: `0.0714286`
- Phase 1R2C manageable CVaR95: `0.00446476`
- Phase 1R2C manageable unsafe fraction: `0.0093192`
- Phase 1R2C manageable throughput: `0.949388`

Interpretation: A mission-feasible region appears only after high radiator and thermal-transport resources are introduced. This should be stated as a high-resource regime, not as a universal cooling result.

## 3. Final controller interpretation

The final preferred controller family is `A10-v4`, with `a10_v4_safe` as the conservative primary setting and `a10_v4_balanced` as a throughput-preserving alternative.

`a10_v4_safe` should be treated as the paper's primary robust architecture because it passes baseline, sensor-delay, actuator-degradation, and out-of-sample checks with the cleanest safety margin.

## 4. Manageable-stress performance by condition

| condition        | mode            |   n |   failure_rate |    CVaR95_V |   mean_unsafe_fraction |   mean_Y_final |   max_Tc_p95 |   fail_Tc_rate |   fail_Tp_rate |   fail_Y_rate |
|:-----------------|:----------------|----:|---------------:|------------:|-----------------------:|---------------:|-------------:|---------------:|---------------:|--------------:|
| baseline         | a10_v4_safe     | 224 |     0.03125    | 4.69764e-05 |            0.0030506   |       0.964707 |     0.991673 |     0.03125    |     0          |      0        |
| baseline         | a10_v4_balanced | 224 |     0.0446429  | 0.000365445 |            0.0046689   |       0.964803 |     0.991487 |     0.0446429  |     0.00446429 |      0        |
| baseline         | a10_robust_v3   | 224 |     0.0535714  | 0.00249849  |            0.00532366  |       0.955872 |     1.00196  |     0.0535714  |     0          |      0        |
| baseline         | pump_radiator   | 224 |     0.325893   | 0.943606    |            0.0998921   |       1        |     1.3643   |     0.325893   |     0.308036   |      0        |
| sensor_delay_0p5 | a10_v4_safe     | 224 |     0.0223214  | 1.14304e-06 |            0.00107887  |       0.92899  |     0.977225 |     0.0223214  |     0          |      0        |
| sensor_delay_0p5 | a10_v4_balanced | 224 |     0.0446429  | 0.000222842 |            0.0052381   |       0.933709 |     0.987611 |     0.0446429  |     0.00446429 |      0        |
| sensor_delay_0p5 | a10_robust_v3   | 224 |     0.0401786  | 0.000179004 |            0.00428199  |       0.928619 |     0.98424  |     0.0401786  |     0.00446429 |      0        |
| sensor_delay_0p5 | pump_radiator   | 224 |     0.727679   | 1.21172     |            0.109479    |       1        |     1.41325  |     0.727679   |     0.308036   |      0        |
| sensor_delay_1p0 | a10_v4_safe     | 224 |     0.0223214  | 1.61166e-05 |            0.00165551  |       0.887552 |     0.949333 |     0.0223214  |     0          |      0        |
| sensor_delay_1p0 | a10_v4_balanced | 224 |     0.00892857 | 4.49558e-06 |            0.000911458 |       0.898742 |     0.951084 |     0.00892857 |     0          |      0        |
| sensor_delay_1p0 | a10_robust_v3   | 224 |     0.0133929  | 8.43428e-06 |            0.000985863 |       0.896441 |     0.968665 |     0.0133929  |     0          |      0        |
| sensor_delay_1p0 | pump_radiator   | 224 |     1          | 1.13645     |            0.151283    |       1        |     1.40856  |     1          |     0.544643   |      0        |
| actuator_0p8     | a10_v4_safe     | 224 |     0.0848214  | 0.00899916  |            0.0101823   |       0.895611 |     1.02862  |     0.0848214  |     0          |      0        |
| actuator_0p8     | a10_v4_balanced | 224 |     0.102679   | 0.0114132   |            0.0125521   |       0.915506 |     1.03116  |     0.102679   |     0          |      0        |
| actuator_0p8     | a10_robust_v3   | 224 |     0.15625    | 0.0371748   |            0.0210156   |       0.929135 |     1.06959  |     0.15625    |     0.0178571  |      0        |
| actuator_0p8     | pump_radiator   | 224 |     0.410714   | 1.57937     |            0.197187    |       1        |     1.51867  |     0.410714   |     0.357143   |      0        |
| actuator_0p6     | a10_v4_safe     | 224 |     0.21875    | 0.0605075   |            0.0251935   |       0.820892 |     1.09479  |     0.1875     |     0.0133929  |      0.107143 |
| actuator_0p6     | a10_v4_balanced | 224 |     0.241071   | 0.0803635   |            0.0336049   |       0.859826 |     1.127    |     0.241071   |     0.0178571  |      0        |
| actuator_0p6     | a10_robust_v3   | 224 |     0.258929   | 0.118565    |            0.0374926   |       0.900848 |     1.15013  |     0.258929   |     0.0446429  |      0        |
| actuator_0p6     | pump_radiator   | 224 |     0.691964   | 2.43614     |            0.496722    |       1        |     1.65454  |     0.691964   |     0.433036   |      0        |

## 5. Best A10 variant by condition

| condition        | mode            |   n |   failure_rate |    CVaR95_V |   mean_unsafe_fraction |   mean_Y_final |   max_Tc_p95 |   fail_Tc_rate |   fail_Tp_rate |   fail_Y_rate |
|:-----------------|:----------------|----:|---------------:|------------:|-----------------------:|---------------:|-------------:|---------------:|---------------:|--------------:|
| baseline         | a10_v4_safe     | 224 |     0.03125    | 4.69764e-05 |            0.0030506   |       0.964707 |     0.991673 |     0.03125    |      0         |      0        |
| sensor_delay_0p5 | a10_v4_safe     | 224 |     0.0223214  | 1.14304e-06 |            0.00107887  |       0.92899  |     0.977225 |     0.0223214  |      0         |      0        |
| sensor_delay_1p0 | a10_v4_balanced | 224 |     0.00892857 | 4.49558e-06 |            0.000911458 |       0.898742 |     0.951084 |     0.00892857 |      0         |      0        |
| actuator_0p8     | a10_v4_safe     | 224 |     0.0848214  | 0.00899916  |            0.0101823   |       0.895611 |     1.02862  |     0.0848214  |      0         |      0        |
| actuator_0p6     | a10_v4_safe     | 224 |     0.21875    | 0.0605075   |            0.0251935   |       0.820892 |     1.09479  |     0.1875     |      0.0133929 |      0.107143 |

## 6. Out-of-sample baseline comparison

| condition   | mode            |   n |   failure_rate |   CVaR95_V |   mean_unsafe_fraction |   mean_Y_final |   max_Tc_p95 |   fail_Tc_rate |   fail_Tp_rate |   fail_Y_rate |
|:------------|:----------------|----:|---------------:|-----------:|-----------------------:|---------------:|-------------:|---------------:|---------------:|--------------:|
| baseline    | a10_v4_safe     | 160 |        0.06875 | 0.00140352 |             0.00666667 |       0.94363  |      1.01098 |        0.06875 |           0    |             0 |
| baseline    | a10_v4_balanced | 160 |        0.10625 | 0.00382573 |             0.0104115  |       0.940794 |      1.01934 |        0.10625 |           0    |             0 |
| baseline    | a10_robust_v3   | 160 |        0.10625 | 0.0054705  |             0.010901   |       0.931023 |      1.02067 |        0.10625 |           0    |             0 |
| baseline    | pump_radiator   | 160 |        0.99375 | 1.22333    |             0.396042   |       1        |      1.41117 |        0.99375 |           0.95 |             0 |

## 7. Frontier and harsh interpretation

### Frontier baseline

| condition   | mode            |   n |   failure_rate |   CVaR95_V |   mean_unsafe_fraction |   mean_Y_final |   max_Tc_p95 |   fail_Tc_rate |   fail_Tp_rate |   fail_Y_rate |
|:------------|:----------------|----:|---------------:|-----------:|-----------------------:|---------------:|-------------:|---------------:|---------------:|--------------:|
| baseline    | a10_robust_v3   |  32 |        0.25    | 0.00425592 |              0.0294271 |       0.92098  |      1.03534 |        0.25    |              0 |             0 |
| baseline    | a10_v4_balanced |  32 |        0.25    | 0.00882743 |              0.0332812 |       0.929895 |      1.05389 |        0.25    |              0 |             0 |
| baseline    | a10_v4_safe     |  32 |        0.34375 | 0.00309814 |              0.0346094 |       0.931709 |      1.03486 |        0.34375 |              0 |             0 |
| baseline    | pump_radiator   |  32 |        1       | 1.38997    |              0.552839  |       1        |      1.45624 |        1       |              1 |             0 |

### Harsh baseline

| condition   | mode            |   n |   failure_rate |   CVaR95_V |   mean_unsafe_fraction |   mean_Y_final |   max_Tc_p95 |   fail_Tc_rate |   fail_Tp_rate |   fail_Y_rate |
|:------------|:----------------|----:|---------------:|-----------:|-----------------------:|---------------:|-------------:|---------------:|---------------:|--------------:|
| baseline    | a10_v4_safe     |  32 |        0.96875 |   0.189089 |               0.164453 |       0.875229 |      1.20923 |        0.96875 |        0.875   |             0 |
| baseline    | a10_v4_balanced |  32 |        1       |   0.207969 |               0.186484 |       0.873311 |      1.21641 |        1       |        0.90625 |             0 |
| baseline    | a10_robust_v3   |  32 |        1       |   0.274029 |               0.18612  |       0.858191 |      1.22906 |        1       |        0.90625 |             0 |
| baseline    | pump_radiator   |  32 |        1       |   4.41355  |               0.905052 |       1        |      1.69657 |        1       |        1       |             0 |

Interpretation: frontier conditions show strong damage-limiting behavior, but harsh combined stress should remain outside the mission-feasible claim. The correct claim is not universal survival, but regime classification.

## 8. Final defensible claim

A10-STMS is a reduced, nondimensional, mission-variable-preserving thermal-control surrogate for spaceborne industrial systems. In the tested high-resource regime, the A10-v4 separated-barrier controller preserves thermal safety and mission throughput across manageable stress families, delayed observations, moderate actuator degradation, and out-of-sample stress windows more effectively than a Pump+Radiator baseline.

## 9. Claims that must not be made

- Do not claim spacecraft hardware readiness.
- Do not claim thermal-vacuum validation.
- Do not claim superiority over all existing spacecraft thermal-control architectures.
- Do not claim operation beyond radiative thermal limits.
- Do not claim harsh combined stress is solved.

## 10. Recommended manuscript title

**A10-STMS: Mission-Variable-Preserving Hybrid Thermal Control for Spaceborne Industrial Systems under Radiative, Storage, Power, Delay, and Actuator Constraints**

## 11. Recommended abstract skeleton

This paper introduces A10-STMS, a mission-variable-preserving hybrid thermal-control framework for spaceborne industrial systems under radiative, storage, power, delay, and actuator constraints. The objective is not to propose a new heat-transfer mechanism or spacecraft hardware design, but to test whether separated-barrier hybrid control can preserve thermal safety and mission throughput in a reduced nondimensional surrogate. The model includes core, plate, radiator, storage, power-margin, thermal-gradient, and mission-throughput states. Initial Phase 1 tests showed damage-limiting behavior but not mission feasibility under insufficient thermal resources. Resource-frontier recalibration identified a high-resource regime in which A10-Hybrid-v2 achieved mission-feasible separation from passive and Pump+Radiator baselines. Subsequent ablation and out-of-sample tests showed that valve routing, storage buffering, and load shaping all contribute nontrivially. A delay/degradation redesign produced an A10-v4 controller that preserved manageable-stress feasibility under delayed sensing, moderate actuator degradation, and out-of-sample stress windows. Harsh combined stress remains unresolved and is interpreted as a resource or architecture-limited regime. The results support A10-STMS as a closed intermediate surrogate and feasibility-diagnostic control framework, not as a flight-ready thermal-control system.

## 12. Output files

- `outputs/phase3_best_manageable_by_condition.csv`
- `outputs/phase3_primary_v4safe_metrics.csv`
- `figs/phase3_primary_v4safe_failure_by_condition.png`
- `figs/phase3_oos_failure_comparison.png`