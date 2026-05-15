#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A10-STMS Phase 2E
Authority-limited retuning after Phase 2D.

Purpose:
- Phase 2D solved the sensor-delay bottleneck but narrowly missed actuator_0p8.
- This phase tests authority-aware v4 variants that add mild preemptive
  demand shaping and stronger thermal-routing bias under actuator degradation.

Scope:
- Reduced nondimensional surrogate audit only.
- Not spacecraft hardware design.
"""

import argparse
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import a10_stms_phase1 as base
import a10_stms_phase1R2_extended_frontier as r2
import a10_stms_phase2_ablation_oos as p2
import a10_stms_phase2D_delay_degrade_redesign as p2d


MODES = [
    "pump_radiator",
    "a10_robust_v3",
    "a10_v4_balanced",
    "a10_v4_safe",
]

CONDITIONS = p2.CONDITIONS
STRESSES = p2.ALL_STRESSES

MANAGEABLE = p2.MANAGEABLE_STRESSES
OOS = p2.OOS_STRESSES
FRONTIER = p2.FRONTIER_STRESSES
HARSH = p2.HARSH_STRESSES


def clip(x, lo, hi):
    return float(np.minimum(np.maximum(x, lo), hi))


def cvar(values, beta=0.95):
    return base.cvar(values, beta)


def make_candidate_params():
    return p2.make_candidate_params()


def v4_control(x, prev_u, condition_name, p, variant):
    """
    v4_balanced:
      preserve throughput while adding actuator-degradation awareness.
    v4_safe:
      slightly more demand-side sacrifice under actuator degradation.
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

    preempt = clip(0.58 * delay_risk + 0.72 * authority_risk, 0.0, 1.0)

    resource_ok = 1.0 - 0.34 * BP
    gradient_ok = 1.0 - 0.24 * BG
    storage_ok = 1.0 - 0.58 * BS

    if variant == "balanced":
        pump = 0.28 + 0.78 * BT * resource_ok * gradient_ok + 0.20 * BR + 0.10 * preempt
        valve = 0.44 + 0.50 * BT * gradient_ok + 0.12 * BS + 0.08 * preempt
        rad = 0.70 + 0.30 * max(BR, 0.62 * BT) + 0.08 * BS - 0.05 * BP + 0.06 * preempt
        store = 0.10 + 0.36 * BT * storage_ok * gradient_ok
        load = 1.00 - 0.12 * BT - 0.18 * BP - 0.19 * BS - 0.05 * BG - 0.08 * authority_risk - 0.04 * delay_risk
        load_min = 0.70

    elif variant == "safe":
        pump = 0.30 + 0.76 * BT * resource_ok * gradient_ok + 0.22 * BR + 0.12 * preempt
        valve = 0.46 + 0.48 * BT * gradient_ok + 0.12 * BS + 0.10 * preempt
        rad = 0.74 + 0.28 * max(BR, 0.60 * BT) + 0.08 * BS - 0.04 * BP + 0.08 * preempt
        store = 0.10 + 0.34 * BT * storage_ok * gradient_ok
        load = 1.00 - 0.13 * BT - 0.18 * BP - 0.20 * BS - 0.05 * BG - 0.12 * authority_risk - 0.05 * delay_risk
        load_min = 0.64

    else:
        raise ValueError(variant)

    return np.array([
        clip(pump, 0.05, 1.00),
        clip(valve, 0.10, 1.00),
        clip(rad, 0.20, 1.00),
        clip(store, 0.00, 0.90),
        clip(load, load_min, 1.00),
    ], dtype=float)


def forecast_state_v4(x_obs, u_prev, t_now, delay_steps, stress, p, condition_name, mode):
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

        if mode == "a10_v4_balanced":
            u_raw = v4_control(xhat, uhat_prev, condition_name, p, "balanced")
        elif mode == "a10_v4_safe":
            u_raw = v4_control(xhat, uhat_prev, condition_name, p, "safe")
        else:
            u_raw = p2d.robust_v3_control(xhat, uhat_prev, condition_name, p)

        cfg = CONDITIONS[condition_name]
        u_raw = p2.apply_actuator_authority(u_raw, float(cfg["actuator_authority"]))
        uhat = base.apply_slew(u_raw, uhat_prev, p)

        xhat = p2d.actual_dynamics_step(
            xhat, uhat, uhat_prev, tj, stress, p, nominal_mult, dummy_rng, noisy=False
        )
        uhat_prev = uhat

    return xhat


