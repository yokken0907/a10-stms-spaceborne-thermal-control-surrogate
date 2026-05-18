# INPIT・公的機関向け1枚説明資料: A10-STMS

## 技術名

A10-STMS  
Spaceborne / Industrial Mission-Variable-Preserving Hybrid Thermal-Control Surrogate

## 一文要約

A10-STMSは、宇宙機実装済み冷却システムを示す技術ではなく、宇宙機・高負荷産業機器を想定した無次元低次元サロゲート上で、熱安全・ミッションスループット・蓄熱余裕・電力余裕・勾配リスク・遅延・アクチュエータ劣化を同時に診断する前工学的制御理論である。

## 背景

宇宙機や高負荷産業機器では、高出力通信、レーザー通信、電気推進、軌道上データ処理、宇宙製造などにより、熱制御の難度が高まる可能性がある。

単純な平均温度管理だけでは、core temperature、thermal gradient、storage margin、power margin、mission throughput を同時に評価できない場合がある。

## 技術的に扱うもの

- nondimensional reduced surrogate
- hybrid thermal control
- separated thermal / storage / power / gradient barriers
- radiative fourth-power proxy
- mission throughput
- sensing delay
- actuator-authority degradation
- out-of-sample stress
- harsh combined stress
- failure / CVaR / unsafe fraction diagnostics

## 報告済みの範囲

tested surrogate 内では、以下が整理されている。

- final locked status: `PASS-PHASE2E-DELAY-DEGRADE-ROBUSTNESS`
- manageable Phase 2E 条件で、A10-v4系が Pump+Radiator baseline に対して failure rate と tail-risk metrics の分離を示す
- Baseline / A10-v4-safe: `failure = 0.03125`, `CVaR0.95 = 4.6976e-05`, `unsafe_frac = 0.003051`
- Delay 1.0 / A10-v4-balanced: `failure = 0.008929`
- Out-of-sample / A10-v4-safe: `failure = 0.06875`
- Harsh combined stress は未解決であり、A10-v4-safe でも `failure = 0.96875`

これらは実宇宙機性能ではなく、無次元サロゲート内の結果である。

## 現時点で主張しないもの

- 宇宙機実装済み冷却技術
- 熱真空試験済み技術
- flight controller
- certified aerospace safety system
- radiator / heat pipe / pumped loop / PCM の実設計
- 新しい熱伝達機構
- harsh combined stress の解決
- formal control-barrier-function proof
- 実宇宙機・実payload・実orbitでの検証

## 相談したいこと

- 本理論をどの分野の専門家にレビューしてもらうべきか
- 宇宙機熱制御・制御工学・安全工学の共同研究候補
- 知財化より先に必要な検証段階
- Jxiv / GitHub / Zenodo 公開物としての適切な見せ方
- 実工学へ進める場合の最低限の安全境界
- 高忠実度熱解析や熱真空試験へ進む前の妥当な前段階

## 相談時の希望姿勢

本件は「すぐに宇宙機へ搭載できる冷却技術」としてではなく、以下として相談したい。

> 宇宙機・高負荷産業機器を想定した、無次元低次元サロゲート上のmission-variable-preserving hybrid thermal-control audit。

## 連絡・公開情報

- 論文: Jxiv投稿・改訂対象
- GitHub: paper companion archive
- DOI: 論文またはリポジトリ記載の最新版を参照
- 著者: 吉村圭司, Independent Researcher
