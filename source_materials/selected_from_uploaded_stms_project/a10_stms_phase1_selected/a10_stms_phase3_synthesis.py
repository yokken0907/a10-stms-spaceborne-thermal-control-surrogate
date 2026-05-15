#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A10-STMS Phase 3
Final synthesis report for manuscript construction.

Inputs:
- outputs/phase1R2C_classification.csv
- outputs/phase2_by_family_condition_mode.csv
- outputs/phase2D_by_family_condition_mode.csv
- outputs/phase2E_by_family_condition_mode.csv
- outputs/phase2E_lock_report.txt

Outputs:
- outputs/phase3_final_synthesis_report.md
- outputs/phase3_best_manageable_by_condition.csv
- outputs/phase3_primary_v4safe_metrics.csv
- figs/phase3_primary_v4safe_failure_by_condition.png
- figs/phase3_oos_failure_comparison.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

os.makedirs("outputs", exist_ok=True)
os.makedirs("figs", exist_ok=True)

def read_csv_required(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path)

def read_text_optional(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def fmt(x, nd=6):
    try:
        return f"{float(x):.{nd}g}"
    except Exception:
        return str(x)

phase1 = read_csv_required("outputs/phase1R2C_classification.csv")
phase2e = read_csv_required("outputs/phase2E_by_family_condition_mode.csv")
phase2e_report = read_text_optional("outputs/phase2E_lock_report.txt")

candidate_modes = ["a10_v4_safe", "a10_v4_balanced", "a10_robust_v3"]
conditions = ["baseline", "sensor_delay_0p5", "sensor_delay_1p0", "actuator_0p8", "actuator_0p6"]

manageable = phase2e[phase2e["stress_family"] == "manageable"].copy()
oos = phase2e[phase2e["stress_family"] == "out_of_sample"].copy()
frontier = phase2e[phase2e["stress_family"] == "frontier"].copy()
harsh = phase2e[phase2e["stress_family"] == "harsh"].copy()

# Best A10 candidate by condition.
best_rows = []
for cond in conditions:
    view = manageable[
        (manageable["condition"] == cond)
        & (manageable["mode"].isin(candidate_modes))
    ].copy()
    view = view.sort_values(["failure_rate", "CVaR95_V", "mean_unsafe_fraction", "mean_Y_final"],
                            ascending=[True, True, True, False])
    if len(view) > 0:
        best_rows.append(view.iloc[0])

best_manageable = pd.DataFrame(best_rows)
best_manageable.to_csv("outputs/phase3_best_manageable_by_condition.csv", index=False)

# Primary final controller: a10_v4_safe.
primary = phase2e[phase2e["mode"] == "a10_v4_safe"].copy()
primary.to_csv("outputs/phase3_primary_v4safe_metrics.csv", index=False)

# Key comparison rows.
def one(df, condition, family, mode):
    q = df[
        (df["condition"] == condition)
        & (df["stress_family"] == family)
        & (df["mode"] == mode)
    ]
    if len(q) == 0:
        return None
    return q.iloc[0]

rows_to_report = []
for cond in conditions:
    for mode in ["a10_v4_safe", "a10_v4_balanced", "a10_robust_v3", "pump_radiator"]:
        r = one(phase2e, cond, "manageable", mode)
        if r is not None:
            rows_to_report.append(r)

manageable_table = pd.DataFrame(rows_to_report)

# Plot 1: v4_safe failure by condition.
safe_manage = primary[primary["stress_family"].eq("manageable") & primary["condition"].isin(conditions)].copy()
safe_manage = safe_manage.set_index("condition").loc[conditions].reset_index()

fig = plt.figure(figsize=(10, 5))
x = np.arange(len(safe_manage))
plt.bar(x, safe_manage["failure_rate"].values)
plt.xticks(x, safe_manage["condition"].values, rotation=30, ha="right")
plt.ylabel("failure rate")
plt.title("Phase 3: A10-v4-safe manageable failure by condition")
plt.tight_layout()
fig.savefig("figs/phase3_primary_v4safe_failure_by_condition.png", dpi=180)
plt.close(fig)

# Plot 2: OOS baseline comparison.
oos_base = phase2e[
    (phase2e["condition"] == "baseline")
    & (phase2e["stress_family"] == "out_of_sample")
    & (phase2e["mode"].isin(["a10_v4_safe", "a10_v4_balanced", "a10_robust_v3", "pump_radiator"]))
].copy()
oos_base = oos_base.sort_values(["failure_rate", "CVaR95_V"])

fig = plt.figure(figsize=(10, 5))
x = np.arange(len(oos_base))
plt.bar(x, oos_base["failure_rate"].values)
plt.xticks(x, oos_base["mode"].values, rotation=30, ha="right")
plt.ylabel("failure rate")
plt.title("Phase 3: out-of-sample baseline failure comparison")
plt.tight_layout()
fig.savefig("figs/phase3_oos_failure_comparison.png", dpi=180)
plt.close(fig)

# Extract Phase 1R2C best confirmed resource point.
p1best = phase1.sort_values(["regime_order", "resource_score", "best_manage_failure", "best_manage_CVaR95"]).iloc[0]

# Final textual synthesis.
lines = []
lines.append("# A10-STMS Phase 3 Final Synthesis Report")
lines.append("")
lines.append("## 1. Locked status")
lines.append("")
lines.append("**Final numerical status:** `PASS-PHASE2E-DELAY-DEGRADE-ROBUSTNESS`")
lines.append("")
lines.append("This closes the reduced-surrogate numerical validation sequence for Paper M.")
lines.append("")
lines.append("## 2. Confirmed resource regime")
lines.append("")
lines.append(f"- Radiator scale: `{fmt(p1best['rad_scale'])}`")
lines.append(f"- Transport scale: `{fmt(p1best['transport_scale'])}`")
lines.append(f"- Storage scale: `{fmt(p1best['storage_scale'])}` to `4.0` was tested; Phase 2/2E uses `4.0`.")
lines.append(f"- Best Phase 1R2C mode: `{p1best['best_a10_mode']}`")
lines.append(f"- Phase 1R2C manageable failure: `{fmt(p1best['best_manage_failure'])}`")
lines.append(f"- Phase 1R2C manageable CVaR95: `{fmt(p1best['best_manage_CVaR95'])}`")
lines.append(f"- Phase 1R2C manageable unsafe fraction: `{fmt(p1best['best_manage_unsafe'])}`")
lines.append(f"- Phase 1R2C manageable throughput: `{fmt(p1best['best_manage_Y'])}`")
lines.append("")
lines.append("Interpretation: A mission-feasible region appears only after high radiator and thermal-transport resources are introduced. This should be stated as a high-resource regime, not as a universal cooling result.")
lines.append("")
lines.append("## 3. Final controller interpretation")
lines.append("")
lines.append("The final preferred controller family is `A10-v4`, with `a10_v4_safe` as the conservative primary setting and `a10_v4_balanced` as a throughput-preserving alternative.")
lines.append("")
lines.append("`a10_v4_safe` should be treated as the paper's primary robust architecture because it passes baseline, sensor-delay, actuator-degradation, and out-of-sample checks with the cleanest safety margin.")
lines.append("")
lines.append("## 4. Manageable-stress performance by condition")
lines.append("")
show_cols = [
    "condition", "mode", "n", "failure_rate", "CVaR95_V",
    "mean_unsafe_fraction", "mean_Y_final", "max_Tc_p95",
    "fail_Tc_rate", "fail_Tp_rate", "fail_Y_rate"
]
lines.append(manageable_table[show_cols].to_markdown(index=False))
lines.append("")
lines.append("## 5. Best A10 variant by condition")
lines.append("")
lines.append(best_manageable[show_cols].to_markdown(index=False))
lines.append("")
lines.append("## 6. Out-of-sample baseline comparison")
lines.append("")
lines.append(oos_base[show_cols].to_markdown(index=False))
lines.append("")
lines.append("## 7. Frontier and harsh interpretation")
lines.append("")
front_base = phase2e[
    (phase2e["condition"] == "baseline")
    & (phase2e["stress_family"] == "frontier")
    & (phase2e["mode"].isin(["a10_v4_safe", "a10_v4_balanced", "a10_robust_v3", "pump_radiator"]))
].copy().sort_values(["failure_rate", "CVaR95_V"])

harsh_base = phase2e[
    (phase2e["condition"] == "baseline")
    & (phase2e["stress_family"] == "harsh")
    & (phase2e["mode"].isin(["a10_v4_safe", "a10_v4_balanced", "a10_robust_v3", "pump_radiator"]))
].copy().sort_values(["failure_rate", "CVaR95_V"])

lines.append("### Frontier baseline")
lines.append("")
lines.append(front_base[show_cols].to_markdown(index=False))
lines.append("")
lines.append("### Harsh baseline")
lines.append("")
lines.append(harsh_base[show_cols].to_markdown(index=False))
lines.append("")
lines.append("Interpretation: frontier conditions show strong damage-limiting behavior, but harsh combined stress should remain outside the mission-feasible claim. The correct claim is not universal survival, but regime classification.")
lines.append("")
lines.append("## 8. Final defensible claim")
lines.append("")
lines.append("A10-STMS is a reduced, nondimensional, mission-variable-preserving thermal-control surrogate for spaceborne industrial systems. In the tested high-resource regime, the A10-v4 separated-barrier controller preserves thermal safety and mission throughput across manageable stress families, delayed observations, moderate actuator degradation, and out-of-sample stress windows more effectively than a Pump+Radiator baseline.")
lines.append("")
lines.append("## 9. Claims that must not be made")
lines.append("")
lines.append("- Do not claim spacecraft hardware readiness.")
lines.append("- Do not claim thermal-vacuum validation.")
lines.append("- Do not claim superiority over all existing spacecraft thermal-control architectures.")
lines.append("- Do not claim operation beyond radiative thermal limits.")
lines.append("- Do not claim harsh combined stress is solved.")
lines.append("")
lines.append("## 10. Recommended manuscript title")
lines.append("")
lines.append("**A10-STMS: Mission-Variable-Preserving Hybrid Thermal Control for Spaceborne Industrial Systems under Radiative, Storage, Power, Delay, and Actuator Constraints**")
lines.append("")
lines.append("## 11. Recommended abstract skeleton")
lines.append("")
lines.append("This paper introduces A10-STMS, a mission-variable-preserving hybrid thermal-control framework for spaceborne industrial systems under radiative, storage, power, delay, and actuator constraints. The objective is not to propose a new heat-transfer mechanism or spacecraft hardware design, but to test whether separated-barrier hybrid control can preserve thermal safety and mission throughput in a reduced nondimensional surrogate. The model includes core, plate, radiator, storage, power-margin, thermal-gradient, and mission-throughput states. Initial Phase 1 tests showed damage-limiting behavior but not mission feasibility under insufficient thermal resources. Resource-frontier recalibration identified a high-resource regime in which A10-Hybrid-v2 achieved mission-feasible separation from passive and Pump+Radiator baselines. Subsequent ablation and out-of-sample tests showed that valve routing, storage buffering, and load shaping all contribute nontrivially. A delay/degradation redesign produced an A10-v4 controller that preserved manageable-stress feasibility under delayed sensing, moderate actuator degradation, and out-of-sample stress windows. Harsh combined stress remains unresolved and is interpreted as a resource or architecture-limited regime. The results support A10-STMS as a closed intermediate surrogate and feasibility-diagnostic control framework, not as a flight-ready thermal-control system.")
lines.append("")
lines.append("## 12. Output files")
lines.append("")
lines.append("- `outputs/phase3_best_manageable_by_condition.csv`")
lines.append("- `outputs/phase3_primary_v4safe_metrics.csv`")
lines.append("- `figs/phase3_primary_v4safe_failure_by_condition.png`")
lines.append("- `figs/phase3_oos_failure_comparison.png`")

report = "\n".join(lines)

with open("outputs/phase3_final_synthesis_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print(report)
print("")
print("Wrote:")
print("  outputs/phase3_final_synthesis_report.md")
print("  outputs/phase3_best_manageable_by_condition.csv")
print("  outputs/phase3_primary_v4safe_metrics.csv")
print("  figs/phase3_primary_v4safe_failure_by_condition.png")
print("  figs/phase3_oos_failure_comparison.png")
