#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A10-STMS Phase 1R
Resource-frontier recalibration after Phase 1T.

Purpose:
- Phase 1 showed A10-Hybrid minimized tail damage, but all modes failed.
- Phase 1T showed the dominant bottleneck is thermal/gradient, not storage or power.
- Phase 1R sweeps transport/radiator/storage resource scales to locate the transition
  from damage-limiting to mission-feasible operation.

Scope:
- Nondimensional reduced-surrogate audit only.
- Not spacecraft hardware design.
- Not thermal-vacuum validation.
"""

import argparse
import os
from dataclasses import replace
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from a10_stms_phase1 import (
    Params,
    STRESSES,
    MODES,
    simulate,
    cvar,
)

MANAGEABLE_STRESSES = [
    "nominal",
    "burst_heat",
    "eclipse_transition",
    "solar_heating",
    "radiator_degradation",
    "power_shortage",
    "storage_saturation",
]

FRONTIER_STRESSES = [
    "combined_moderate",
]

HARSH_STRESSES = [
    "combined_harsh",
]


def make_scaled_params(rad_scale, transport_scale, storage_scale):
    p = Params()

    # Transport resource: cold plate to plate, plate to radiator.
    p.k_cp *= transport_scale
    p.k_pr *= transport_scale

    # Radiative resource: effective radiator area/emissivity authority.
    p.k_rad *= rad_scale

    # Storage resource: thermal buffer coupling.
    p.k_store *= storage_scale

    return p


def aggregate_records(df):
    rows = []
    for (rad, trans, store, mode, stress), g in df.groupby(
        ["rad_scale", "transport_scale", "storage_scale", "mode", "stress"]
    ):
        rows.append({
            "rad_scale": rad,
            "transport_scale": trans,
            "storage_scale": store,
            "mode": mode,
            "stress": stress,
            "n": len(g),
            "failure_rate": float(g["failure"].mean()),
            "throughput_failure_rate": float(g["throughput_fail"].mean()),
            "mean_V": float(g["V"].mean()),
            "median_V": float(g["V"].median()),
            "CVaR90_V": cvar(g["V"], 0.90),
            "CVaR95_V": cvar(g["V"], 0.95),
            "mean_unsafe_fraction": float(g["unsafe_fraction"].mean()),
            "mean_Y_final": float(g["Y_final"].mean()),
            "max_Tc_p95": float(np.quantile(g["max_Tc"], 0.95)),
            "min_Es_p05": float(np.quantile(g["min_Es"], 0.05)),
            "min_Pm_p05": float(np.quantile(g["min_Pm"], 0.05)),
        })
    return pd.DataFrame(rows)


def regime_summary(agg):
    rows = []

    for (rad, trans, store, mode), g in agg.groupby(
        ["rad_scale", "transport_scale", "storage_scale", "mode"]
    ):
        gm = g[g["stress"].isin(MANAGEABLE_STRESSES)]
        gf = g[g["stress"].isin(FRONTIER_STRESSES)]
        gh = g[g["stress"].isin(HARSH_STRESSES)]

        rows.append({
            "rad_scale": rad,
            "transport_scale": trans,
            "storage_scale": store,
            "mode": mode,

            "manageable_failure": float(gm["failure_rate"].mean()),
            "manageable_CVaR95": float(gm["CVaR95_V"].mean()),
            "manageable_unsafe": float(gm["mean_unsafe_fraction"].mean()),
            "manageable_Y": float(gm["mean_Y_final"].mean()),
            "manageable_Tc95": float(gm["max_Tc_p95"].mean()),

            "frontier_failure": float(gf["failure_rate"].mean()),
            "frontier_CVaR95": float(gf["CVaR95_V"].mean()),
            "frontier_unsafe": float(gf["mean_unsafe_fraction"].mean()),
            "frontier_Y": float(gf["mean_Y_final"].mean()),
            "frontier_Tc95": float(gf["max_Tc_p95"].mean()),

            "harsh_failure": float(gh["failure_rate"].mean()),
            "harsh_CVaR95": float(gh["CVaR95_V"].mean()),
            "harsh_unsafe": float(gh["mean_unsafe_fraction"].mean()),
            "harsh_Y": float(gh["mean_Y_final"].mean()),
            "harsh_Tc95": float(gh["max_Tc_p95"].mean()),
        })

    return pd.DataFrame(rows)


def classify_combo(summary):
    """
    Resource-combo-level classification.
    Uses A10-Hybrid as the candidate architecture, with No Control and Pump+Radiator as checks.
    """
    rows = []

    for (rad, trans, store), g in summary.groupby(
        ["rad_scale", "transport_scale", "storage_scale"]
    ):
        a10 = g[g["mode"] == "a10_hybrid"].iloc[0]
        nc = g[g["mode"] == "no_control"].iloc[0]
        pr = g[g["mode"] == "pump_radiator"].iloc[0]

        # Mission-feasible for manageable stresses.
        a10_manage_ok = (
            a10["manageable_failure"] <= 0.10
            and a10["manageable_Y"] >= 0.80
            and a10["manageable_unsafe"] <= 0.05
        )

        # Frontier case may still fail, but should be less bad than Pump+Radiator.
        a10_frontier_adv = (
            a10["frontier_CVaR95"] <= pr["frontier_CVaR95"]
            and a10["frontier_unsafe"] <= pr["frontier_unsafe"]
        )

        # Not too easy: No Control should not trivially solve the manageable set.
        nontrivial = nc["manageable_failure"] >= 0.20

        if a10_manage_ok and nontrivial and a10_frontier_adv:
            regime = "PASS-CALIBRATED-MISSION-FEASIBLE-SEPARATION"
        elif a10_manage_ok and nontrivial:
            regime = "PASS-CALIBRATED-MISSION-FEASIBLE-NONTRIVIAL"
        elif a10_manage_ok:
            regime = "MISSION-FEASIBLE-BUT-BENCHMARK-TOO-EASY"
        elif a10["manageable_CVaR95"] < pr["manageable_CVaR95"]:
            regime = "DAMAGE-LIMITING-NOT-MISSION-FEASIBLE"
        else:
            regime = "NO-A10-ADVANTAGE-OR-RESOURCE-INSUFFICIENT"

        rows.append({
            "rad_scale": rad,
            "transport_scale": trans,
            "storage_scale": store,
            "regime": regime,

            "a10_manage_failure": float(a10["manageable_failure"]),
            "a10_manage_CVaR95": float(a10["manageable_CVaR95"]),
            "a10_manage_unsafe": float(a10["manageable_unsafe"]),
            "a10_manage_Y": float(a10["manageable_Y"]),
            "a10_manage_Tc95": float(a10["manageable_Tc95"]),

            "a10_frontier_failure": float(a10["frontier_failure"]),
            "a10_frontier_CVaR95": float(a10["frontier_CVaR95"]),
            "a10_frontier_unsafe": float(a10["frontier_unsafe"]),
            "a10_frontier_Y": float(a10["frontier_Y"]),

            "a10_harsh_failure": float(a10["harsh_failure"]),
            "a10_harsh_CVaR95": float(a10["harsh_CVaR95"]),
            "a10_harsh_unsafe": float(a10["harsh_unsafe"]),
            "a10_harsh_Y": float(a10["harsh_Y"]),

            "no_control_manage_failure": float(nc["manageable_failure"]),
            "pump_radiator_manage_failure": float(pr["manageable_failure"]),
            "pump_radiator_manage_CVaR95": float(pr["manageable_CVaR95"]),
            "pump_radiator_frontier_CVaR95": float(pr["frontier_CVaR95"]),
            "pump_radiator_frontier_unsafe": float(pr["frontier_unsafe"]),
        })

    out = pd.DataFrame(rows)

    order = {
        "PASS-CALIBRATED-MISSION-FEASIBLE-SEPARATION": 0,
        "PASS-CALIBRATED-MISSION-FEASIBLE-NONTRIVIAL": 1,
        "MISSION-FEASIBLE-BUT-BENCHMARK-TOO-EASY": 2,
        "DAMAGE-LIMITING-NOT-MISSION-FEASIBLE": 3,
        "NO-A10-ADVANTAGE-OR-RESOURCE-INSUFFICIENT": 4,
    }
    out["regime_order"] = out["regime"].map(order)
    out["resource_score"] = (
        out["rad_scale"] + out["transport_scale"] + 0.5 * out["storage_scale"]
    )

    return out.sort_values(
        [
            "regime_order",
            "resource_score",
            "a10_manage_failure",
            "a10_manage_CVaR95",
        ]
    )


def plot_frontier(classified):
    os.makedirs("figs", exist_ok=True)

    a = classified.copy()
    fig = plt.figure(figsize=(9, 6))

    # Numeric regime code for visualization.
    codes = {
        "PASS-CALIBRATED-MISSION-FEASIBLE-SEPARATION": 0,
        "PASS-CALIBRATED-MISSION-FEASIBLE-NONTRIVIAL": 1,
        "MISSION-FEASIBLE-BUT-BENCHMARK-TOO-EASY": 2,
        "DAMAGE-LIMITING-NOT-MISSION-FEASIBLE": 3,
        "NO-A10-ADVANTAGE-OR-RESOURCE-INSUFFICIENT": 4,
    }
    c = a["regime"].map(codes).values

    sc = plt.scatter(
        a["transport_scale"],
        a["rad_scale"],
        c=c,
        s=70 + 30 * a["storage_scale"],
    )
    plt.xlabel("transport scale")
    plt.ylabel("radiator scale")
    plt.title("Phase 1R resource-frontier classification")
    cb = plt.colorbar(sc)
    cb.set_label("regime code: 0 best, 4 insufficient")
    plt.tight_layout()
    fig.savefig("figs/phase1R_resource_frontier_classification.png", dpi=180)
    plt.close(fig)

    # A10 manageable CVaR surface as scatter.
    fig = plt.figure(figsize=(9, 6))
    sc = plt.scatter(
        a["transport_scale"],
        a["rad_scale"],
        c=a["a10_manage_CVaR95"],
        s=70 + 30 * a["storage_scale"],
    )
    plt.xlabel("transport scale")
    plt.ylabel("radiator scale")
    plt.title("A10-Hybrid manageable-set CVaR0.95 across resources")
    cb = plt.colorbar(sc)
    cb.set_label("A10 manageable CVaR0.95")
    plt.tight_layout()
    fig.savefig("figs/phase1R_a10_manageable_cvar95.png", dpi=180)
    plt.close(fig)


def write_report(classified, summary, path):
    best = classified.iloc[0]
    mission = classified[
        classified["regime"].isin([
            "PASS-CALIBRATED-MISSION-FEASIBLE-SEPARATION",
            "PASS-CALIBRATED-MISSION-FEASIBLE-NONTRIVIAL",
            "MISSION-FEASIBLE-BUT-BENCHMARK-TOO-EASY",
        ])
    ]
    damage = classified[classified["regime"] == "DAMAGE-LIMITING-NOT-MISSION-FEASIBLE"]

    lines = []
    lines.append("A10-STMS Phase 1R Resource-Frontier Recalibration Report")
    lines.append("=" * 78)
    lines.append("")
    lines.append("Purpose:")
    lines.append("  Locate the transition from damage-limiting behavior to mission-feasible")
    lines.append("  behavior by sweeping radiator, transport, and storage resource scales.")
    lines.append("")
    lines.append("Best classified resource point:")
    for k in [
        "rad_scale",
        "transport_scale",
        "storage_scale",
        "regime",
        "a10_manage_failure",
        "a10_manage_CVaR95",
        "a10_manage_unsafe",
        "a10_manage_Y",
        "a10_frontier_failure",
        "a10_frontier_CVaR95",
        "a10_frontier_unsafe",
        "a10_frontier_Y",
        "no_control_manage_failure",
        "pump_radiator_manage_failure",
        "pump_radiator_manage_CVaR95",
    ]:
        lines.append(f"  {k}: {best[k]}")
    lines.append("")

    lines.append("Regime counts:")
    lines.append(classified["regime"].value_counts().to_string())
    lines.append("")

    if len(mission) > 0:
        lines.append("Lowest-resource mission-feasible candidates:")
        cols = [
            "rad_scale",
            "transport_scale",
            "storage_scale",
            "regime",
            "a10_manage_failure",
            "a10_manage_CVaR95",
            "a10_manage_unsafe",
            "a10_manage_Y",
            "no_control_manage_failure",
            "pump_radiator_manage_failure",
        ]
        lines.append(mission.head(12)[cols].to_string(index=False))
    else:
        lines.append("No mission-feasible candidate found in this resource grid.")
        lines.append("This means the tested resource envelope is still too weak, or the A10")
        lines.append("load-preservation logic is too conservative.")
    lines.append("")

    if len(damage) > 0:
        lines.append("Best damage-limiting but not mission-feasible points:")
        cols = [
            "rad_scale",
            "transport_scale",
            "storage_scale",
            "a10_manage_failure",
            "a10_manage_CVaR95",
            "a10_manage_unsafe",
            "a10_manage_Y",
            "pump_radiator_manage_CVaR95",
        ]
        lines.append(damage.head(12)[cols].to_string(index=False))
    lines.append("")

    lines.append("Claim boundary:")
    lines.append("  A PASS here only means that the reduced nondimensional surrogate contains")
    lines.append("  a nontrivial mission-feasible region for the A10-STMS architecture.")
    lines.append("  It is not a spacecraft thermal-control validation or hardware design.")
    lines.append("")
    lines.append("Next decision:")
    lines.append("  If a mission-feasible nontrivial point appears, proceed to Phase 2 stress")
    lines.append("  and ablation tests around the lowest-resource candidate.")
    lines.append("  If only damage-limiting points appear, expand the resource grid or retune")
    lines.append("  the A10 load-preservation barrier.")
    lines.append("")

    text = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8, help="samples per stress/mode/resource point")
    ap.add_argument("--seed", type=int, default=24680)
    args = ap.parse_args()

    os.makedirs("outputs", exist_ok=True)
    os.makedirs("figs", exist_ok=True)

    # Resource grid. Keep this modest for first pass.
    rad_grid = [1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0]
    transport_grid = [1.0, 1.5, 2.0, 3.0, 4.0]
    storage_grid = [1.0, 2.0]

    root_rng = np.random.default_rng(args.seed)

    records = []
    total = len(rad_grid) * len(transport_grid) * len(storage_grid) * len(MODES) * len(STRESSES) * args.n
    done = 0

    for rad in rad_grid:
        for trans in transport_grid:
            for store in storage_grid:
                p = make_scaled_params(rad, trans, store)

                for stress in STRESSES:
                    for mode in MODES:
                        for i in range(args.n):
                            seed = int(root_rng.integers(0, 2**31 - 1))
                            rec, _ = simulate(mode, stress, seed, p, store_history=False)
                            rec["rad_scale"] = rad
                            rec["transport_scale"] = trans
                            rec["storage_scale"] = store
                            records.append(rec)

                            done += 1
                            if done % 5000 == 0:
                                print(f"Progress: {done}/{total}")

    df = pd.DataFrame(records)
    agg = aggregate_records(df)
    summary = regime_summary(agg)
    classified = classify_combo(summary)

    df.to_csv("outputs/phase1R_runs.csv", index=False)
    agg.to_csv("outputs/phase1R_by_resource_stress_mode.csv", index=False)
    summary.to_csv("outputs/phase1R_regime_summary_by_mode.csv", index=False)
    classified.to_csv("outputs/phase1R_resource_classification.csv", index=False)

    plot_frontier(classified)

    report = write_report(
        classified,
        summary,
        "outputs/phase1R_lock_report.txt",
    )

    print(report)
    print("")
    print("Wrote:")
    print("  outputs/phase1R_runs.csv")
    print("  outputs/phase1R_by_resource_stress_mode.csv")
    print("  outputs/phase1R_regime_summary_by_mode.csv")
    print("  outputs/phase1R_resource_classification.csv")
    print("  outputs/phase1R_lock_report.txt")
    print("  figs/phase1R_resource_frontier_classification.png")
    print("  figs/phase1R_a10_manageable_cvar95.png")


if __name__ == "__main__":
    main()