def get_control(mode, x_obs, u_prev, t, stress, condition_name, p):
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

    elif mode == "a10_robust_v3":
        xhat = p2d.forecast_state(x_obs, u_prev, t, delay_steps, stress, p, mode, condition_name)
        delay_risk = clip(float(cfg["sensor_delay"]) / 1.0, 0.0, 1.0)
        authority_risk = clip((1.0 - authority) / 0.4, 0.0, 1.0)
        xhat2 = xhat.copy()
        xhat2[0] += 0.045 * delay_risk + 0.035 * authority_risk
        xhat2[1] += 0.030 * delay_risk + 0.025 * authority_risk
        u_raw = p2d.robust_v3_control(xhat2, u_prev, condition_name, p)

    elif mode == "a10_v4_balanced":
        xhat = forecast_state_v4(x_obs, u_prev, t, delay_steps, stress, p, condition_name, mode)
        delay_risk = clip(float(cfg["sensor_delay"]) / 1.0, 0.0, 1.0)
        authority_risk = clip((1.0 - authority) / 0.4, 0.0, 1.0)
        xhat2 = xhat.copy()
        xhat2[0] += 0.050 * delay_risk + 0.045 * authority_risk
        xhat2[1] += 0.034 * delay_risk + 0.030 * authority_risk
        u_raw = v4_control(xhat2, u_prev, condition_name, p, "balanced")

    elif mode == "a10_v4_safe":
        xhat = forecast_state_v4(x_obs, u_prev, t, delay_steps, stress, p, condition_name, mode)
        delay_risk = clip(float(cfg["sensor_delay"]) / 1.0, 0.0, 1.0)
        authority_risk = clip((1.0 - authority) / 0.4, 0.0, 1.0)
        xhat2 = xhat.copy()
        xhat2[0] += 0.055 * delay_risk + 0.060 * authority_risk
        xhat2[1] += 0.038 * delay_risk + 0.040 * authority_risk
        u_raw = v4_control(xhat2, u_prev, condition_name, p, "safe")

    else:
        raise ValueError(f"Unknown mode: {mode}")

    u_raw = p2.apply_actuator_authority(u_raw, authority)
    return base.apply_slew(u_raw, u_prev, p)


