# Jxiv v3.x 改訂方針: A10-STMS

## 1. 目的

本メモは、A10-STMS論文をJxiv v3.xとして改訂・差し替え・補足する場合の方針を整理する。

目的は論文を増やすことではなく、既存論文の主張境界をより明確にし、GitHub・Zenodo・Jxiv間の整合性を高めることである。

## 2. 維持すべき中心位置づけ

A10-STMSは以下として扱う。

> 宇宙機・高負荷産業機器を想定した、無次元低次元サロゲート上のmission-variable-preserving hybrid thermal-control audit。

## 3. 強めない方がよい表現

Jxiv改訂では、以下のような表現を避ける、または明確に限定する。

- 宇宙機実装済み冷却技術
- thermal-vacuum validated technology
- flight controller
- spacecraft hardware design
- certified aerospace safety system
- new heat-transfer mechanism
- solved harsh combined stress
- formal control-barrier-function proof
- universal superiority over existing spacecraft thermal-control architectures

## 4. 推奨タイトル案

### 英語タイトル案

A10-STMS: A Reduced-Surrogate Audit of Mission-Variable-Preserving Hybrid Thermal Control under Radiative, Storage, Power, Delay, and Actuator Constraints

### 日本語タイトル案

A10-STMS：放射・蓄熱・電力・遅延・アクチュエータ制約下のミッション変数保存型ハイブリッド熱制御に関する低次元サロゲート監査

## 5. 副題案

### 英語副題

A bounded pre-engineering surrogate study without spacecraft-ready, thermal-vacuum, flight-control, or certified-safety claims

### 日本語副題

宇宙機実装・熱真空検証・飛行制御・安全認証を主張しない前工学的サロゲート研究

## 6. 抄録で明記すべきこと

抄録では以下を明記する。

- nondimensional reduced surrogate であること
- mission variable は実ミッション達成ではなく、surrogate viability target であること
- radiative / storage / power / delay / actuator constraints を扱うこと
- Phase 2E の manageable stress における分離を示すこと
- harsh combined stress は未解決であり mission-feasible claim から除外すること
- spacecraft-ready cooling, thermal-vacuum validation, flight readiness, certified safety は主張しないこと

## 7. 結論で明記すべきこと

結論では、以下のように閉じるのが安全である。

> 本研究は、宇宙機冷却装置、熱真空試験済み技術、または飛行制御器を示すものではない。得られた結果は、tested nondimensional reduced surrogate 内において、separated-barrier hybrid control がmanageable stress familyでfailure rateとtail-risk metricsを分離できることを示す一方、harsh combined stressは未解決領域として残ることを示すものである。

## 8. GitHubとの整合性

Jxiv本文・GitHub README・`CLAIM_BOUNDARY.md`・`LIMITATIONS.md` の表現は一致させる。

特に以下の短文を共通化するとよい。

> A10-STMS is a nondimensional reduced-surrogate audit of mission-variable-preserving hybrid thermal control. It is not spacecraft-ready cooling technology, thermal-vacuum-validated technology, a flight controller, or a certified aerospace safety system.

## 9. 改訂の優先順位

1. タイトル・副題の安全化
2. abstract / conclusion の主張境界追記
3. manageable stress と harsh combined stress の明確な分離
4. Phase 2E 結果の限定表現
5. GitHub URL / DOI / repository status の確認
6. AI assistance disclosure の維持
7. references / citation metadata の整合性確認

## 10. 改訂しない方がよい方向

- 数値結果を実宇宙機性能のように見せる
- failure rate の改善を安全認証のように扱う
- A10-v4-safe を flight controller のように扱う
- harsh combined stress を解決済みのように見せる
- radiator / heat pipe / pumped loop / PCM の具体設計へ踏み込む
- thermal-vacuum validation なしに実装可能性を強調する

## 11. 推奨結論

Jxiv v3.xは、A10-STMSを「宇宙機冷却技術」ではなく、「宇宙機・高負荷産業機器を想定した前工学的 thermal-control surrogate audit」として再提示するのが最も安全である。
