#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A10-STMS Phase 2D
Delay/degradation redesign after Phase 2.

Reason:
- Phase 2 locked PASS-PHASE2-BASELINE-ABLATION.
- A10-Full worked under baseline/manageable and OOS damage metrics.
- However, sensor delay and actuator degradation exposed a new bottleneck.

This phase adds:
1. a model-based delay predictor for delayed observations;
2. an authority-aware A10 robust-v3 controller;
3. direct comparison against raw A10-Full and Pump+Radiator.

Scope:
- Reduced nondimensional surrogate audit only.
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
import a10_stms_phase2_ablation_oos as p2


MODES = [
    "pump_radiator",
    "a10_full",
    "a10_predictive",
    "a10_robust_v3",
]

CONDITIONS = p2.CONDITIONS
STRESSES = p2.ALL_STRESSES

MANAGEABLE = p2.MANAGEABLE_STRESSES
FRONTIER = p2.FRONTIER_STRESSES
HARSH = p2.HARSH_STRESSES
OOS = p2.OOS_STRESSES


def clip(x, lo, hi):
    return float(np.minimum(np.maximum(x, lo), hi))


def pos(x):
    return float(max(x, 0.0))


def cvar(values, beta=0.95):
    return base.cvar(values, beta)


def make_candidate_params():
    return p2.make_candidate_params()


def robust_v3_control(x, prev_u, condition_name, p):
    """
    Authority-aware and delay-aware variant.

    Design intent:
    - react earlier than v2 under predicted thermal approach;
    - increase baseline radiator/transport authority;
    - retain demand shaping as a last-resort non-degraded channel;
    - avoid sacrificing throughput unless thermal/storage/power barriers demand it.
    """
    cfg = CONDITIONS[condition_name]
    delay = float(cfg["sensor_delay"])
    authority = float(cfg["actuator_authority"])

    r = base.risks(x, p)
    BT = r["BT"]
    BR = r["BR"]
    BS = r["BS"]
    BP = r["BP"]
    BG = r["BG"]

    delay_risk = clip(delay / 1.0, 0.0, 1.0)
    authority_risk = clip((1.0 - authority) / 0.4, 0.0, 1.0)
    preempt = clip(0.65 * delay_risk + 0.55 * authority_risk, 0.0, 1.0)

    resource_ok = 1.0 - 0.38 * BP
    gradient_ok = 1.0 - 0.28 * BG
    storage_ok = 1.0 - 0.62 * BS

    pump = 0.24 + 0.78 * BT * resource_ok * gradient_ok + 0.20 * BR + 0.08 * preempt
    valve = 0.40 + 0.50 * BT * gradient_ok + 0.12 * BS + 0.06 * preempt
    rad = 0.66 + 0.32 * max(BR, 0.62 * BT) + 0.10 * BS - 0.06 * BP + 0.05 * preempt
    store = 0.10 + 0.38 * BT * storage_ok * gradient_ok

    # Demand-side channel: allowed to save the system when cooling actuation is degraded.
    load = 1.00 - 0.13 * BT - 0.18 * BP - 0.20 * BS - 0.06 * BG - 0.05 * preempt

    return np.array([
        clip(pump, 0.05, 1.00),
        clip(valve, 0.10, 1.00),
        clip(rad, 0.20, 1.00),
        clip(store, 0.00, 0.90),
        clip(load, 0.60, 1.00),
    ], dtype=float)


