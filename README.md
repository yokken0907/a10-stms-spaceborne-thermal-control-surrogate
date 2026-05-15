# A10-STMS Spaceborne Thermal-Control Surrogate

This repository accompanies the AI-assisted independent research manuscript:

**A10-STMS: A Reduced-Surrogate Audit of Mission-Variable-Preserving Hybrid Thermal Control for Spaceborne Industrial Systems under Radiative, Storage, Power, Delay, and Actuator Constraints**

Author: Keiji Yoshimura, Independent Researcher  
Status: GitHub-ready paper companion archive v0.1.1-public-gate

## Simple Japanese classification title

**宇宙機・高負荷産業機器の熱制御／冷却サロゲート**

## Scope

A10-STMS is a nondimensional reduced-surrogate audit of hybrid thermal control for spaceborne industrial systems. It studies whether separated-barrier hybrid control can preserve thermal safety and mission throughput under radiative, storage, power, sensing-delay, and actuator-authority constraints.

The objective is not to propose a new heat-transfer mechanism, spacecraft hardware design, or flight-ready thermal-control system.

## Central interpretation

A10-STMS is best interpreted as a **feasibility-diagnostic reduced-control architecture**. It diagnoses when thermal-control failure is due to insufficient resources, missing routing/storage/load-shaping structure, delayed sensing, actuator degradation, or harsh combined stress.

## Technical Visual Orientation

For technically interested first-time readers, this repository includes a browser-only technical visual orientation page:

`docs/technical_visual_orientation/index.html`

This page provides a structured overview of A10-STMS, including the project mission variable, reduced-model or surrogate status, structured-prior / constrained-evaluation logic, uncertainty and stress discipline where applicable, evidence hierarchy, recommended repository reading order, and the claim boundary.

The page is intended only as an orientation aid. It does not execute simulations, does not validate the project, does not certify deployment readiness, and does not replace the manuscript, source/configuration materials, supporting archive materials, or independent expert review.

## What this repository contains

- manuscript PDF,
- Japanese and English README files,
- claim boundary and limitations,
- AI-assistance disclosure,
- practical positioning sheet,
- selected scripts, figures, and small CSV files from the uploaded A10-STMS archive,
- compact result-summary CSVs reconstructed from the paper,
- inventory of large raw outputs and compressed phase-output archives excluded from the GitHub body.

## What this repository does not claim

This repository does **not** claim:

- spacecraft-ready thermal control,
- thermal-vacuum validation,
- new heat-transfer physics,
- spacecraft hardware design,
- flight-controller readiness,
- superiority over existing spacecraft thermal-control architectures,
- formal control-barrier-function guarantees.

## Repository status

This is a paper companion archive, not a certified spacecraft thermal-control technology and not a full one-command reproduction package for every raw phase-output archive.

## PUBLIC-GATE-0 status

Decision: `PASS-WITH-MINOR-PUBLICATION-FIXES-A10-STMS-PUBLIC-GATE-0`  
Public version: `v0.1.1-public-gate`  
Classification: 宇宙機・高負荷産業機器の熱制御／冷却サロゲート

This repository is a public-gate copy reviewed under an A10 Evidence-Lock Protocol style gate. The gate fixes the claim boundary, non-claims, manifest policy, and GitHub/Zenodo/Jxiv publication posture.


## Zenodo-safe citation metadata

The active root `CITATION.cff` file is intentionally omitted from this pre-DOI public-gate package to avoid metadata-validation conflicts during Zenodo archival.

Draft citation metadata is preserved at:

`docs/citation_metadata/CITATION_DRAFT_pre_doi.cff`

After Zenodo DOI assignment, DOI metadata should be added to the README, manuscript metadata, and citation files in a follow-up DOI-metadata release.
