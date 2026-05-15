#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A10-STMS Phase 1R2
Extended resource-frontier sweep with a load-preserving A10-Hybrid variant.

Reason:
- Phase 1R found only DAMAGE-LIMITING-NOT-MISSION-FEASIBLE regimes.
- Transport scaling strongly reduced tail damage, but mission feasibility was not reached.
- This phase expands resource scales and adds A10-Hybrid-v2:
  more preemptive radiator/transport authority, less aggressive load sacrifice.

Scope:
- Nondimensional reduced-surrogate audit only.
- Not spacecraft hardware design.
- Not thermal-vacuum validation.
"""

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import a10_stms_phase1 as base

old_raw_control = base.raw_control

MODES_R2 = [
    "no_control",
    "pump_radiator",
    "a10_hybrid",
    "a10_hybrid_v2",
]

MANAGEABLE_STRESSES = [
    "nominal",
    "burst_heat",
    "eclipse_transition",
    "solar_heating",
    "radiator_degradation",
    "power_shortage",
    "storage_saturation",
]

FRONTIER_STRESSES = ["combined_moderate"]
HARSH_STRESSES = ["combined_harsh"]


def clip(x, lo, hi):
    return float(np.minimum(np.maximum(x, lo), hi))


def raw_control_r2(mode, x, prev_u, t, stress, p):
    if mode != "a10_hybrid_v2":
        return old_raw_control(mode, x, prev_u, t, stress, p)

    r = base.risks(x, p)
    BT = r["BT"]
    BR = r["BR"]
    BS = r["BS"]
    BP = r["BP"]
    BG = r["BG"]

    # v2 philosophy:
    # - Act earlier on transport/radiator.
    # - Preserve load unless storage/power/thermal risk is severe.
    # - Use high baseline radiator authority because space radiation has long lag.
    # - Avoid using storage too aggressively when storage risk rises.
    resource_ok = 1.0 - 0.45 * BP
    gradient_ok = 1.0 - 0.35 * BG
    storage_ok = 1.0 - 0.70 * BS

    pump = 0.20 + 0.78 * BT * resource_ok * gradient_ok + 0.18 * BR
    valve = 0.34 + 0.55 * BT * gradient_ok + 0.12 * BS
    rad = 0.58 + 0.40 * max(BR, 0.65 * BT) + 0.10 * BS - 0.10 * BP
    store = 0.08 + 0.42 * BT * storage_ok * gradient_ok

    # Less throughput sacrifice than v1.
    load = 1.00 - 0.13 * BT - 0.18 * BP - 0.20 * BS - 0.06 * BG

    return np.array([
        clip(pump, 0.05, 1.00),
        clip(valve, 0.10, 1.00),
        clip(rad, 0.20, 1.00),
        clip(store, 0.00, 0.90),
        clip(load, 0.68, 1.00),
    ], dtype=float)


base.raw_control = raw_control_r2


def make_scaled_params(rad_scale, transport_scale, storage_scale):
    p = base.Params()
    p.k_cp *= transport_scale
    p.k_pr *= transport_scale
    p.k_rad *= rad_scale
    p.k_store *= storage_scale
    return p


def cvar(values, beta=0.95):
    return base.cvar(values, beta)


def aggregate(df):
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


def summarize_by_combo(agg):
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
            "manageable_throughput_failure": float(gm["throughput_failure_rate"].mean()),
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


def classify(summary):
    rows = []

    for (rad, trans, store), g in summary.groupby(
        ["rad_scale", "transport_scale", "storage_scale"]
    ):
        nc = g[g["mode"] == "no_control"].iloc[0]
        pr = g[g["mode"] == "pump_radiator"].iloc[0]
        a10v1 = g[g["mode"] == "a10_hybrid"].iloc[0]
        a10v2 = g[g["mode"] == "a10_hybrid_v2"].iloc[0]

        candidates = [a10v1, a10v2]
        best = sorted(
            candidates,
            key=lambda r: (
                r["manageable_failure"],
                r["manageable_CVaR95"],
                r["manageable_unsafe"],
                -r["manageable_Y"],
            )
        )[0]

        best_mode = best["mode"]

        manage_ok = (
            best["manageable_failure"] <= 0.10
            and best["manageable_unsafe"] <= 0.05
            and best["manageable_Y"] >= 0.80
        )

        nontrivial = nc["manageable_failure"] >= 0.20

        separation = (
            manage_ok
            and nontrivial
            and (
                pr["manageable_failure"] > best["manageable_failure"]
                or pr["manageable_CVaR95"] > 1.25 * best["manageable_CVaR95"]
            )
        )

        pump_also_ok = (
            pr["manageable_failure"] <= 0.10
            and pr["manageable_unsafe"] <= 0.05
            and pr["manageable_Y"] >= 0.80
        )

        if separation:
            regime = "PASS-MISSION-FEASIBLE-SEPARATION"
        elif manage_ok and nontrivial and pump_also_ok:
            regime = "MISSION-FEASIBLE-BUT-PUMP-RADIATOR-ALSO-FEASIBLE"
        elif manage_ok and nontrivial:
            regime = "PASS-MISSION-FEASIBLE-NONTRIVIAL"
        elif manage_ok:
            regime = "MISSION-FEASIBLE-BUT-TOO-EASY"
        elif best["manageable_CVaR95"] < pr["manageable_CVaR95"]:
            regime = "DAMAGE-LIMITING-NOT-MISSION-FEASIBLE"
        else:
            regime = "NO-A10-ADVANTAGE-OR-RESOURCE-INSUFFICIENT"

        rows.append({
            "rad_scale": rad,
            "transport_scale": trans,
            "storage_scale": store,
            "best_a10_mode": best_mode,
            "regime": regime,

            "best_manage_failure": float(best["manageable_failure"]),
            "best_manage_CVaR95": float(best["manageable_CVaR95"]),
            "best_manage_unsafe": float(best["manageable_unsafe"]),
            "best_manage_Y": float(best["manageable_Y"]),
            "best_manage_Tc95": float(best["manageable_Tc95"]),

            "best_frontier_failure": float(best["frontier_failure"]),
            "best_frontier_CVaR95": float(best["frontier_CVaR95"]),
            "best_frontier_unsafe": float(best["frontier_unsafe"]),
            "best_frontier_Y": float(best["frontier_Y"]),

            "best_harsh_failure": float(best["harsh_failure"]),
            "best_harsh_CVaR95": float(best["harsh_CVaR95"]),
            "best_harsh_unsafe": float(best["harsh_unsafe"]),
            "best_harsh_Y": float(best["harsh_Y"]),

            "a10v1_manage_failure": float(a10v1["manageable_failure"]),
            "a10v1_manage_CVaR95": float(a10v1["manageable_CVaR95"]),
            "a10v1_manage_Y": float(a10v1["manageable_Y"]),

            "a10v2_manage_failure": float(a10v2["manageable_failure"]),
            "a10v2_manage_CVaR95": float(a10v2["manageable_CVaR95"]),
            "a10v2_manage_Y": float(a10v2["manageable_Y"]),

            "no_control_manage_failure": float(nc["manageable_failure"]),
            "no_control_manage_CVaR95": float(nc["manageable_CVaR95"]),

            "pump_radiator_manage_failure": float(pr["manageable_failure"]),
            "pump_radiator_manage_CVaR95": float(pr["manageable_CVaR95"]),
            "pump_radiator_manage_unsafe": float(pr["manageable_unsafe"]),
            "pump_radiator_manage_Y": float(pr["manageable_Y"]),
        })

    out = pd.DataFrame(rows)
    order = {
        "PASS-MISSION-FEASIBLE-SEPARATION": 0,
        "PASS-MISSION-FEASIBLE-NONTRIVIAL": 1,
        "MISSION-FEASIBLE-BUT-PUMP-RADIATOR-ALSO-FEASIBLE": 2,
        "MISSION-FEASIBLE-BUT-TOO-EASY": 3,
        "DAMAGE-LIMITING-NOT-MISSION-FEASIBLE": 4,
        "NO-A10-ADVANTAGE-OR-RESOURCE-INSUFFICIENT": 5,
    }
    out["regime_order"] = out["regime"].map(order)
    out["resource_score"] = out["rad_scale"] + out["transport_scale"] + 0.5 * out["storage_scale"]

    return out.sort_values(
        ["regime_order", "resource_score", "best_manage_failure", "best_manage_CVaR95"]
    )


def plot_classification(classified):
    os.makedirs("figs", exist_ok=True)

    codes = {
        "PASS-MISSION-FEASIBLE-SEPARATION": 0,
        "PASS-MISSION-FEASIBLE-NONTRIVIAL": 1,
        "MISSION-FEASIBLE-BUT-PUMP-RADIATOR-ALSO-FEASIBLE": 2,
        "MISSION-FEASIBLE-BUT-TOO-EASY": 3,
        "DAMAGE-LIMITING-NOT-MISSION-FEASIBLE": 4,
        "NO-A10-ADVANTAGE-OR-RESOURCE-INSUFFICIENT": 5,
    }

    df = classified.copy()
    fig = plt.figure(figsize=(9, 6))
    sc = plt.scatter(
        df["transport_scale"],
        df["rad_scale"],
        c=df["regime"].map(codes),
        s=60 + 20 * df["storage_scale"],
    )
    plt.xlabel("transport scale")
    plt.ylabel("radiator scale")
    plt.title("Phase 1R2 extended resource-frontier classification")
    cb = plt.colorbar(sc)
    cb.set_label("regime code: 0 best")
    plt.tight_layout()
    fig.savefig("figs/phase1R2_frontier_classification.png", dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(9, 6))
    sc = plt.scatter(
        df["transport_scale"],
        df["rad_scale"],
        c=df["best_manage_CVaR95"],
        s=60 + 20 * df["storage_scale"],
    )
    plt.xlabel("transport scale")
    plt.ylabel("radiator scale")
    plt.title("Best A10 manageable CVaR0.95")
    cb = plt.colorbar(sc)
    cb.set_label("CVaR0.95")
    plt.tight_layout()
    fig.savefig("figs/phase1R2_best_a10_cvar95.png", dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(9, 6))
    sc = plt.scatter(
        df["transport_scale"],
        df["rad_scale"],
        c=df["best_manage_Y"],
        s=60 + 20 * df["storage_scale"],
    )
    plt.xlabel("transport scale")
    plt.ylabel("radiator scale")
    plt.title("Best A10 manageable mission throughput")
    cb = plt.colorbar(sc)
    cb.set_label("Y")
    plt.tight_layout()
    fig.savefig("figs/phase1R2_best_a10_throughput.png", dpi=180)
    plt.close(fig)


def write_report(classified, path):
    best = classified.iloc[0]
    mission = classified[classified["regime"].str.contains("MISSION-FEASIBLE", regex=False)]
    sep = classified[classified["regime"] == "PASS-MISSION-FEASIBLE-SEPARATION"]
    damage = classified[classified["regime"] == "DAMAGE-LIMITING-NOT-MISSION-FEASIBLE"]

    lines = []
    lines.append("A10-STMS Phase 1R2 Extended Resource-Frontier Report")
    lines.append("=" * 76)
    lines.append("")
    lines.append("Best classified point:")
    for k in [
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
        "no_control_manage_failure",
        "pump_radiator_manage_failure",
        "pump_radiator_manage_CVaR95",
    ]:
        lines.append(f"  {k}: {best[k]}")
    lines.append("")

    lines.append("Regime counts:")
    lines.append(classified["regime"].value_counts().to_string())
    lines.append("")

    if len(sep) > 0:
        lines.append("Mission-feasible separation candidates:")
        lines.append(sep.head(15).to_string(index=False))
    elif len(mission) > 0:
        lines.append("Mission-feasible candidates without clean separation:")
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
            "no_control_manage_failure",
            "pump_radiator_manage_failure",
            "pump_radiator_manage_CVaR95",
        ]
        lines.append(mission.head(15)[cols].to_string(index=False))
    else:
        lines.append("No mission-feasible candidate found even in the extended grid.")
        lines.append("Interpretation: the current surrogate remains thermal/gradient limited,")
        lines.append("or the safety thresholds are too strict for the chosen nondimensional scaling.")
    lines.append("")

    if len(damage) > 0:
        lines.append("Best damage-limiting candidates:")
        cols = [
            "rad_scale",
            "transport_scale",
            "storage_scale",
            "best_a10_mode",
            "best_manage_CVaR95",
            "best_manage_unsafe",
            "best_manage_Y",
            "best_manage_Tc95",
            "pump_radiator_manage_CVaR95",
        ]
        lines.append(damage.head(12)[cols].to_string(index=False))
    lines.append("")

    lines.append("Claim boundary:")
    lines.append("  This is still a reduced nondimensional surrogate audit.")
    lines.append("  A mission-feasible result here would justify Phase 2 stress/ablation testing,")
    lines.append("  not a hardware or spacecraft validation claim.")
    lines.append("")

    text = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--seed", type=int, default=97531)
    args = ap.parse_args()

    os.makedirs("outputs", exist_ok=True)
    os.makedirs("figs", exist_ok=True)

    rad_grid = [1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0]
    transport_grid = [2.0, 4.0, 6.0, 8.0, 12.0]
    storage_grid = [1.0, 2.0, 4.0]

    root_rng = np.random.default_rng(args.seed)

    records = []
    total = len(rad_grid) * len(transport_grid) * len(storage_grid) * len(MODES_R2) * len(base.STRESSES) * args.n
    done = 0

    for rad in rad_grid:
        for trans in transport_grid:
            for store in storage_grid:
                p = make_scaled_params(rad, trans, store)

                for stress in base.STRESSES:
                    for mode in MODES_R2:
                        for _ in range(args.n):
                            seed = int(root_rng.integers(0, 2**31 - 1))
                            rec, _ = base.simulate(mode, stress, seed, p, store_history=False)
                            rec["rad_scale"] = rad
                            rec["transport_scale"] = trans
                            rec["storage_scale"] = store
                            records.append(rec)

                            done += 1
                            if done % 3000 == 0:
                                print(f"Progress: {done}/{total}")

    df = pd.DataFrame(records)
    agg = aggregate(df)
    summary = summarize_by_combo(agg)
    classified = classify(summary)

    df.to_csv("outputs/phase1R2_runs.csv", index=False)
    agg.to_csv("outputs/phase1R2_by_resource_stress_mode.csv", index=False)
    summary.to_csv("outputs/phase1R2_summary_by_mode.csv", index=False)
    classified.to_csv("outputs/phase1R2_classification.csv", index=False)

    plot_classification(classified)

    report = write_report(classified, "outputs/phase1R2_lock_report.txt")
    print(report)

    print("")
    print("Wrote:")
    print("  outputs/phase1R2_runs.csv")
    print("  outputs/phase1R2_by_resource_stress_mode.csv")
    print("  outputs/phase1R2_summary_by_mode.csv")
    print("  outputs/phase1R2_classification.csv")
    print("  outputs/phase1R2_lock_report.txt")
    print("  figs/phase1R2_frontier_classification.png")
    print("  figs/phase1R2_best_a10_cvar95.png")
    print("  figs/phase1R2_best_a10_throughput.png")


if __name__ == "__main__":
    main()