def actual_dynamics_step(x, u, u_prev, t, stress, p, mult, rng, noisy=True):
    sp = p2.phase2_stress_profile(stress, t, p)

    pump, valve, rad_u, store_u, load_u = u
    Tc, Tp, Tr, Es, Pm, G, Y = x

    q_gen = (p.q_idle + p.q_mission * load_u) * sp["heat"] * mult["heat_scale"]

    q_cp = p.k_cp * mult["kcp_scale"] * (0.07 + 1.15 * pump) * (Tc - Tp)
    q_pr = p.k_pr * mult["kpr_scale"] * (0.05 + 1.20 * valve) * (Tp - Tr)

    storage_factor = clip((Es - p.Es_min) / max(1.0 - p.Es_min, 1e-9), 0.0, 1.0)
    q_store = p.k_store * store_u * pos(Tp - p.T_store) * storage_factor

    eps = p.eps_min + (p.eps_max - p.eps_min) * rad_u
    Trad = max(Tr, 0.03)
    q_rad = (
        p.k_rad
        * mult["krad_scale"]
        * sp["rad_eff"]
        * eps
        * pos(Trad**4 - p.T_space**4)
    )

    q_sun = sp["sun"]

    cooling_power = (
        p.P_base
        + p.c_pump * pump**2
        + p.c_rad * rad_u**2
        + p.c_store * store_u**2
        + p.c_valve * abs(valve - u_prev[1]) / max(p.dt, 1e-9)
    )
    pin = sp["pin"] * mult["power_scale"]

    slew_risk = (
        abs(u[0] - u_prev[0])
        + abs(u[1] - u_prev[1])
        + abs(u[3] - u_prev[3])
    ) / max(p.dt, 1e-9)

    G_inst = (
        1.05 * abs(Tc - Tp)
        + 0.80 * abs(Tp - Tr)
        + 0.035 * slew_risk
    )

    if noisy:
        ns = p.base_noise * mult["noise_scale"]
        noise = rng.normal(0.0, ns, size=3)
    else:
        noise = np.zeros(3)

    dTc = (q_gen - q_cp) / p.Cc + noise[0]
    dTp = (q_cp - q_pr - q_store) / p.Cp + noise[1]
    dTr = (q_pr - q_rad + q_sun) / p.Cr + noise[2]

    dEs = (
        -p.k_es * q_store
        + p.k_es_recover
        * sp["storage_recovery"]
        * rad_u
        * pos(0.46 - Tr)
        * (1.0 - Es)
    )

    dPm = p.k_pm * (pin - cooling_power)
    dG = (G_inst - G) / p.tau_g
    dY = load_u / p.T

    x_next = np.array([
        Tc + p.dt * dTc,
        Tp + p.dt * dTp,
        Tr + p.dt * dTr,
        clip(Es + p.dt * dEs, -0.20, 1.10),
        clip(Pm + p.dt * dPm, -0.25, 1.10),
        max(G + p.dt * dG, 0.0),
        Y + p.dt * dY,
    ], dtype=float)

    return x_next


def forecast_state(x_obs, u_prev, t_now, delay_steps, stress, p, mode, condition_name):
    """
    Deterministic short-horizon predictor from the delayed observation.
    This is intentionally simple: it uses nominal uncertainty multipliers and no noise.
    """
    if delay_steps <= 0:
        return x_obs.copy()

    xhat = x_obs.copy()
    uhat_prev = u_prev.copy()

    nominal_mult = {
        "heat_scale": 1.0,
        "kcp_scale": 1.0,
        "kpr_scale": 1.0,
        "krad_scale": 1.0,
        "power_scale": 1.0,
        "noise_scale": 1.0,
    }

    dummy_rng = np.random.default_rng(0)

    t_start = max(0.0, t_now - delay_steps * p.dt)

    for j in range(delay_steps):
        tj = t_start + j * p.dt

        if mode == "a10_robust_v3":
            u_raw = robust_v3_control(xhat, uhat_prev, condition_name, p)
        else:
            u_raw = r2.raw_control_r2(
                "a10_hybrid_v2",
                xhat,
                uhat_prev,
                tj,
                stress if stress in base.STRESSES else "nominal",
                p,
            )

        cfg = CONDITIONS[condition_name]
        u_raw = p2.apply_actuator_authority(u_raw, float(cfg["actuator_authority"]))
        uhat = base.apply_slew(u_raw, uhat_prev, p)

        xhat = actual_dynamics_step(
            xhat,
            uhat,
            uhat_prev,
            tj,
            stress,
            p,
            nominal_mult,
            dummy_rng,
            noisy=False,
        )

        uhat_prev = uhat

    return xhat


