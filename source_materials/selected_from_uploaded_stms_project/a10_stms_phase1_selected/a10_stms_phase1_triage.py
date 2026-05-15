#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from a10_stms_phase1 import Params

p = Params()

df = pd.read_csv("outputs/phase1_runs.csv")

df["fail_Tc"] = df["max_Tc"] > p.Tc_max
df["fail_Tp"] = df["max_Tp"] > p.Tp_max
df["fail_Tr"] = df["max_Tr"] > p.Tr_max
df["fail_Es"] = df["min_Es"] < p.Es_min
df["fail_Pm"] = df["min_Pm"] < p.Pm_min
df["fail_G"]  = df["max_G"] > p.G_max
df["fail_Y"]  = df["Y_final"] < p.Y_min

reason_cols = ["fail_Tc","fail_Tp","fail_Tr","fail_Es","fail_Pm","fail_G","fail_Y"]

by_mode = (
    df.groupby("mode")[reason_cols + ["failure","V","unsafe_fraction","Y_final","max_Tc","min_Es","min_Pm"]]
    .agg({
        "fail_Tc":"mean",
        "fail_Tp":"mean",
        "fail_Tr":"mean",
        "fail_Es":"mean",
        "fail_Pm":"mean",
        "fail_G":"mean",
        "fail_Y":"mean",
        "failure":"mean",
        "V":["mean","median"],
        "unsafe_fraction":"mean",
        "Y_final":"mean",
        "max_Tc":["mean","median","max"],
        "min_Es":["mean","min"],
        "min_Pm":["mean","min"],
    })
)

by_mode.columns = ["_".join(c).strip("_") for c in by_mode.columns]
by_mode = by_mode.reset_index()

by_stress_mode = (
    df.groupby(["stress","mode"])[reason_cols + ["failure","V","unsafe_fraction","Y_final","max_Tc","min_Es","min_Pm"]]
    .agg({
        "fail_Tc":"mean",
        "fail_Tp":"mean",
        "fail_Tr":"mean",
        "fail_Es":"mean",
        "fail_Pm":"mean",
        "fail_G":"mean",
        "fail_Y":"mean",
        "failure":"mean",
        "V":["mean","median"],
        "unsafe_fraction":"mean",
        "Y_final":"mean",
        "max_Tc":["mean","median","max"],
        "min_Es":["mean","min"],
        "min_Pm":["mean","min"],
    })
)

by_stress_mode.columns = ["_".join(c).strip("_") for c in by_stress_mode.columns]
by_stress_mode = by_stress_mode.reset_index()

by_mode.to_csv("outputs/phase1_triage_by_mode.csv", index=False)
by_stress_mode.to_csv("outputs/phase1_triage_by_stress_mode.csv", index=False)

lines = []
lines.append("A10-STMS Phase 1T Failure-Reason Triage")
lines.append("=" * 72)
lines.append("")
lines.append("Interpretation:")
lines.append("  fail_Tc/Tp/Tr = thermal ceiling violation rate")
lines.append("  fail_Es       = storage depletion violation rate")
lines.append("  fail_Pm       = power-margin depletion violation rate")
lines.append("  fail_G        = gradient-risk violation rate")
lines.append("  fail_Y        = mission-throughput shortfall rate")
lines.append("")
lines.append("By mode:")
lines.append(by_mode.to_string(index=False))
lines.append("")
lines.append("A10-Hybrid by stress:")
lines.append(
    by_stress_mode[by_stress_mode["mode"] == "a10_hybrid"].to_string(index=False)
)
lines.append("")
lines.append("Most important diagnostic:")
lines.append("  If fail_Tc is near 1.0 while fail_Es and fail_Pm are near 0, the case is radiator/heat-transport limited.")
lines.append("  If fail_Y is near 1.0 for A10-Hybrid, the controller is preserving thermal margin by sacrificing mission throughput.")
lines.append("  If all modes fail_Tc even in nominal stress, the surrogate is too severe and requires calibrated Phase 1R.")
lines.append("")

report = "\n".join(lines)

with open("outputs/phase1_triage_report.txt", "w", encoding="utf-8") as f:
    f.write(report)

print(report)
print("")
print("Wrote:")
print("  outputs/phase1_triage_by_mode.csv")
print("  outputs/phase1_triage_by_stress_mode.csv")
print("  outputs/phase1_triage_report.txt")
