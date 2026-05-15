#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A10-STMS Phase 1R2C
High-sample confirmation of the Phase 1R2 mission-feasible separation candidates.

Purpose:
- Phase 1R2 found provisional PASS-MISSION-FEASIBLE-SEPARATION at:
    rad_scale = 24.0
    transport_scale = 12.0
    storage_scale = 1.0, 2.0, 4.0
- This confirmation reruns those candidates with higher Monte Carlo count.
- It checks whether the result survives sampling noise.

Scope:
- Nondimensional reduced-surrogate audit only.
- Not spacecraft hardware design.
- Not thermal-vacuum validation.
"""

import argparse
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import a10_stms_phase1 as base
import a10_stms_phase1R2_extended_frontier as r2

# Importing r2 monkey-patches base.raw_control to include a10_hybrid_v2.
MODES = r2.MODES_R2
STRESSES = base.STRESSES

MANAGEABLE_STRESSES = r2.MANAGEABLE_STRESSES
FRONTIER_STRESSES = r2.FRONTIER_STRESSES
HARSH_STRESSES = r2.HARSH_STRESSES


def candidate_grid():
    return [
        (24.0, 12.0, 1.0),
        (24.0, 12.0, 2.0),
        (24.0, 12.0, 4.0),
    ]


def add_failure_reasons(df):
    p = base.Params()

    df = df.copy()
    df["fail_Tc"] = df["max_Tc"] > p.Tc_max
    df["fail_Tp"] = df["max_Tp"] > p.Tp_max
    df["fail_Tr"] = df["max_Tr"] > p.Tr_max
    df["fail_Es"] = df["min_Es"] < p.Es_min
    df["fail_Pm"] = df["min_Pm"] < p.Pm_min
    df["fail_G"] = df["max_G"] > p.G_max
    df["fail_Y"] = df["Y_final"] < p.Y_min

    return df


def reason_summary(df):
    reason_cols = [
        "fail_Tc",
        "fail_Tp",
        "fail_Tr",
        "fail_Es",
        "fail_Pm",
        "fail_G",
        "fail_Y",
    ]

    rows = []
    for (rad, trans, store, mode), g in df.groupby(
        ["rad_scale", "transport_scale", "storage_scale", "mode"]
    ):
        manageable = g[g["stress"].isin(MANAGEABLE_STRESSES)]
        frontier = g[g["stress"].isin(FRONTIER_STRESSES)]
        harsh = g[g["stress"].isin(HARSH_STRESSES)]

        row = {
            "rad_scale": rad,
            "transport_scale": trans,
            "storage_scale": store,
            "mode": mode,
            "manageable_n": len(manageable),
            "frontier_n": len(frontier),
            "harsh_n": len(harsh),
        }

        for col in reason_cols:
            row[f"manageable_{col}"] = float(manageable[col].mean())
            row[f"frontier_{col}"] = float(frontier[col].mean())
            row[f"harsh_{col}"] = float(harsh[col].mean())

        row["manageable_failure"] = float(manageable["failure"].mean())
        row["frontier_failure"] = float(frontier["failure"].mean())
        row["harsh_failure"] = float(harsh["failure"].mean())
        row["manageable_Y"] = float(manageable["Y_final"].mean())
        row["frontier_Y"] = float(frontier["Y_final"].mean())
        row["harsh_Y"] = float(harsh["Y_final"].mean())
        row["manageable_unsafe"] = float(manageable["unsafe_fraction"].mean())
        row["frontier_unsafe"] = float(frontier["unsafe_fraction"].mean())
        row["harsh_unsafe"] = float(harsh["unsafe_fraction"].mean())

        rows.append(row)

    return pd.DataFrame(rows)


def plot_candidate_bars(summary):
    os.makedirs("figs", exist_ok=True)

    # Plot only A10-v2 and Pump+Radiator for compact interpretation.
    view = summary[summary["mode"].isin(["a10_hybrid_v2", "pump_radiator"])].copy()
    view["label"] = (
        "S=" + view["storage_scale"].astype(str)
        + " / "
        + view["mode"]
    )

    fig = plt.figure(figsize=(11, 5))
    x = np.arange(len(view))
    plt.bar(x, view["manageable_failure"].values)
    plt.xticks(x, view["label"].values, rotation=35, ha="right")
    plt.ylabel("manageable failure rate")
    plt.title("Phase 1R2C manageable failure confirmation")
    plt.tight_layout()
    fig.savefig("figs/phase1R2C_manageable_failure.png", dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(11, 5))
    x = np.arange(len(view))
    plt.bar(x, view["manageable_CVaR95"].values)
    plt.xticks(x, view["label"].values, rotation=35, ha="right")
    plt.ylabel("manageable CVaR0.95")
    plt.title("Phase 1R2C manageable CVaR0.95 confirmation")
    plt.tight_layout()
    fig.savefig("figs/phase1R2C_manageable_cvar95.png", dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(11, 5))
    x = np.arange(len(view))
    plt.bar(x, view["manageable_Y"].values)
    plt.xticks(x, view["label"].values, rotation=35, ha="right")
    plt.ylabel("manageable mission throughput")
    plt.title("Phase 1R2C manageable throughput confirmation")
    plt.tight_layout()
    fig.savefig("figs/phase1R2C_manageable_throughput.png", dpi=180)
    plt.close(fig)


def write_report(classified, summary, reasons, path, n):
    sep = classified[classified["regime"] == "PASS-MISSION-FEASIBLE-SEPARATION"]
    mission = classified[classified["regime"].str.contains("MISSION-FEASIBLE", regex=False)]

    lines = []
    lines.append("A10-STMS Phase 1R2C High-Sample Confirmation Report")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Monte Carlo samples per stress/mode/candidate: {n}")
    lines.append(f"Manageable sample count per mode/candidate: {n * len(MANAGEABLE_STRESSES)}")
    lines.append(f"Frontier sample count per mode/candidate: {n * len(FRONTIER_STRESSES)}")
    lines.append(f"Harsh sample count per mode/candidate: {n * len(HARSH_STRESSES)}")
    lines.append("")

    lines.append("Classification table:")
    cols = [
        "rad_scale",
        "transport_scale",
        "storage_scale",
        "best_a10_mode",
        "regime",
        "best_manage_failure",
        "best_manage_CVaR95",
        "best_manage_unsafe",
        "best_manage_Y",
        "best_manage_Tc95",
        "best_frontier_failure",
        "best_frontier_CVaR95",
        "best_frontier_unsafe",
        "best_frontier_Y",
        "best_harsh_failure",
        "best_harsh_CVaR95",
        "best_harsh_unsafe",
        "best_harsh_Y",
        "no_control_manage_failure",
        "pump_radiator_manage_failure",
        "pump_radiator_manage_CVaR95",
        "pump_radiator_manage_unsafe",
        "pump_radiator_manage_Y",
    ]
    lines.append(classified[cols].to_string(index=False))
    lines.append("")

    if len(sep) > 0:
        status = "PASS-CONFIRMED-MISSION-FEASIBLE-SEPARATION"
        lines.append("Status: PASS-CONFIRMED-MISSION-FEASIBLE-SEPARATION")
        lines.append("")
        lines.append("Interpretation:")
        lines.append("  The Phase 1R2 separation result survived higher-sample confirmation.")
        lines.append("  A10-Hybrid-v2 preserves the manageable-stress mission condition in a")
        lines.append("  nontrivial resource regime where No Control fails and Pump+Radiator")
        lines.append("  remains worse by failure rate or tail-risk metrics.")
    elif len(mission) > 0:
        status = "PASS-MISSION-FEASIBLE-BUT-SEPARATION-WEAK"
        lines.append("Status: PASS-MISSION-FEASIBLE-BUT-SEPARATION-WEAK")
        lines.append("")
        lines.append("Interpretation:")
        lines.append("  Mission-feasible behavior exists, but the separation from Pump+Radiator")
        lines.append("  is not clean under the higher-sample confirmation.")
    else:
        status = "FAIL-CONFIRMATION-DAMAGE-LIMITING-ONLY"
        lines.append("Status: FAIL-CONFIRMATION-DAMAGE-LIMITING-ONLY")
        lines.append("")
        lines.append("Interpretation:")
        lines.append("  The provisional Phase 1R2 pass did not survive high-sample confirmation.")
        lines.append("  The safe claim reverts to damage-limiting, not mission feasibility.")

    lines.append("")
    lines.append("A10-Hybrid-v2 failure-reason triage:")
    a10_reasons = reasons[reasons["mode"] == "a10_hybrid_v2"].copy()
    reason_cols = [
        "rad_scale",
        "transport_scale",
        "storage_scale",
        "manageable_failure",
        "manageable_fail_Tc",
        "manageable_fail_Tp",
        "manageable_fail_Tr",
        "manageable_fail_G",
        "manageable_fail_Y",
        "frontier_failure",
        "frontier_fail_Tc",
        "frontier_fail_Tp",
        "frontier_fail_Tr",
        "frontier_fail_G",
        "frontier_fail_Y",
        "harsh_failure",
        "harsh_fail_Tc",
        "harsh_fail_Tp",
        "harsh_fail_Tr",
        "harsh_fail_G",
        "harsh_fail_Y",
    ]
    lines.append(a10_reasons[reason_cols].to_string(index=False))
    lines.append("")

    lines.append("Claim boundary:")
    lines.append("  This confirmation remains a reduced nondimensional surrogate result.")
    lines.append("  It does not imply hardware readiness, real spacecraft validation,")
    lines.append("  or superiority over all existing spacecraft thermal-control architectures.")
    lines.append("")
    lines.append("Next step:")
    lines.append("  If PASS-CONFIRMED, proceed to Phase 2 around the best confirmed candidate.")
    lines.append("  Phase 2 should test ablations, delayed sensors, actuator degradation,")
    lines.append("  and out-of-sample stress windows.")
    lines.append("")

    text = "\n".join(lines)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return status, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--seed", type=int, default=424242)
    args = ap.parse_args()

    os.makedirs("outputs", exist_ok=True)
    os.makedirs("figs", exist_ok=True)

    root_rng = np.random.default_rng(args.seed)

    records = []
    total = len(candidate_grid()) * len(MODES) * len(STRESSES) * args.n
    done = 0

    for rad, trans, store in candidate_grid():
        p = r2.make_scaled_params(rad, trans, store)

        for stress in STRESSES:
            for mode in MODES:
                for _ in range(args.n):
                    seed = int(root_rng.integers(0, 2**31 - 1))
                    rec, _ = base.simulate(mode, stress, seed, p, store_history=False)
                    rec["rad_scale"] = rad
                    rec["transport_scale"] = trans
                    rec["storage_scale"] = store
                    records.append(rec)

                    done += 1
                    if done % 2000 == 0:
                        print(f"Progress: {done}/{total}")

    df = pd.DataFrame(records)
    df = add_failure_reasons(df)

    agg = r2.aggregate(df)
    summary = r2.summarize_by_combo(agg)
    classified = r2.classify(summary)
    reasons = reason_summary(df)

    df.to_csv("outputs/phase1R2C_runs.csv", index=False)
    agg.to_csv("outputs/phase1R2C_by_resource_stress_mode.csv", index=False)
    summary.to_csv("outputs/phase1R2C_summary_by_mode.csv", index=False)
    classified.to_csv("outputs/phase1R2C_classification.csv", index=False)
    reasons.to_csv("outputs/phase1R2C_failure_reasons.csv", index=False)

    plot_candidate_bars(summary)

    status, report = write_report(
        classified,
        summary,
        reasons,
        "outputs/phase1R2C_confirmation_report.txt",
        args.n,
    )

    print(report)
    print("")
    print("Wrote:")
    print("  outputs/phase1R2C_runs.csv")
    print("  outputs/phase1R2C_by_resource_stress_mode.csv")
    print("  outputs/phase1R2C_summary_by_mode.csv")
    print("  outputs/phase1R2C_classification.csv")
    print("  outputs/phase1R2C_failure_reasons.csv")
    print("  outputs/phase1R2C_confirmation_report.txt")
    print("  figs/phase1R2C_manageable_failure.png")
    print("  figs/phase1R2C_manageable_cvar95.png")
    print("  figs/phase1R2C_manageable_throughput.png")


if __name__ == "__main__":
    main()