def get_control(mode, x_obs, x_buffer, u_prev, t, stress, condition_name, p):
    cfg = CONDITIONS[condition_name]
    delay_steps = int(round(float(cfg["sensor_delay"]) / p.dt))
    authority = float(cfg["actuator_authority"])

    if mode == "pump_radiator":
        u_raw = r2.old_raw_control(
            "pump_radiator",
            x_obs,
            u_prev,
            t,
            stress if stress in base.STRESSES else "nominal",
            p,
        )

    elif mode == "a10_full":
        u_raw = r2.raw_control_r2(
            "a10_hybrid_v2",
            x_obs,
            u_prev,
            t,
            stress if stress in base.STRESSES else "nominal",
            p,
        )

    elif mode == "a10_predictive":
        xhat = forecast_state(
            x_obs,
            u_prev,
            t,
            delay_steps,
            stress,
            p,
            mode,
            condition_name,
        )
        u_raw = r2.raw_control_r2(
            "a10_hybrid_v2",
            xhat,
            u_prev,
            t,
            stress if stress in base.STRESSES else "nominal",
            p,
        )

    elif mode == "a10_robust_v3":
        xhat = forecast_state(
            x_obs,
            u_prev,
            t,
            delay_steps,
            stress,
            p,
            mode,
            condition_name,
        )

        # Additional conservative inflation under delay/degradation.
        delay_risk = clip(float(cfg["sensor_delay"]) / 1.0, 0.0, 1.0)
        authority_risk = clip((1.0 - authority) / 0.4, 0.0, 1.0)

        xhat2 = xhat.copy()
        xhat2[0] += 0.045 * delay_risk + 0.035 * authority_risk
        xhat2[1] += 0.030 * delay_risk + 0.025 * authority_risk

        u_raw = robust_v3_control(xhat2, u_prev, condition_name, p)

    else:
        raise ValueError(f"Unknown mode: {mode}")

    u_raw = p2.apply_actuator_authority(u_raw, authority)
    return base.apply_slew(u_raw, u_prev, p)


def simulate_phase2D(mode, stress, condition_name, seed, p):
    rng = np.random.default_rng(seed)
    mult = base.random_multipliers(rng)

    cfg = CONDITIONS[condition_name]
    delay_steps = int(round(float(cfg["sensor_delay"]) / p.dt))

    x = base.initial_state(stress if stress in base.STRESSES else "combined_moderate")
    u_prev = np.array([0.05, 0.25, 0.42, 0.00, 1.00], dtype=float)
    x_buffer = [x.copy() for _ in range(delay_steps + 1)]

    n = int(round(p.T / p.dt))

    V = 0.0
    unsafe_steps = 0
    finite_ok = True

    max_Tc = x[0]
    max_Tp = x[1]
    max_Tr = x[2]
    min_Es = x[3]
    min_Pm = x[4]
    max_G = x[5]

    for k in range(n):
        t = k * p.dt

        if delay_steps > 0:
            x_obs = x_buffer[0].copy()
        else:
            x_obs = x.copy()

        u = get_control(mode, x_obs, x_buffer, u_prev, t, stress, condition_name, p)

        x_next = actual_dynamics_step(
            x,
            u,
            u_prev,
            t,
            stress,
            p,
            mult,
            rng,
            noisy=True,
        )

        if not np.all(np.isfinite(x_next)):
            finite_ok = False
            break

        vt = base.violation_terms(x_next, p)
        Vinst = sum(vt.values())
        V += p.dt * Vinst

        if base.is_unsafe(x_next, p):
            unsafe_steps += 1

        max_Tc = max(max_Tc, x_next[0])
        max_Tp = max(max_Tp, x_next[1])
        max_Tr = max(max_Tr, x_next[2])
        min_Es = min(min_Es, x_next[3])
        min_Pm = min(min_Pm, x_next[4])
        max_G = max(max_G, x_next[5])

        x = x_next
        u_prev = u

        x_buffer.append(x.copy())
        if len(x_buffer) > delay_steps + 1:
            x_buffer.pop(0)

    Y_final = float(x[6])
    throughput_fail = Y_final < p.Y_min
    failure = (not finite_ok) or (unsafe_steps > 0) or throughput_fail

    return {
        "mode": mode,
        "stress": stress,
        "stress_family": p2.stress_family(stress),
        "condition": condition_name,
        "seed": seed,
        "finite_ok": bool(finite_ok),
        "failure": bool(failure),
        "throughput_fail": bool(throughput_fail),
        "V": float(V),
        "unsafe_fraction": float(unsafe_steps / max(n, 1)),
        "max_Tc": float(max_Tc),
        "max_Tp": float(max_Tp),
        "max_Tr": float(max_Tr),
        "min_Es": float(min_Es),
        "min_Pm": float(min_Pm),
        "max_G": float(max_G),
        "Y_final": float(Y_final),
    }


