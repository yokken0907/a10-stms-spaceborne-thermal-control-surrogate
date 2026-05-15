#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A10-STMS Phase 2
Ablation, sensor-delay, actuator-degradation, and out-of-sample stress validation.

Starting point:
- Phase 1R2C confirmed mission-feasible separation for:
    rad_scale = 24.0
    transport_scale = 12.0
    storage_scale = 1.0, 2.0, 4.0
- This Phase 2 focuses on the strongest confirmed candidate:
    rad_scale = 24.0
    transport_scale = 12.0
    storage_scale = 4.0

Scope:
- Reduced nondimensional surrogate audit only.
- Not spacecraft hardware design.
- Not thermal-vacuum validation.
"""

import argparse
import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import a10_stms_phase1 as base
import a10_stms_phase1R2_extended_frontier as r2

# Importing r2 installs the a10_hybrid_v2 controller into the previous framework.
# We still explicitly call r2.raw_control_r2 to avoid ambiguity.

P_CANDIDATE = {
    "rad_scale": 24.0,
    "transport_scale": 12.0,
    "storage_scale": 4.0,
}

BASE_STRESSES = base.STRESSES

OOS_STRESSES = [
    "oos_dual_burst",
    "oos_long_eclipse",
    "oos_sun_locked_radiator",
    "oos_brownout_burst",
    "oos_recovery_lag",
]

ALL_STRESSES = BASE_STRESSES + OOS_STRESSES

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

MODES = [
    "no_control",
    "pump_radiator",
    "a10_v1",
    "a10_full",
    "a10_no_valve",
    "a10_no_store",
    "a10_no_load",
]

CONDITIONS = {
    "baseline": {
        "sensor_delay": 0.0,
        "actuator_authority": 1.0,
    },
    "sensor_delay_0p5": {
        "sensor_delay": 0.5,
        "actuator_authority": 1.0,
    },
    "sensor_delay_1p0": {
        "sensor_delay": 1.0,
        "actuator_authority": 1.0,
    },
    "actuator_0p8": {
        "sensor_delay": 0.0,
        "actuator_authority": 0.8,
    },
    "actuator_0p6": {
        "sensor_delay": 0.0,
        "actuator_authority": 0.6,
    },
}


def clip(x, lo, hi):
    return float(np.minimum(np.maximum(x, lo), hi))


def pos(x):
    return float(max(x, 0.0))


def cvar(values, beta=0.95):
    return base.cvar(values, beta)


def make_candidate_params():
    p = base.Params()
    p.k_cp *= P_CANDIDATE["transport_scale"]
    p.k_pr *= P_CANDIDATE["transport_scale"]
    p.k_rad *= P_CANDIDATE["rad_scale"]
    p.k_store *= P_CANDIDATE["storage_scale"]
    return p


def phase2_stress_profile(stress, t, p):
    if stress in BASE_STRESSES:
        return base.stress_profile(stress, t, p)

    heat = 1.0
    sun = 0.035
    rad_eff = 1.0
    pin = 1.0
    storage_recovery = 1.0

    mid = 1.0 if (0.42 * p.T <= t <= 0.58 * p.T) else 0.0
    early = 1.0 if (0.18 * p.T <= t <= 0.28 * p.T) else 0.0
    late = 1.0 if (0.70 * p.T <= t <= 0.80 * p.T) else 0.0
    long_eclipse = 1.0 if (0.25 * p.T <= t <= 0.76 * p.T) else 0.0

    if stress == "oos_dual_burst":
        heat = 1.05 + 0.85 * early + 0.95 * late
        sun = 0.075
        rad_eff = 0.82
        pin = 0.82
        storage_recovery = 0.75

    elif stress == "oos_long_eclipse":
        heat = 1.02 + 0.40 * mid
        sun = 0.015 * (1.0 - long_eclipse)
        rad_eff = 0.85
        pin = 1.0 - 0.55 * long_eclipse
        storage_recovery = 0.70

    elif stress == "oos_sun_locked_radiator":
        heat = 1.04 + 0.45 * mid
        sun = 0.18
        rad_eff = 0.45
        pin = 0.88
        storage_recovery = 0.65

    elif stress == "oos_brownout_burst":
        heat = 1.10 + 0.90 * mid
        sun = 0.075
        rad_eff = 0.70
        pin = 0.52
        storage_recovery = 0.70

    elif stress == "oos_recovery_lag":
        heat = 1.04 + 0.75 * mid
        sun = 0.080
        rad_eff = 0.72
        pin = 0.78
        storage_recovery = 0.32

    else:
        raise ValueError(f"Unknown stress: {stress}")

    return {
        "heat": heat,
        "sun": sun,
        "rad_eff": rad_eff,
        "pin": pin,
        "storage_recovery": storage_recovery,
    }


def stress_family(stress):
    if stress in MANAGEABLE_STRESSES:
        return "manageable"
    if stress in FRONTIER_STRESSES:
        return "frontier"
    if stress in HARSH_STRESSES:
        return "harsh"
    if stress in OOS_STRESSES:
        return "out_of_sample"
    return "unknown"


def phase2_raw_control(mode, x_obs, prev_u, t, stress, p):
    if mode == "no_control":
        return r2.old_raw_control("no_control", x_obs, prev_u, t, stress if stress in BASE_STRESSES else "nominal", p)

    if mode == "pump_radiator":
        return r2.old_raw_control("pump_radiator", x_obs, prev_u, t, stress if stress in BASE_STRESSES else "nominal", p)

    if mode == "a10_v1":
        return r2.old_raw_control("a10_hybrid", x_obs, prev_u, t, stress if stress in BASE_STRESSES else "nominal", p)

    if mode == "a10_full":
        return r2.raw_control_r2("a10_hybrid_v2", x_obs, prev_u, t, stress if stress in BASE_STRESSES else "nominal", p)

    if mode == "a10_no_valve":
        u = r2.raw_control_r2("a10_hybrid_v2", x_obs, prev_u, t, stress if stress in BASE_STRESSES else "nominal", p)
        u[1] = 0.34
        return u

    if mode == "a10_no_store":
        u = r2.raw_control_r2("a10_hybrid_v2", x_obs, prev_u, t, stress if stress in BASE_STRESSES else "nominal", p)
        u[3] = 0.0
        return u

    if mode == "a10_no_load":
        u = r2.raw_control_r2("a10_hybrid_v2", x_obs, prev_u, t, stress if stress in BASE_STRESSES else "nominal", p)
        u[4] = 1.0
        return u

    raise ValueError(f"Unknown mode: {mode}")


def apply_actuator_authority(u_raw, authority):
    """
    Degrade active thermal actuators around passive baselines.
    Load shaping is left intact because it is a demand-side control channel,
    not a cooling actuator.
    """
    passive = np.array([0.05, 0.25, 0.42, 0.00, 1.00], dtype=float)
    u = np.array(u_raw, dtype=float).copy()

    for j in range(4):
        u[j] = passive[j] + authority * (u[j] - passive[j])

    return u


def violation_terms(x, p):
    return base.violation_terms(x, p)


def is_unsafe(x, p):
    return base.is_unsafe(x, p)


def simulate_phase2(mode, stress, condition_name, seed, p, store_history=False):
    rng = np.random.default_rng(seed)
    mult = base.random_multipliers(rng)

    cfg = CONDITIONS[condition_name]
    delay_steps = int(round(cfg["sensor_delay"] / p.dt))
    authority = float(cfg["actuator_authority"])

    n = int(round(p.T / p.dt))
    x = base.initial_state(stress if stress in BASE_STRESSES else "combined_moderate")

    u_prev = np.array([0.05, 0.25, 0.42, 0.00, 1.00], dtype=float)

    x_buffer = [x.copy() for _ in range(delay_steps + 1)]

    V = 0.0
    unsafe_steps = 0
    finite_ok = True

    max_Tc = x[0]
    max_Tp = x[1]
    max_Tr = x[2]
    min_Es = x[3]
    min_Pm = x[4]
    max_G = x[5]

    if store_history:
        hist = {
            "t": [],
            "Tc": [],
            "Tp": [],
            "Tr": [],
            "Es": [],
            "Pm": [],
            "G": [],
            "Y": [],
            "pump": [],
            "valve": [],
            "rad": [],
            "store": [],
            "load": [],
            "Vinst": [],
        }
    else:
        hist = None

    for k in range(n):
        t = k * p.dt
        sp = phase2_stress_profile(stress, t, p)

        if delay_steps > 0:
            x_obs = x_buffer[0].copy()
        else:
            x_obs = x.copy()

        u_raw = phase2_raw_control(mode, x_obs, u_prev, t, stress, p)
        u_raw = apply_actuator_authority(u_raw, authority)
        u = base.apply_slew(u_raw, u_prev, p)

        pump, valve, rad_u, store_u, load_u = u
        Tc, Tp, Tr, Es, Pm, G, Y = x

        q_gen = (p.q_idle + p.q_mission * load_u) * sp["heat"] * mult["heat_scale"]

        q_cp = p.k_cp * mult["kcp_scale"] * (0.07 + 1.15 * pump) * (Tc - Tp)
        q_pr = p.k_pr * mult["kpr_scale"] * (0.05 + 1.20 * valve) * (Tp - Tr)

        storage_factor = base.clip((Es - p.Es_min) / max(1.0 - p.Es_min, 1e-9), 0.0, 1.0)
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

        ns = p.base_noise * mult["noise_scale"]
        noise = rng.normal(0.0, ns, size=3)

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
            base.clip(Es + p.dt * dEs, -0.20, 1.10),
            base.clip(Pm + p.dt * dPm, -0.25, 1.10),
            max(G + p.dt * dG, 0.0),
            Y + p.dt * dY,
        ], dtype=float)

        if not np.all(np.isfinite(x_next)):
            finite_ok = False
            break

        vt = violation_terms(x_next, p)
        Vinst = sum(vt.values())
        V += p.dt * Vinst

        if is_unsafe(x_next, p):
            unsafe_steps += 1

        max_Tc = max(max_Tc, x_next[0])
        max_Tp = max(max_Tp, x_next[1])
        max_Tr = max(max_Tr, x_next[2])
        min_Es = min(min_Es, x_next[3])
        min_Pm = min(min_Pm, x_next[4])
        max_G = max(max_G, x_next[5])

        if store_history:
            hist["t"].append(t)
            hist["Tc"].append(x_next[0])
            hist["Tp"].append(x_next[1])
            hist["Tr"].append(x_next[2])
            hist["Es"].append(x_next[3])
            hist["Pm"].append(x_next[4])
            hist["G"].append(x_next[5])
            hist["Y"].append(x_next[6])
            hist["pump"].append(u[0])
            hist["valve"].append(u[1])
            hist["rad"].append(u[2])
            hist["store"].append(u[3])
            hist["load"].append(u[4])
            hist["Vinst"].append(Vinst)

        x = x_next
        u_prev = u

        x_buffer.append(x.copy())
        if len(x_buffer) > delay_steps + 1:
            x_buffer.pop(0)

    Y_final = float(x[6])
    throughput_fail = Y_final < p.Y_min
    failure = (not finite_ok) or (unsafe_steps > 0) or throughput_fail

    rec = {
        "mode": mode,
        "stress": stress,
        "stress_family": stress_family(stress),
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
        "rad_scale": P_CANDIDATE["rad_scale"],
        "transport_scale": P_CANDIDATE["transport_scale"],
        "storage_scale": P_CANDIDATE["storage_scale"],
    }

    return rec, hist


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
    for (condition, stress_family, mode), g in df.groupby(["condition", "stress_family", "mode"]):
        rows.append({
            "condition": condition,
            "stress_family": stress_family,
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


def mode_row(agg, condition, family, mode):
    q = agg[
        (agg["condition"] == condition)
        & (agg["stress_family"] == family)
        & (agg["mode"] == mode)
    ]
    if len(q) == 0:
        return None
    return q.iloc[0]


def plot_phase2(agg):
    os.makedirs("figs", exist_ok=True)

    for family in ["manageable", "frontier", "out_of_sample", "harsh"]:
        view = agg[
            (agg["condition"] == "baseline")
            & (agg["stress_family"] == family)
        ].copy()
        if len(view) == 0:
            continue

        view = view.sort_values("failure_rate")
        fig = plt.figure(figsize=(11, 5))
        x = np.arange(len(view))
        plt.bar(x, view["failure_rate"].values)
        plt.xticks(x, view["mode"].values, rotation=30, ha="right")
        plt.ylabel("failure rate")
        plt.title(f"Phase 2 baseline failure rate: {family}")
        plt.tight_layout()
        fig.savefig(f"figs/phase2_baseline_failure_{family}.png", dpi=180)
        plt.close(fig)

        fig = plt.figure(figsize=(11, 5))
        x = np.arange(len(view))
        plt.bar(x, view["CVaR95_V"].values)
        plt.xticks(x, view["mode"].values, rotation=30, ha="right")
        plt.ylabel("CVaR0.95")
        plt.title(f"Phase 2 baseline CVaR0.95: {family}")
        plt.tight_layout()
        fig.savefig(f"figs/phase2_baseline_cvar95_{family}.png", dpi=180)
        plt.close(fig)

    # Condition robustness for a10_full.
    view = agg[
        (agg["mode"] == "a10_full")
        & (agg["stress_family"] == "manageable")
    ].copy()
    view = view.sort_values("condition")

    fig = plt.figure(figsize=(10, 5))
    x = np.arange(len(view))
    plt.bar(x, view["failure_rate"].values)
    plt.xticks(x, view["condition"].values, rotation=30, ha="right")
    plt.ylabel("manageable failure rate")
    plt.title("A10-Full robustness across delay/degradation conditions")
    plt.tight_layout()
    fig.savefig("figs/phase2_a10_full_condition_failure.png", dpi=180)
    plt.close(fig)


def write_report(agg, p, out_path, n):
    lines = []
    lines.append("A10-STMS Phase 2 Ablation and Out-of-Sample Validation Report")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Candidate resource point: rad_scale={P_CANDIDATE['rad_scale']}, "
                 f"transport_scale={P_CANDIDATE['transport_scale']}, "
                 f"storage_scale={P_CANDIDATE['storage_scale']}")
    lines.append(f"Monte Carlo samples per stress/mode/condition: {n}")
    lines.append("")

    baseline_manage = agg[
        (agg["condition"] == "baseline")
        & (agg["stress_family"] == "manageable")
    ].copy().sort_values(["failure_rate", "CVaR95_V"])

    baseline_frontier = agg[
        (agg["condition"] == "baseline")
        & (agg["stress_family"] == "frontier")
    ].copy().sort_values(["failure_rate", "CVaR95_V"])

    baseline_oos = agg[
        (agg["condition"] == "baseline")
        & (agg["stress_family"] == "out_of_sample")
    ].copy().sort_values(["failure_rate", "CVaR95_V"])

    baseline_harsh = agg[
        (agg["condition"] == "baseline")
        & (agg["stress_family"] == "harsh")
    ].copy().sort_values(["failure_rate", "CVaR95_V"])

    cols = [
        "mode",
        "n",
        "failure_rate",
        "CVaR95_V",
        "mean_unsafe_fraction",
        "mean_Y_final",
        "max_Tc_p95",
        "fail_Tc_rate",
        "fail_Tp_rate",
        "fail_G_rate",
        "fail_Y_rate",
    ]

    lines.append("Baseline / manageable stress family:")
    lines.append(baseline_manage[cols].to_string(index=False))
    lines.append("")

    lines.append("Baseline / frontier stress family:")
    lines.append(baseline_frontier[cols].to_string(index=False))
    lines.append("")

    lines.append("Baseline / out-of-sample stress family:")
    lines.append(baseline_oos[cols].to_string(index=False))
    lines.append("")

    lines.append("Baseline / harsh stress family:")
    lines.append(baseline_harsh[cols].to_string(index=False))
    lines.append("")

    # Main comparisons
    full_manage = mode_row(agg, "baseline", "manageable", "a10_full")
    pump_manage = mode_row(agg, "baseline", "manageable", "pump_radiator")
    v1_manage = mode_row(agg, "baseline", "manageable", "a10_v1")

    no_valve = mode_row(agg, "baseline", "manageable", "a10_no_valve")
    no_store = mode_row(agg, "baseline", "manageable", "a10_no_store")
    no_load = mode_row(agg, "baseline", "manageable", "a10_no_load")

    full_delay05 = mode_row(agg, "sensor_delay_0p5", "manageable", "a10_full")
    full_delay10 = mode_row(agg, "sensor_delay_1p0", "manageable", "a10_full")
    full_act08 = mode_row(agg, "actuator_0p8", "manageable", "a10_full")
    full_act06 = mode_row(agg, "actuator_0p6", "manageable", "a10_full")

    full_oos = mode_row(agg, "baseline", "out_of_sample", "a10_full")
    pump_oos = mode_row(agg, "baseline", "out_of_sample", "pump_radiator")

    baseline_pass = (
        full_manage is not None
        and pump_manage is not None
        and full_manage["failure_rate"] <= 0.10
        and full_manage["mean_unsafe_fraction"] <= 0.05
        and full_manage["mean_Y_final"] >= 0.80
        and full_manage["failure_rate"] < pump_manage["failure_rate"]
        and full_manage["CVaR95_V"] < pump_manage["CVaR95_V"]
    )

    ablation_worse_count = 0
    for r in [no_valve, no_store, no_load, v1_manage]:
        if r is None:
            continue
        if (
            r["failure_rate"] > full_manage["failure_rate"] + 0.05
            or r["CVaR95_V"] > 1.5 * max(full_manage["CVaR95_V"], 1e-12)
        ):
            ablation_worse_count += 1

    delay_degrade_pass = (
        full_delay05 is not None
        and full_act08 is not None
        and full_delay05["failure_rate"] <= 0.15
        and full_delay05["mean_Y_final"] >= 0.80
        and full_act08["failure_rate"] <= 0.15
        and full_act08["mean_Y_final"] >= 0.80
    )

    oos_damage_pass = (
        full_oos is not None
        and pump_oos is not None
        and full_oos["CVaR95_V"] < pump_oos["CVaR95_V"]
        and full_oos["mean_unsafe_fraction"] <= pump_oos["mean_unsafe_fraction"]
    )

    if baseline_pass and ablation_worse_count >= 2 and delay_degrade_pass and oos_damage_pass:
        status = "PASS-PHASE2-ROBUST-ABLATION-OOS"
    elif baseline_pass and ablation_worse_count >= 2:
        status = "PASS-PHASE2-BASELINE-ABLATION"
    elif baseline_pass:
        status = "PASS-PHASE2-BASELINE-ONLY"
    else:
        status = "NEEDS-TRIAGE-PHASE2"

    lines.append("Predeclared Phase 2 checks:")
    lines.append(f"  baseline_manageable_pass: {baseline_pass}")
    lines.append(f"  ablation_worse_count: {ablation_worse_count}")
    lines.append(f"  delay_degrade_pass: {delay_degrade_pass}")
    lines.append(f"  out_of_sample_damage_pass: {oos_damage_pass}")
    lines.append("")
    lines.append(f"Status: {status}")
    lines.append("")

    lines.append("A10-Full manageable robustness across delay/degradation:")
    cond_view = agg[
        (agg["mode"] == "a10_full")
        & (agg["stress_family"] == "manageable")
    ].copy().sort_values("condition")
    cond_cols = [
        "condition",
        "failure_rate",
        "CVaR95_V",
        "mean_unsafe_fraction",
        "mean_Y_final",
        "max_Tc_p95",
        "fail_Tc_rate",
        "fail_Tp_rate",
        "fail_Y_rate",
    ]
    lines.append(cond_view[cond_cols].to_string(index=False))
    lines.append("")

    lines.append("Interpretation guide:")
    lines.append("  PASS-PHASE2-ROBUST-ABLATION-OOS means the confirmed Phase 1R2C")
    lines.append("  candidate remains nontrivially useful under ablations, moderate")
    lines.append("  delay/degradation, and out-of-sample stress.")
    lines.append("  PASS-PHASE2-BASELINE-ABLATION means the architecture is meaningful,")
    lines.append("  but delay/degradation or OOS robustness still needs redesign.")
    lines.append("  NEEDS-TRIAGE means the Phase 1R2C success was too narrow.")
    lines.append("")

    lines.append("Claim boundary:")
    lines.append("  This remains a reduced nondimensional surrogate result.")
    lines.append("  It is not a spacecraft thermal-control validation, hardware design,")
    lines.append("  or proof of superiority over all conventional thermal architectures.")
    lines.append("")

    report = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    return status, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=32)
    ap.add_argument("--seed", type=int, default=515151)
    args = ap.parse_args()

    os.makedirs("outputs", exist_ok=True)
    os.makedirs("figs", exist_ok=True)

    p = make_candidate_params()
    root_rng = np.random.default_rng(args.seed)

    records = []

    total = len(CONDITIONS) * len(ALL_STRESSES) * len(MODES) * args.n
    done = 0

    for condition in CONDITIONS:
        for stress in ALL_STRESSES:
            for mode in MODES:
                for _ in range(args.n):
                    seed = int(root_rng.integers(0, 2**31 - 1))
                    rec, _ = simulate_phase2(mode, stress, condition, seed, p, store_history=False)
                    records.append(rec)

                    done += 1
                    if done % 3000 == 0:
                        print(f"Progress: {done}/{total}")

    df = pd.DataFrame(records)
    df = add_failure_reasons(df, p)

    agg = aggregate(df)

    df.to_csv("outputs/phase2_runs.csv", index=False)
    agg.to_csv("outputs/phase2_by_family_condition_mode.csv", index=False)

    plot_phase2(agg)

    status, report = write_report(
        agg,
        p,
        "outputs/phase2_lock_report.txt",
        args.n,
    )

    print(report)
    print("")
    print("Wrote:")
    print("  outputs/phase2_runs.csv")
    print("  outputs/phase2_by_family_condition_mode.csv")
    print("  outputs/phase2_lock_report.txt")
    print("  figs/phase2_*.png")


if __name__ == "__main__":
    main()
