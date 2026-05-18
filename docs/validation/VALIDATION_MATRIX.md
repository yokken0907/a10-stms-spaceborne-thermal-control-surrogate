# Validation Matrix: A10-STMS

| Stage | Question | Evidence currently present | Next action | Claim boundary |
|---|---|---|---|---|
| V0 Repository consistency | Are README, limitations, and claim boundary aligned? | README, README_ja, CLAIM_BOUNDARY, LIMITATIONS | Cross-check all new documents | Repository-level only |
| V1 Table reproduction | Are reported table results reproducible? | results_summary CSV/JSON, selected source materials | Rerun selected scripts and record seeds | Reduced surrogate only |
| V2 Manageable-stress expansion | Does manageable separation survive wider stress profiles? | Phase 2E manageable tables | Expand nondimensional stress families | No spacecraft environment claim |
| V3 Delay robustness | Does classification survive observation imperfections? | Delay 0.5 and 1.0 summaries | Add noise, latency, dropout, drift | No sensor-system claim |
| V4 Actuator authority | Where does actuator authority become limiting? | Actuator 0.8 and 0.6 summaries | Sweep authority, saturation, rate limits | No hardware actuator claim |
| V5 Model-form audit | Is result model-form dependent? | Current selected model family | Test alternative reduced model forms | No universal controller claim |
| V6 Benchmark bridge | Can findings be compared to higher-fidelity thermal models? | Not yet established | Public multi-node thermal benchmark comparison | No thermal-vacuum validation |
| V7 Hardware discussion gate | What would be required before hardware discussion? | Claim boundary and limitations | Expert-led thermal-vacuum / instrumentation planning | No flight-ready claim |
| V8 Expert review | Can specialists review without misreading the claim? | New reviewer files and claim boundary | Package for thermal-control experts | No deployment claim |

## Interpretation

The validation path should strengthen reproducibility, robustness, and benchmark comparison while preserving the explicit boundary against spacecraft-ready cooling, thermal-vacuum validation, flight control, certified safety, and harsh-combined-stress solution claims.