def add_failure_reasons(df, p):
    df = df.copy()
    df["fail_Tc"] = df["max_Tc"] > p.Tc_max
    df["fail_Tp"] = df["max_Tp"] > p.Tp_max
    df["fail_Tr"] = df["max_Tr"] > p.Tr_max
    df["fail_Es"] = df["min_Es"] < p.Es_min
    df["fail_Pm"] = df["min_Pm"] < p.Pm_min
    df["fail_G"] = df["max_G"] > p.G_max
    df["fail_Y"] = df["Y_final"] < p.Y_min
    return df


def aggregate(df):
    rows = []
    for (condition, family, mode), g in df.groupby(["condition", "stress_family", "mode"]):
        rows.append({
            "condition": condition,
            "stress_family": family,
            "mode": mode,
            "n": len(g),
            "finite_rate": float(g["finite_ok"].mean()),
            "failure_rate": float(g["failure"].mean()),
            "throughput_failure_rate": float(g["throughput_fail"].mean()),
            "mean_V": float(g["V"].mean()),
            "median_V": float(g["V"].median()),
            "CVaR90_V": cvar(g["V"], 0.90),
            "CVaR95_V": cvar(g["V"], 0.95),
            "mean_unsafe_fraction": float(g["unsafe_fraction"].mean()),
            "mean_Y_final": float(g["Y_final"].mean()),
            "max_Tc_p95": float(np.quantile(g["max_Tc"], 0.95)),
            "max_Tp_p95": float(np.quantile(g["max_Tp"], 0.95)),
            "max_Tr_p95": float(np.quantile(g["max_Tr"], 0.95)),
            "min_Es_p05": float(np.quantile(g["min_Es"], 0.05)),
            "min_Pm_p05": float(np.quantile(g["min_Pm"], 0.05)),
            "fail_Tc_rate": float(g["fail_Tc"].mean()),
            "fail_Tp_rate": float(g["fail_Tp"].mean()),
            "fail_Tr_rate": float(g["fail_Tr"].mean()),
            "fail_Es_rate": float(g["fail_Es"].mean()),
            "fail_Pm_rate": float(g["fail_Pm"].mean()),
            "fail_G_rate": float(g["fail_G"].mean()),
            "fail_Y_rate": float(g["fail_Y"].mean()),
        })
    return pd.DataFrame(rows)


def getrow(agg, condition, family, mode):
    q = agg[
        (agg["condition"] == condition)
        & (agg["stress_family"] == family)
        & (agg["mode"] == mode)
    ]
    if len(q) == 0:
        return None
    return q.iloc[0]


def plot_results(agg):
    os.makedirs("figs", exist_ok=True)

    # Manageable comparison across conditions.
    for condition in CONDITIONS.keys():
        view = agg[
            (agg["condition"] == condition)
            & (agg["stress_family"] == "manageable")
        ].copy().sort_values(["failure_rate", "CVaR95_V"])

        fig = plt.figure(figsize=(10, 5))
        x = np.arange(len(view))
        plt.bar(x, view["failure_rate"].values)
        plt.xticks(x, view["mode"].values, rotation=30, ha="right")
        plt.ylabel("failure rate")
        plt.title(f"Phase 2D manageable failure: {condition}")
        plt.tight_layout()
        fig.savefig(f"figs/phase2D_manageable_failure_{condition}.png", dpi=180)
        plt.close(fig)

    # Robust-v3 condition trend.
    view = agg[
        (agg["mode"] == "a10_robust_v3")
        & (agg["stress_family"] == "manageable")
    ].copy().sort_values("condition")

    fig = plt.figure(figsize=(10, 5))
    x = np.arange(len(view))
    plt.bar(x, view["failure_rate"].values)
    plt.xticks(x, view["condition"].values, rotation=30, ha="right")
    plt.ylabel("failure rate")
    plt.title("A10 robust-v3 manageable failure across conditions")
    plt.tight_layout()
    fig.savefig("figs/phase2D_robust_v3_condition_failure.png", dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(10, 5))
    x = np.arange(len(view))
    plt.bar(x, view["mean_Y_final"].values)
    plt.xticks(x, view["condition"].values, rotation=30, ha="right")
    plt.ylabel("mission throughput")
    plt.title("A10 robust-v3 throughput across conditions")
    plt.tight_layout()
    fig.savefig("figs/phase2D_robust_v3_condition_throughput.png", dpi=180)
    plt.close(fig)