def simulate(mode, stress, condition_name, seed, p):
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

        u = get_control(mode, x_obs, u_prev, t, stress, condition_name, p)

        x_next = p2d.actual_dynamics_step(
            x, u, u_prev, t, stress, p, mult, rng, noisy=True
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
        "condition": condition_name,
        "stress": stress,
        "stress_family": p2.stress_family(stress),
        "mode": mode,
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


def row(agg, condition, family, mode):
    q = agg[
        (agg["condition"] == condition)
        & (agg["stress_family"] == family)
        & (agg["mode"] == mode)
    ]
    if len(q) == 0:
        return None
    return q.iloc[0]


def write_report(agg, n, out_path):
    lines = []
    lines.append("A10-STMS Phase 2E Authority-Limited Retuning Report")
    lines.append("=" * 78)
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
        view = agg[
            (agg["condition"] == condition)
            & (agg["stress_family"] == "manageable")
        ].copy().sort_values(["failure_rate", "CVaR95_V"])
        lines.append(f"Manageable family / {condition}:")
        lines.append(view[cols].to_string(index=False))
        lines.append("")

    lines.append("Out-of-sample family / baseline:")
    view = agg[
        (agg["condition"] == "baseline")
        & (agg["stress_family"] == "out_of_sample")
    ].copy().sort_values(["failure_rate", "CVaR95_V"])
    lines.append(view[cols].to_string(index=False))
    lines.append("")

    def pass_manage(r, fail_thr, unsafe_thr=0.05):
        return (
            r is not None
            and r["failure_rate"] <= fail_thr
            and r["mean_unsafe_fraction"] <= unsafe_thr
            and r["mean_Y_final"] >= 0.80
        )

    candidates = ["a10_robust_v3", "a10_v4_balanced", "a10_v4_safe"]

    best_rows = {}
    for cond in CONDITIONS.keys():
        available = [row(agg, cond, "manageable", m) for m in candidates]
        available = [r for r in available if r is not None]
        best = sorted(
            available,
            key=lambda r: (r["failure_rate"], r["CVaR95_V"], r["mean_unsafe_fraction"], -r["mean_Y_final"])
        )[0]
        best_rows[cond] = best

    baseline_pass = pass_manage(best_rows["baseline"], 0.10)
    delay05_pass = pass_manage(best_rows["sensor_delay_0p5"], 0.15)
    delay10_pass = pass_manage(best_rows["sensor_delay_1p0"], 0.15)
    act08_pass = pass_manage(best_rows["actuator_0p8"], 0.15)
    act06_soft = pass_manage(best_rows["actuator_0p6"], 0.35, unsafe_thr=0.08)

    oos_best = sorted(
        [row(agg, "baseline", "out_of_sample", m) for m in candidates],
        key=lambda r: (r["failure_rate"], r["CVaR95_V"])
    )[0]
    oos_pump = row(agg, "baseline", "out_of_sample", "pump_radiator")
    oos_pass = (
        oos_best["CVaR95_V"] < oos_pump["CVaR95_V"]
        and oos_best["mean_unsafe_fraction"] <= oos_pump["mean_unsafe_fraction"]
    )

    if baseline_pass and delay05_pass and delay10_pass and act08_pass and act06_soft and oos_pass:
        status = "PASS-PHASE2E-DELAY-DEGRADE-ROBUSTNESS"
    elif baseline_pass and delay05_pass and delay10_pass and act08_pass and oos_pass:
        status = "PASS-PHASE2E-MODERATE-DEGRADE-ROBUSTNESS"
    elif baseline_pass and oos_pass:
        status = "PASS-PHASE2E-PARTIAL-RETUNE"
    else:
        status = "NEEDS-TRIAGE-PHASE2E"

    lines.append("Best manageable candidate by condition:")
    best_table = pd.DataFrame([dict(r) for r in best_rows.values()])
    lines.append(best_table[cols].to_string(index=False))
    lines.append("")

    lines.append("Predeclared Phase 2E checks:")
    lines.append(f"  baseline_pass: {baseline_pass}")
    lines.append(f"  delay05_pass: {delay05_pass}")
    lines.append(f"  delay10_pass: {delay10_pass}")
    lines.append(f"  actuator_0p8_pass: {act08_pass}")
    lines.append(f"  actuator_0p6_soft_pass: {act06_soft}")
    lines.append(f"  out_of_sample_damage_pass: {oos_pass}")
    lines.append("")
    lines.append(f"Status: {status}")
    lines.append("")

    lines.append("Claim boundary:")
    lines.append("  This remains a reduced nondimensional surrogate audit.")
    lines.append("  It supports only toy-model delay/degradation robustness, not hardware validation.")
    lines.append("")

    lines.append("Next step:")
    lines.append("  If PASS-PHASE2E, close Phase 2 and move to Phase 3 synthesis.")
    lines.append("  If not, retain Phase 2D's partial robustness claim and do not overstate actuator-degraded performance.")
    lines.append("")

    text = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return status, text


def plot_results(agg):
    os.makedirs("figs", exist_ok=True)
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
        plt.title(f"Phase 2E manageable failure: {condition}")
        plt.tight_layout()
        fig.savefig(f"figs/phase2E_manageable_failure_{condition}.png", dpi=180)
        plt.close(fig)

    view = agg[
        (agg["condition"] == "baseline")
        & (agg["stress_family"] == "out_of_sample")
    ].copy().sort_values(["failure_rate", "CVaR95_V"])

    fig = plt.figure(figsize=(10, 5))
    x = np.arange(len(view))
    plt.bar(x, view["CVaR95_V"].values)
    plt.xticks(x, view["mode"].values, rotation=30, ha="right")
    plt.ylabel("CVaR0.95")
    plt.title("Phase 2E OOS CVaR0.95 baseline")
    plt.tight_layout()
    fig.savefig("figs/phase2E_oos_cvar95_baseline.png", dpi=180)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=32)
    ap.add_argument("--seed", type=int, default=737373)
    args = ap.parse_args()

    os.makedirs("outputs", exist_ok=True)
    os.makedirs("figs", exist_ok=True)

    p = make_candidate_params()
    rng = np.random.default_rng(args.seed)

    records = []
    total = len(CONDITIONS) * len(STRESSES) * len(MODES) * args.n
    done = 0

    for condition in CONDITIONS.keys():
        for stress in STRESSES:
            for mode in MODES:
                for _ in range(args.n):
                    seed = int(rng.integers(0, 2**31 - 1))
                    rec = simulate(mode, stress, condition, seed, p)
                    records.append(rec)
                    done += 1
                    if done % 3000 == 0:
                        print(f"Progress: {done}/{total}")

    df = pd.DataFrame(records)
    df = add_failure_reasons(df, p)
    agg = aggregate(df)

    df.to_csv("outputs/phase2E_runs.csv", index=False)
    agg.to_csv("outputs/phase2E_by_family_condition_mode.csv", index=False)

    plot_results(agg)

    status, report = write_report(agg, args.n, "outputs/phase2E_lock_report.txt")
    print(report)
    print("")
    print("Wrote:")
    print("  outputs/phase2E_runs.csv")
    print("  outputs/phase2E_by_family_condition_mode.csv")
    print("  outputs/phase2E_lock_report.txt")
    print("  figs/phase2E_*.png")


if __name__ == "__main__":
    main()
