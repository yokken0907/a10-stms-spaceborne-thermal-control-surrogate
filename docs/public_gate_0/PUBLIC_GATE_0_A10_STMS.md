# PUBLIC-GATE-0: A10-STMS

Decision: `PASS-WITH-MINOR-PUBLICATION-FIXES-A10-STMS-PUBLIC-GATE-0`

Repository: `a10-stms-spaceborne-thermal-control-surrogate`  
Public version: `v0.1.1-public-gate`  
Date: 2026-05-07  
Classification: 宇宙機・高負荷産業機器の熱制御／冷却サロゲート

## Allowed public description

A dimensionless reduced-surrogate audit of mission-variable-preserving hybrid thermal control for spaceborne/industrial thermal-control motifs.

## Allowed Japanese public description

宇宙機・高負荷産業機器を想定した無次元低次元サロゲート上のmission-variable-preserving hybrid thermal-control監査。

## Forbidden / unauthorized claims

- spacecraft implemented cooling technology
- thermal-vacuum tested technology
- flight controller
- certified aerospace safety system
- mission-feasible claim for unresolved harsh combined stress

## Publication posture

| Target | Gate posture |
|---|---|
| GitHub | GO after URL replacement. |
| Zenodo | GO after GitHub release. |
| Jxiv | CONDITIONAL; explicitly exclude harsh combined stress from mission-feasible claims. |

## Manifest / integrity posture

- Manifest policy: manifest-excluding-self
- Manifest entries verified: 111
- Manifest verification errors: 0

## Notes

- Harsh combined stress remains unresolved and is excluded from mission-feasible claims.
- Japanese marker source paths were normalized to ASCII selected-source names.

## Gate conclusion

This repository may be used as a public-gate package only under the allowed description and forbidden-claim boundary above. This gate does not create a new scientific or engineering claim; it only fixes the public archive posture.