def write_report(agg, n, path):
    lines = []
    lines.append("A10-STMS Phase 2D Delay/Degradation Redesign Report")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Monte Carlo samples per stress/mode/condition: {n}")
    lines.append("Candidate resource point: rad_scale=24.0, transport_scale=12.0, storage_scale=4.0")
    lines.append("")

    cols = [
        "condition",
        "stress_family",
        "mode",
        "n",
        "failure_rate",
        "CVaR95_V",
        "mean_unsafe_fraction",
        "mean_Y_final",
        "max_Tc_p95",
        "fail_Tc_rate",
        "fail_Tp_rate",
        "fail_Y_rate",
    ]

    for condition in CONDITIONS.keys():
        lines.append(f"Manageable family / {condition}:")
        view = agg[
            (agg["condition"] == condition)
            & (agg["stress_family"] == "manageable")
        ].copy().sort_values(["failure_rate", "CVaR95_V"])
        lines.append(view[cols].to_string(index=False))
        lines.append("")

    lines.append("Out-of-sample family / baseline:")
    view = agg[
        (agg["condition"] == "baseline")
        & (agg["stress_family"] == "out_of_sample")
    ].copy().sort_values(["failure_rate", "CVaR95_V"])
    lines.append(view[cols].to_string(index=False))
    lines.append("")

    lines.append("Frontier family / baseline:")
    view = agg[
        (agg["condition"] == "baseline")
        & (agg["stress_family"] == "frontier")
    ].copy().sort_values(["failure_rate", "CVaR95_V"])
    lines.append(view[cols].to_string(index=False))
    lines.append("")

    def pass_manage(row, fail_thr, unsafe_thr=0.05):
        return (
            row is not None
            and row["failure_rate"] <= fail_thr
            and row["mean_unsafe_fraction"] <= unsafe_thr
            and row["mean_Y_final"] >= 0.80
        )

    r_base = getrow(agg, "baseline", "manageable", "a10_robust_v3")
    r_delay05 = getrow(agg, "sensor_delay_0p5", "manageable", "a10_robust_v3")
    r_delay10 = getrow(agg, "sensor_delay_1p0", "manageable", "a10_robust_v3")
    r_act08 = getrow(agg, "actuator_0p8", "manageable", "a10_robust_v3")
    r_act06 = getrow(agg, "actuator_0p6", "manageable", "a10_robust_v3")

    full_delay05 = getrow(agg, "sensor_delay_0p5", "manageable", "a10_full")
    full_act08 = getrow(agg, "actuator_0p8", "manageable", "a10_full")

    oos_r3 = getrow(agg, "baseline", "out_of_sample", "a10_robust_v3")
    oos_pump = getrow(agg, "baseline", "out_of_sample", "pump_radiator")

    baseline_pass = pass_manage(r_base, 0.10)
    delay05_pass = pass_manage(r_delay05, 0.15)
    act08_pass = pass_manage(r_act08, 0.15)
    delay10_soft = pass_manage(r_delay10, 0.35, unsafe_thr=0.18)
    act06_soft = pass_manage(r_act06, 0.35, unsafe_thr=0.08)

    improvement_delay05 = (
        r_delay05 is not None
        and full_delay05 is not None
        and r_delay05["failure_rate"] < full_delay05["failure_rate"]
        and r_delay05["CVaR95_V"] < full_delay05["CVaR95_V"]
    )

    improvement_act08 = (
        r_act08 is not None
        and full_act08 is not None
        and r_act08["failure_rate"] < full_act08["failure_rate"]
        and r_act08["CVaR95_V"] < full_act08["CVaR95_V"]
    )

    oos_damage_pass = (
        oos_r3 is not None
        and oos_pump is not None
        and oos_r3["CVaR95_V"] < oos_pump["CVaR95_V"]
        and oos_r3["mean_unsafe_fraction"] <= oos_pump["mean_unsafe_fraction"]
    )

    if baseline_pass and delay05_pass and act08_pass and oos_damage_pass:
        if delay10_soft and act06_soft:
            status = "PASS-PHASE2D-ROBUST-REDESIGN"
        else:
            status = "PASS-PHASE2D-PARTIAL-DELAY-DEGRADE-ROBUSTNESS"
    elif baseline_pass and (improvement_delay05 or improvement_act08):
        status = "PASS-PHASE2D-IMPROVEMENT-NOT-ROBUST"
    else:
        status = "NEEDS-TRIAGE-PHASE2D"

    lines.append("Predeclared Phase 2D checks:")
    lines.append(f"  baseline_pass: {baseline_pass}")
    lines.append(f"  delay05_pass: {delay05_pass}")
    lines.append(f"  act08_pass: {act08_pass}")
    lines.append(f"  delay10_soft_pass: {delay10_soft}")
    lines.append(f"  act06_soft_pass: {act06_soft}")
    lines.append(f"  improvement_vs_raw_a10_delay05: {improvement_delay05}")
    lines.append(f"  improvement_vs_raw_a10_act08: {improvement_act08}")
    lines.append(f"  out_of_sample_damage_pass: {oos_damage_pass}")
    lines.append("")
    lines.append(f"Status: {status}")
    lines.append("")

    lines.append("Claim boundary:")
    lines.append("  A Phase 2D pass remains a reduced nondimensional surrogate result.")
    lines.append("  It supports only delay/degradation robustness inside this toy/preflight model.")
    lines.append("  It is not spacecraft hardware validation.")
    lines.append("")

    lines.append("Next step:")
    lines.append("  If PASS-PHASE2D, proceed to Phase 3 resource-frontier/mission-readiness synthesis.")
    lines.append("  If only improvement is observed, record a delayed-observation bottleneck and")
    lines.append("  keep the paper claim at baseline-ablation/OOS-damage level.")
    lines.append("")

    report = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    return status, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=32)
    ap.add_argument("--seed", type=int, default=626262)
    args = ap.parse_args()

    os.makedirs("outputs", exist_ok=True)
    os.makedirs("figs", exist_ok=True)

    p = make_candidate_params()
    root_rng = np.random.default_rng(args.seed)

    records = []
    total = len(CONDITIONS) * len(STRESSES) * len(MODES) * args.n
    done = 0

    for condition in CONDITIONS.keys():
        for stress in STRESSES:
            for mode in MODES:
                for _ in range(args.n):
                    seed = int(root_rng.integers(0, 2**31 - 1))
                    rec = simulate_phase2D(mode, stress, condition, seed, p)
                    records.append(rec)

                    done += 1
                    if done % 3000 == 0:
                        print(f"Progress: {done}/{total}")

    df = pd.DataFrame(records)
    df = add_failure_reasons(df, p)
    agg = aggregate(df)

    df.to_csv("outputs/phase2D_runs.csv", index=False)
    agg.to_csv("outputs/phase2D_by_family_condition_mode.csv", index=False)

    plot_results(agg)

    status, report = write_report(
        agg,
        args.n,
        "outputs/phase2D_lock_report.txt",
    )

    print(report)
    print("")
    print("Wrote:")
    print("  outputs/phase2D_runs.csv")
    print("  outputs/phase2D_by_family_condition_mode.csv")
    print("  outputs/phase2D_lock_report.txt")
    print("  figs/phase2D_*.png")


if __name__ == "__main__":
    main()
