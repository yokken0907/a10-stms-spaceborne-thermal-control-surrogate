#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A10-STMS Phase 1
Minimal reduced thermal surrogate for spaceborne industrial cooling.

Scope:
- This is not a spacecraft thermal-design tool.
- This is not a hardware prescription.
- This is a closed nondimensional surrogate for testing control architecture,
  safe-set preservation, tail risk, storage depletion, power margin, and
  mission throughput under stress.

Controllers:
- No Control
- Pump Only
- Radiator Only
- Load Throttle
- Pump + Radiator
- A10 Hybrid

Outputs:
- outputs/phase1_runs.csv
- outputs/phase1_by_mode.csv
- outputs/phase1_by_stress_mode.csv
- outputs/phase1_lock_report.txt
- figs/*.png
"""

import argparse
import os
import math
from dataclasses import dataclass
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# Utilities
# -----------------------------

def clip(x, lo, hi):
    return float(np.minimum(np.maximum(x, lo), hi))


def pos(x):
    return float(max(x, 0.0))


def cvar(values, beta=0.95):
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return np.nan
    q = np.quantile(arr, beta)
    tail = arr[arr >= q]
    if len(tail) == 0:
        return float(q)
    return float(np.mean(tail))


def smooth_gate(z):
    """
    Smooth clipped gate.
    z <= 0 -> 0
    z >= 1 -> 1
    0 < z < 1 -> smoothstep
    """
    z = clip(z, 0.0, 1.0)
    return z * z * (3.0 - 2.0 * z)


# -----------------------------
# Parameters
# -----------------------------

@dataclass
class Params:
    T: float = 24.0
    dt: float = 0.02

    # Thermal capacities, nondimensional
    Cc: float = 1.00
    Cp: float = 0.75
    Cr: float = 1.35

    # Couplings
    k_cp: float = 0.92
    k_pr: float = 0.70
    k_store: float = 0.62
    k_rad: float = 0.58
    k_es: float = 0.16
    k_es_recover: float = 0.06

    # Power dynamics
    k_pm: float = 0.050
    P_base: float = 0.34
    c_pump: float = 0.24
    c_rad: float = 0.18
    c_valve: float = 0.018
    c_store: float = 0.055

    # Heat generation
    q_idle: float = 0.28
    q_mission: float = 0.74

    # Temperature scales
    T_space: float = 0.05
    T_store: float = 0.28

    # Safety thresholds
    Tc_max: float = 1.00
    Tp_max: float = 0.92
    Tr_max: float = 0.86
    Es_min: float = 0.12
    Pm_min: float = 0.12
    G_max: float = 1.00
    Y_min: float = 0.80

    # Warning thresholds
    Tc_warn: float = 0.78
    Tp_warn: float = 0.70
    Tr_warn: float = 0.67
    Es_warn: float = 0.36
    Pm_warn: float = 0.34
    G_warn: float = 0.72

    # Control limits and slew rates
    du_rate: float = 3.2
    dload_rate: float = 4.8

    # Radiation
    eps_min: float = 0.22
    eps_max: float = 1.00

    # Gradient-risk relaxation
    tau_g: float = 0.55

    # Noise
    base_noise: float = 0.0025


STRESSES = [
    "nominal",
    "burst_heat",
    "eclipse_transition",
    "solar_heating",
    "radiator_degradation",
    "power_shortage",
    "storage_saturation",
    "combined_moderate",
    "combined_harsh",
]

MODES = [
    "no_control",
    "pump_only",
    "radiator_only",
    "load_throttle",
    "pump_radiator",
    "a10_hybrid",
]


# -----------------------------
# Stress model
# -----------------------------

def stress_profile(stress, t, p: Params):
    """
    Returns deterministic stress multipliers at time t.
    """
    heat = 1.0
    sun = 0.035
    rad_eff = 1.0
    pin = 1.0
    storage_recovery = 1.0

    # Reusable time windows
    mid_burst = 1.0 if (0.42 * p.T <= t <= 0.58 * p.T) else 0.0
    early_burst = 1.0 if (0.18 * p.T <= t <= 0.27 * p.T) else 0.0
    late_burst = 1.0 if (0.70 * p.T <= t <= 0.78 * p.T) else 0.0
    eclipse = 1.0 if (0.36 * p.T <= t <= 0.66 * p.T) else 0.0

    if stress == "nominal":
        pass

    elif stress == "burst_heat":
        heat = 1.0 + 1.25 * mid_burst + 0.55 * early_burst

    elif stress == "eclipse_transition":
        pin = 1.0 - 0.48 * eclipse
        sun = 0.020 * (1.0 - eclipse)

    elif stress == "solar_heating":
        sun = 0.115 + 0.035 * math.sin(2.0 * math.pi * t / p.T)
        rad_eff = 0.90

    elif stress == "radiator_degradation":
        rad_eff = 0.57
        sun = 0.055

    elif stress == "power_shortage":
        pin = 0.58
        heat = 1.05

    elif stress == "storage_saturation":
        heat = 1.0 + 0.95 * mid_burst
        storage_recovery = 0.48

    elif stress == "combined_moderate":
        heat = 1.10 + 0.90 * mid_burst + 0.42 * late_burst
        sun = 0.085
        rad_eff = 0.72
        pin = 0.76
        storage_recovery = 0.70

    elif stress == "combined_harsh":
        heat = 1.20 + 1.35 * mid_burst + 0.70 * early_burst + 0.60 * late_burst
        sun = 0.125
        rad_eff = 0.55
        pin = 0.60
        storage_recovery = 0.52

    else:
        raise ValueError(f"Unknown stress: {stress}")

    return {
        "heat": heat,
        "sun": sun,
        "rad_eff": rad_eff,
        "pin": pin,
        "storage_recovery": storage_recovery,
    }


def random_multipliers(rng):
    """
    Scenario-to-scenario uncertainty.
    """
    return {
        "heat_scale": float(rng.lognormal(mean=0.0, sigma=0.08)),
        "kcp_scale": float(rng.lognormal(mean=0.0, sigma=0.06)),
        "kpr_scale": float(rng.lognormal(mean=0.0, sigma=0.06)),
        "krad_scale": float(rng.lognormal(mean=0.0, sigma=0.10)),
        "power_scale": float(rng.lognormal(mean=0.0, sigma=0.07)),
        "noise_scale": float(rng.uniform(0.65, 1.35)),
    }


# -----------------------------
# Controller logic
# -----------------------------

def risks(x, p: Params):
    Tc, Tp, Tr, Es, Pm, G, Y = x

    BTc = (Tc - p.Tc_warn) / max(p.Tc_max - p.Tc_warn, 1e-9)
    BTp = (Tp - p.Tp_warn) / max(p.Tp_max - p.Tp_warn, 1e-9)
    BTr = (Tr - p.Tr_warn) / max(p.Tr_max - p.Tr_warn, 1e-9)
    BS = (p.Es_warn - Es) / max(p.Es_warn - p.Es_min, 1e-9)
    BP = (p.Pm_warn - Pm) / max(p.Pm_warn - p.Pm_min, 1e-9)
    BG = (G - p.G_warn) / max(p.G_max - p.G_warn, 1e-9)

    return {
        "BTc": smooth_gate(BTc),
        "BTp": smooth_gate(BTp),
        "BTr": smooth_gate(BTr),
        "BT": smooth_gate(max(BTc, BTp, 0.70 * BTr)),
        "BR": smooth_gate(max(BTr, 0.35 * BTc)),
        "BS": smooth_gate(BS),
        "BP": smooth_gate(BP),
        "BG": smooth_gate(BG),
    }


def raw_control(mode, x, prev_u, t, stress, p: Params):
    r = risks(x, p)
    BT = r["BT"]
    BR = r["BR"]
    BS = r["BS"]
    BP = r["BP"]
    BG = r["BG"]

    # u = pump, valve, rad, store, load
    if mode == "no_control":
        return np.array([0.05, 0.25, 0.42, 0.00, 1.00], dtype=float)

    if mode == "pump_only":
        pump = 0.08 + 0.90 * BT
        return np.array([pump, 0.30, 0.45, 0.00, 1.00], dtype=float)

    if mode == "radiator_only":
        rad = 0.28 + 0.72 * max(BR, 0.45 * BT)
        return np.array([0.08, 0.30, rad, 0.00, 1.00], dtype=float)

    if mode == "load_throttle":
        load = 1.00 - 0.45 * BT - 0.35 * BP - 0.30 * BS
        return np.array([0.08, 0.30, 0.45, 0.00, clip(load, 0.38, 1.00)], dtype=float)

    if mode == "pump_radiator":
        pump = 0.08 + 0.80 * BT * (1.0 - 0.30 * BP)
        rad = 0.30 + 0.70 * max(BR, 0.65 * BT) * (1.0 - 0.18 * BP)
        return np.array([pump, 0.38, rad, 0.00, 1.00], dtype=float)

    if mode == "a10_hybrid":
        # Separated-barrier hybrid logic.
        # Temperature risk triggers transport, radiation, and storage.
        # Storage risk suppresses further storage use and pushes heat toward radiator/load-shaping.
        # Power risk prevents blindly maxing active cooling.
        # Gradient risk softens aggressive heat-transfer actions.
        resource_ok = (1.0 - 0.62 * BP)
        gradient_ok = (1.0 - 0.48 * BG)
        storage_ok = (1.0 - 0.75 * BS)

        pump = 0.10 + 0.72 * BT * resource_ok * gradient_ok + 0.12 * BR
        valve = 0.24 + 0.50 * BT * gradient_ok + 0.20 * BS
        rad = 0.34 + 0.55 * max(BR, 0.70 * BT) + 0.18 * BS - 0.16 * BP
        store = 0.04 + 0.62 * BT * storage_ok * gradient_ok

        # Demand shaping only when the thermal/storage/power barrier says so.
        load = 1.00 - 0.22 * BT - 0.34 * BP - 0.30 * BS - 0.12 * BG

        return np.array([
            clip(pump, 0.02, 1.00),
            clip(valve, 0.05, 1.00),
            clip(rad, 0.10, 1.00),
            clip(store, 0.00, 1.00),
            clip(load, 0.45, 1.00),
        ], dtype=float)

    raise ValueError(f"Unknown mode: {mode}")


def apply_slew(u_raw, u_prev, p: Params):
    u = np.array(u_raw, dtype=float).copy()
    out = u_prev.copy()

    for i in range(4):
        max_du = p.du_rate * p.dt
        out[i] = clip(u_prev[i] + clip(u[i] - u_prev[i], -max_du, max_du), 0.0, 1.0)

    max_dl = p.dload_rate * p.dt
    out[4] = clip(u_prev[4] + clip(u[4] - u_prev[4], -max_dl, max_dl), 0.0, 1.0)

    return out


# -----------------------------
# Simulation
# -----------------------------

def initial_state(stress):
    Tc = 0.36
    Tp = 0.33
    Tr = 0.31
    Es = 0.86
    Pm = 0.84
    G = 0.08
    Y = 0.0

    if stress == "storage_saturation":
        Es = 0.46
    if stress == "combined_moderate":
        Es = 0.72
        Pm = 0.72
    if stress == "combined_harsh":
        Es = 0.62
        Pm = 0.65

    return np.array([Tc, Tp, Tr, Es, Pm, G, Y], dtype=float)


def violation_terms(x, p: Params):
    Tc, Tp, Tr, Es, Pm, G, Y = x
    return {
        "Tc": pos(Tc - p.Tc_max) ** 2,
        "Tp": pos(Tp - p.Tp_max) ** 2,
        "Tr": pos(Tr - p.Tr_max) ** 2,
        "Es": pos(p.Es_min - Es) ** 2,
        "Pm": pos(p.Pm_min - Pm) ** 2,
        "G": pos(G - p.G_max) ** 2,
    }


def is_unsafe(x, p: Params):
    vt = violation_terms(x, p)
    return any(v > 0.0 for v in vt.values())


def simulate(mode, stress, seed, p: Params, store_history=False):
    rng = np.random.default_rng(seed)
    mult = random_multipliers(rng)

    n = int(round(p.T / p.dt))
    x = initial_state(stress)

    # Passive starting control.
    u_prev = np.array([0.05, 0.25, 0.42, 0.00, 1.00], dtype=float)

    V = 0.0
    unsafe_steps = 0
    max_Tc = x[0]
    max_Tp = x[1]
    max_Tr = x[2]
    min_Es = x[3]
    min_Pm = x[4]
    max_G = x[5]
    finite_ok = True

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
        sp = stress_profile(stress, t, p)

        u_raw = raw_control(mode, x, u_prev, t, stress, p)
        u = apply_slew(u_raw, u_prev, p)

        pump, valve, rad_u, store_u, load_u = u

        Tc, Tp, Tr, Es, Pm, G, Y = x

        # Mission heat generation.
        q_gen = (p.q_idle + p.q_mission * load_u) * sp["heat"] * mult["heat_scale"]

        # Thermal transport.
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

        # Power margin dynamics.
        cooling_power = (
            p.P_base
            + p.c_pump * pump**2
            + p.c_rad * rad_u**2
            + p.c_store * store_u**2
            + p.c_valve * abs(valve - u_prev[1]) / max(p.dt, 1e-9)
        )
        pin = sp["pin"] * mult["power_scale"]

        # Gradient risk.
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

        # Noise.
        ns = p.base_noise * mult["noise_scale"]
        noise = rng.normal(0.0, ns, size=3)

        # ODE update.
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

    Y_final = float(x[6])
    throughput_fail = Y_final < p.Y_min

    failure = (not finite_ok) or (unsafe_steps > 0) or throughput_fail

    result = {
        "mode": mode,
        "stress": stress,
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

    return result, hist


# -----------------------------
# Aggregation and plotting
# -----------------------------

def aggregate(df):
    rows = []
    for mode, g in df.groupby("mode"):
        rows.append({
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
            "max_Tc_p95": float(np.quantile(g["max_Tc"], 0.95)),
            "min_Es_p05": float(np.quantile(g["min_Es"], 0.05)),
            "min_Pm_p05": float(np.quantile(g["min_Pm"], 0.05)),
            "mean_Y_final": float(g["Y_final"].mean()),
        })
    out = pd.DataFrame(rows)
    return out.sort_values(["failure_rate", "CVaR95_V", "mean_unsafe_fraction"])


def aggregate_stress_mode(df):
    rows = []
    for (stress, mode), g in df.groupby(["stress", "mode"]):
        rows.append({
            "stress": stress,
            "mode": mode,
            "n": len(g),
            "finite_rate": float(g["finite_ok"].mean()),
            "failure_rate": float(g["failure"].mean()),
            "mean_V": float(g["V"].mean()),
            "CVaR90_V": cvar(g["V"], 0.90),
            "CVaR95_V": cvar(g["V"], 0.95),
            "mean_unsafe_fraction": float(g["unsafe_fraction"].mean()),
            "max_Tc_p95": float(np.quantile(g["max_Tc"], 0.95)),
            "min_Es_p05": float(np.quantile(g["min_Es"], 0.05)),
            "min_Pm_p05": float(np.quantile(g["min_Pm"], 0.05)),
            "mean_Y_final": float(g["Y_final"].mean()),
        })
    return pd.DataFrame(rows).sort_values(["stress", "failure_rate", "CVaR95_V"])


def plot_bar(df_mode, col, ylabel, path):
    fig = plt.figure(figsize=(10, 5))
    x = np.arange(len(df_mode))
    plt.bar(x, df_mode[col].values)
    plt.xticks(x, df_mode["mode"].values, rotation=30, ha="right")
    plt.ylabel(ylabel)
    plt.title(ylabel + " by controller")
    plt.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_example_histories(p, out_dir):
    stress = "combined_moderate"
    seed = 777

    fig = plt.figure(figsize=(11, 6))
    for mode in MODES:
        _, hist = simulate(mode, stress, seed, p, store_history=True)
        plt.plot(hist["t"], hist["Tc"], label=mode)
    plt.axhline(p.Tc_max, linestyle="--", linewidth=1.0)
    plt.xlabel("time")
    plt.ylabel("core temperature Tc")
    plt.title("Example trajectory: core temperature under combined_moderate")
    plt.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, "example_Tc_combined_moderate.png"), dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(11, 6))
    for mode in MODES:
        _, hist = simulate(mode, stress, seed, p, store_history=True)
        plt.plot(hist["t"], hist["Pm"], label=mode)
    plt.axhline(p.Pm_min, linestyle="--", linewidth=1.0)
    plt.xlabel("time")
    plt.ylabel("power margin Pm")
    plt.title("Example trajectory: power margin under combined_moderate")
    plt.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, "example_Pm_combined_moderate.png"), dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(11, 6))
    for mode in MODES:
        _, hist = simulate(mode, stress, seed, p, store_history=True)
        plt.plot(hist["t"], hist["Y"], label=mode)
    plt.axhline(p.Y_min, linestyle="--", linewidth=1.0)
    plt.xlabel("time")
    plt.ylabel("mission throughput Y")
    plt.title("Example trajectory: mission throughput under combined_moderate")
    plt.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, "example_Y_combined_moderate.png"), dpi=180)
    plt.close(fig)

    # A10 hybrid controls.
    _, hist = simulate("a10_hybrid", stress, seed, p, store_history=True)
    fig = plt.figure(figsize=(11, 6))
    for key in ["pump", "valve", "rad", "store", "load"]:
        plt.plot(hist["t"], hist[key], label=key)
    plt.xlabel("time")
    plt.ylabel("control")
    plt.title("A10-Hybrid separated-barrier control actions")
    plt.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, "a10_hybrid_controls_combined_moderate.png"), dpi=180)
    plt.close(fig)


def lock_report(df, by_mode, by_stress, p, out_path):
    finite_pass = bool(df["finite_ok"].all())

    # No Control should fail under at least one severe stress;
    # otherwise the benchmark is too easy.
    nc = by_stress[by_stress["mode"] == "no_control"]
    nc_severe = nc[nc["stress"].isin(["combined_moderate", "combined_harsh", "radiator_degradation"])]
    no_control_fail_check = bool((nc_severe["failure_rate"] > 0.10).any())

    a10 = by_mode[by_mode["mode"] == "a10_hybrid"].iloc[0]
    min_failure = float(by_mode["failure_rate"].min())
    min_cvar95 = float(by_mode["CVaR95_V"].min())
    min_unsafe = float(by_mode["mean_unsafe_fraction"].min())

    a10_best_failure = bool(a10["failure_rate"] <= min_failure + 1e-12)
    a10_best_cvar = bool(a10["CVaR95_V"] <= min_cvar95 + 1e-12)
    a10_best_unsafe = bool(a10["mean_unsafe_fraction"] <= min_unsafe + 1e-12)

    advantage = a10_best_failure or a10_best_cvar or a10_best_unsafe

    if finite_pass and no_control_fail_check and advantage:
        status = "PASS-PHASE1-CANDIDATE"
    elif finite_pass and no_control_fail_check:
        status = "NEEDS-TRIAGE-A10-NOT-BEST"
    elif finite_pass:
        status = "NEEDS-TRIAGE-BENCHMARK-TOO-EASY"
    else:
        status = "FAIL-NONFINITE"

    lines = []
    lines.append("A10-STMS Phase 1 Lock Report")
    lines.append("=" * 72)
    lines.append(f"Status: {status}")
    lines.append("")
    lines.append("Predeclared checks:")
    lines.append(f"  finite_pass: {finite_pass}")
    lines.append(f"  no_control_fail_check: {no_control_fail_check}")
    lines.append(f"  a10_best_failure: {a10_best_failure}")
    lines.append(f"  a10_best_CVaR95: {a10_best_cvar}")
    lines.append(f"  a10_best_unsafe_duration: {a10_best_unsafe}")
    lines.append("")
    lines.append("A10-Hybrid aggregate:")
    for key in [
        "failure_rate",
        "CVaR90_V",
        "CVaR95_V",
        "mean_unsafe_fraction",
        "max_Tc_p95",
        "min_Es_p05",
        "min_Pm_p05",
        "mean_Y_final",
    ]:
        lines.append(f"  {key}: {float(a10[key]):.8g}")

    lines.append("")
    lines.append("Best modes by metric:")
    for key in ["failure_rate", "CVaR95_V", "mean_unsafe_fraction", "mean_Y_final"]:
        if key == "mean_Y_final":
            row = by_mode.sort_values(key, ascending=False).iloc[0]
            lines.append(f"  max {key}: {row['mode']} = {float(row[key]):.8g}")
        else:
            row = by_mode.sort_values(key, ascending=True).iloc[0]
            lines.append(f"  min {key}: {row['mode']} = {float(row[key]):.8g}")

    lines.append("")
    lines.append("Claim boundary:")
    lines.append("  This result is a nondimensional reduced-surrogate audit only.")
    lines.append("  It is not a spacecraft hardware design, not a thermal-vacuum validation,")
    lines.append("  and not evidence that A10-STMS exceeds radiative thermal limits.")
    lines.append("")
    lines.append("Interpretation guide:")
    lines.append("  PASS-PHASE1-CANDIDATE means the separated-barrier hybrid architecture")
    lines.append("  deserves Phase 2 stress/resource-frontier testing.")
    lines.append("  NEEDS-TRIAGE-A10-NOT-BEST is still scientifically useful: it identifies")
    lines.append("  whether the regime is simple-pump-feasible, radiator-limited,")
    lines.append("  power-limited, storage-limited, or badly tuned.")
    lines.append("")

    report = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    return status, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=48, help="Monte Carlo samples per stress/mode")
    ap.add_argument("--seed", type=int, default=12345)
    args = ap.parse_args()

    p = Params()

    os.makedirs("outputs", exist_ok=True)
    os.makedirs("figs", exist_ok=True)

    records = []
    root_rng = np.random.default_rng(args.seed)

    for stress in STRESSES:
        for mode in MODES:
            for i in range(args.n):
                seed = int(root_rng.integers(0, 2**31 - 1))
                rec, _ = simulate(mode, stress, seed, p, store_history=False)
                records.append(rec)

    df = pd.DataFrame(records)
    by_mode = aggregate(df)
    by_stress = aggregate_stress_mode(df)

    df.to_csv("outputs/phase1_runs.csv", index=False)
    by_mode.to_csv("outputs/phase1_by_mode.csv", index=False)
    by_stress.to_csv("outputs/phase1_by_stress_mode.csv", index=False)

    plot_bar(by_mode, "failure_rate", "Failure rate", "figs/failure_rate_by_mode.png")
    plot_bar(by_mode, "CVaR95_V", "CVaR0.95 of violation integral", "figs/cvar95_by_mode.png")
    plot_bar(by_mode, "mean_unsafe_fraction", "Mean unsafe duration fraction", "figs/unsafe_duration_by_mode.png")
    plot_bar(by_mode, "mean_Y_final", "Mean mission throughput", "figs/mission_throughput_by_mode.png")
    plot_example_histories(p, "figs")

    status, report = lock_report(
        df,
        by_mode,
        by_stress,
        p,
        "outputs/phase1_lock_report.txt",
    )

    print(report)
    print("\nAggregate by mode:")
    print(by_mode.to_string(index=False))
    print("\nWrote:")
    print("  outputs/phase1_runs.csv")
    print("  outputs/phase1_by_mode.csv")
    print("  outputs/phase1_by_stress_mode.csv")
    print("  outputs/phase1_lock_report.txt")
    print("  figs/*.png")


if __name__ == "__main__":
    main()
