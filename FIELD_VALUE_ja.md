# FIELD VALUE: A10-STMS の現場価値整理

## 1. 一文要約

A10-STMSは、宇宙機や高負荷産業機器の実冷却装置を設計する技術ではなく、熱安全・蓄熱余裕・電力余裕・勾配リスク・遅延観測・アクチュエータ劣化を、無次元低次元サロゲート上で同時に診断する **mission-variable-preserving hybrid thermal-control audit** である。

## 2. 現場・研究開発で問題になること

宇宙機・高負荷産業機器の熱制御では、平均温度だけでは安全側の判断ができない。実際には、以下のような複数制約を同時に扱う必要がある。

- core-temperature-like state の上限管理
- cold-plate / radiator-like rejection の制約
- radiative heat rejection の非線形性
- storage margin
- power margin
- thermal-gradient risk
- mission throughput
- sensing delay
- actuator authority degradation
- out-of-sample stress
- harsh combined stress

A10-STMSは、これらを実機熱設計としてではなく、低次元・無次元サロゲート上で分類する。

## 3. A10-STMS が与える価値

A10-STMSの価値は「宇宙機冷却装置を完成させること」ではない。価値は、前工学的な研究開発段階で、熱制御失敗の原因と制約境界を整理できる点にある。

### 3.1 thermal safety と mission throughput の同時評価

A10-STMSは、thermal safety だけでなく mission throughput も同時に見る。  
そのため、「安全側だがミッションが成立しない制御」と「ミッションを通すが熱的に危険な制御」を分けて評価できる。

### 3.2 separated-barrier control の寄与整理

A10は単一の冷却努力ではなく、thermal barrier、storage barrier、power barrier、gradient barrier を分けて扱う structured-prior controller として位置づけられる。

これにより、以下を切り分けやすくなる。

- controller-limited failure
- resource-limited failure
- thermal / gradient bottleneck
- delay-induced degradation
- actuator-authority limitation
- harsh combined-stress failure

### 3.3 manageable stress における分離

Phase 2E の manageable 条件では、A10-v4 系が Pump+Radiator baseline に対して、failure rate と tail-risk metrics の分離を示している。

例として、tested surrogate 内では以下が報告されている。

- Baseline / A10-v4-safe: `failure = 0.03125`, `CVaR0.95 = 4.6976e-05`, `unsafe_frac = 0.003051`
- Delay 1.0 / A10-v4-balanced: `failure = 0.008929`
- Out-of-sample / A10-v4-safe: `failure = 0.06875`

これらは実機性能ではなく、tested nondimensional reduced surrogate 内の結果である。

### 3.4 未解決領域の明示

Harsh combined stress は未解決である。  
A10-v4-safe でも `failure = 0.96875` が報告されており、mission-feasible claim から明示的に除外される。

この未解決結果を隠さないこと自体が、A10-STMSの主張境界として重要である。

## 4. 想定される使い道

A10-STMSは、以下のような使い方に向く。

- 宇宙機熱制御研究の初期整理
- hybrid thermal-control architecture の比較検討
- Pump+Radiator baseline に対する reduced-surrogate 比較
- thermal / storage / power / gradient bottleneck の切り分け
- delay / actuator degradation の影響診断
- 高忠実度 thermal model に進む前の仮説整理
- 公的機関・共同研究候補・専門家レビュー向け説明資料

## 5. 置き換えないもの

A10-STMSは、以下を置き換えない。

- 実宇宙機熱設計
- radiator / heat pipe / pumped loop / PCM / material-stack 設計
- 熱真空試験
- orbit / beta angle / attitude dynamics を含む詳細熱解析
- multi-node high-fidelity thermal model
- flight controller
- aerospace safety certification
- formal control-barrier-function proof
- 宇宙機熱制御専門家による設計審査

## 6. 現場接続のために必要な次段階

A10-STMSを実工学に接続するには、少なくとも以下が必要である。

- calibrated thermal-node model との照合
- realistic orbit/environment forcing
- detailed view-factor / geometry model
- radiator / heat-pipe / pumped-loop / PCM などの実アクチュエータモデル
- power-system constraints の詳細化
- sensor noise / delay / dropout / drift のロバスト性検証
- thermal-vacuum test との接続可能性評価
- independent replication
- 宇宙機熱制御・制御工学・安全工学の専門家レビュー

## 7. 誇張しない結論

A10-STMSは、宇宙機冷却装置を完成させる技術ではない。  
その価値は、無次元 reduced surrogate 上で、熱安全・ミッションスループット・蓄熱余裕・電力余裕・勾配リスク・遅延・アクチュエータ劣化を同時に診断し、manageable stress と unresolved harsh combined stress を明確に分ける点にある。
