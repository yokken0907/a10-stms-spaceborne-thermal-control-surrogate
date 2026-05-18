# README Insert Blocks for A10-STMS Repository

This file contains optional blocks that can be inserted into `README.md` and `README_ja.md`.

## English README: suggested insertion near the top

```markdown
## Start here

This repository is not a spacecraft-ready cooling system, thermal-vacuum-validated technology, flight controller, certified aerospace safety system, or hardware thermal-control design.

A10-STMS is a nondimensional reduced-surrogate audit of mission-variable-preserving hybrid thermal control for spaceborne / industrial thermal-control motifs under radiative, storage, power, sensing-delay, actuator-authority, and combined-stress constraints.

Recommended first reading:

1. `REVIEWER_START_HERE.md`
2. `CLAIM_BOUNDARY.md`
3. `LIMITATIONS.md`
4. `FIELD_VALUE_en.md`
5. `NEXT_VALIDATION_PLAN.md`
6. `docs/technical_visual_orientation/index.html`
```

## Japanese README: suggested insertion near the top

```markdown
## 初めて読む方へ

本リポジトリは、宇宙機実装済み冷却システム、熱真空試験済み技術、飛行用制御器、航空宇宙安全認証済み技術、または実ハードウェア熱設計を示すものではありません。

A10-STMSは、宇宙機・高負荷産業機器を想定した無次元低次元サロゲート上で、放射・蓄熱・電力・観測遅延・アクチュエータ権限・複合ストレス制約下のmission-variable-preserving hybrid thermal controlを監査する研究です。

初見の方は、以下の順に読むことを推奨します。

1. `REVIEWER_START_HERE.md`
2. `CLAIM_BOUNDARY.md`
3. `LIMITATIONS.md`
4. `FIELD_VALUE_ja.md`
5. `NEXT_VALIDATION_PLAN.md`
6. `docs/technical_visual_orientation/index.html`
```

## English README: compact claim-boundary box

```markdown
## Claim boundary in one paragraph

A10-STMS is a nondimensional reduced-surrogate audit of mission-variable-preserving hybrid thermal control. It does not provide spacecraft-ready cooling technology, thermal-vacuum validation, flight-controller readiness, certified aerospace safety, hardware thermal design, new heat-transfer physics, or a solution of harsh combined stress. All reported numerical results are bounded to the tested reduced surrogate and stress families.
```

## Japanese README: compact claim-boundary box

```markdown
## 主張境界の要約

A10-STMSは、無次元低次元サロゲート上のmission-variable-preserving hybrid thermal control監査です。宇宙機実装済み冷却技術、熱真空試験済み技術、飛行用制御器、安全認証済み技術、実ハードウェア熱設計、新しい熱伝達機構、またはharsh combined stressの解決を主張するものではありません。報告された数値結果は、すべてtested reduced surrogate と stress family 内に限定されます。
```
