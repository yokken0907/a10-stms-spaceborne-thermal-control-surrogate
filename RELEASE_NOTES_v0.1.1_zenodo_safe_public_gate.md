# A10-STMS Spaceborne Thermal-Control Surrogate v0.1.1-zenodo-safe-public-gate

This is a Zenodo-safe public-gate release package for the A10-STMS spaceborne/industrial thermal-control surrogate study.

## Scope

This release provides a reproducibility-oriented public archive for A10-STMS, a nondimensional reduced-surrogate audit of mission-variable-preserving hybrid thermal control under radiative, storage, power, delay, actuator-authority, and combined-stress constraints.

A10-STMS is not a spacecraft hardware design, not a thermal-vacuum-validated technology, not a flight-ready controller, and not a certified aerospace thermal-control system.

## Included materials

- Manuscript PDF and submission metadata
- README and Japanese README
- Claim-boundary and limitation documents
- AI-assistance disclosure
- Practical positioning and publication strategy materials
- Selected scripts, figures, and compact CSV outputs
- Result-summary JSON/CSV files
- Public-gate audit materials
- File manifest with SHA-256 hashes
- Inventory of large raw outputs excluded from the GitHub body

## Claim boundary

This release supports the limited claim that A10-STMS is a nondimensional reduced-surrogate audit of mission-variable-preserving hybrid thermal control for spaceborne/industrial thermal-control motifs.

It does not claim:

- spacecraft-ready thermal control;
- thermal-vacuum validation;
- new heat-transfer physics;
- spacecraft hardware design;
- flight-controller readiness;
- superiority over existing spacecraft thermal-control architectures;
- formal control-barrier-function guarantees;
- mission feasibility for unresolved harsh combined stress.

## Zenodo-safe metadata fix

The active root `CITATION.cff` file has been intentionally omitted from this release to avoid pre-DOI metadata-validation conflicts during Zenodo archival.

Draft citation metadata is preserved at:

`docs/citation_metadata/CITATION_DRAFT_pre_doi.cff`

After Zenodo DOI assignment, DOI metadata should be added to README, manuscript metadata, and citation files in a follow-up DOI-metadata release.

## Integrity check

The checkfix package was verified before release.

- Manifest verification: PASS
- JSON parse: PASS
- Draft CFF YAML parse: PASS
- Root CITATION.cff: intentionally omitted
- Root LICENSE: present
- Git-ignore included-file conflict: 0
- Large files over 100 MB: none detected
- Compiled binaries: none detected
- AI assistance disclosure: present
- Claim-boundary documents: present

## Suggested tag

`v0.1.1-zenodo-safe-public-gate`
