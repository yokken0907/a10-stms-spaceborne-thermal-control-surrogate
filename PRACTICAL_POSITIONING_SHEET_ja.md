# 実務位置づけシート

## 技術名

A10-STMS Spaceborne Thermal-Control Surrogate  
または  
A10-STMS: Mission-Variable-Preserving Hybrid Thermal Control Surrogate

## 簡易分類フォルダ名

宇宙機・高負荷産業機器の熱制御／冷却サロゲート

## 対象産業

- 宇宙機熱制御
- 軌道上データ処理・高出力通信・レーザー通信
- 電気推進パワーエレクトロニクス
- 宇宙製造・高負荷産業機器
- 高熱流束電子機器
- safety-oriented thermal-control evaluation

## 現場課題

高負荷宇宙機器では、平均温度だけでなく、core temperature、cold-plate、radiator、storage margin、power margin、thermal-gradient risk、mission throughputを同時に守る必要がある。  
単純なPump制御やPump+Radiator制御だけでは、thermal safetyとmission throughputを同時に満たせないstress windowが存在する可能性がある。

## A10の役割

A10は単一の冷却努力ではなく、thermal barrier、storage barrier、power barrier、gradient barrierを分離して扱うstructured-prior controllerとして働く。  
冷却、routing、storage、load shapingを分けることで、どの制約が支配的かを診断する。

## 期待効果

- controller-limited failureとresource-limited failureを区別できる。
- routing / storage / load shaping の寄与をablationで評価できる。
- delayやactuator degradationが支配的ボトルネックかどうかを診断できる。
- manageable stressではfeasibility separationを示し、harsh combined stressでは未解決領域として境界設定できる。

## 検証済み範囲

論文内では、最終状態として PASS-PHASE2E-DELAY-DEGRADE-ROBUSTNESS が報告されている。  
A10-v4-safeは、baseline、delayed sensing、moderate actuator degradation、out-of-sample条件でPump+Radiator baselineからfailure rateとtail-risk metricsの分離を維持した。  
ただし、harsh combined stressは未解決であり、mission-feasible claimから明示的に除外されている。

## 未検証範囲

- 熱真空試験
- 実宇宙機・実payload・実orbit
- multi-node high-fidelity thermal model
- 詳細view factor / attitude dynamics
- 実radiator / heat pipe / pumped loop / PCM設計
- flight controller
- safety certification
- harsh combined stressの解決

## 実装への次ステップ

1. paper companion archiveとして公開する。
2. large phase-output archivesはGitHub本体ではなくZenodoまたはrelease asset候補にする。
3. 代表scriptとsummary CSVだけを公開repoに置く。
4. 次段階では、calibrated thermal nodes、realistic orbit/environment forcing、view-factor geometry、power-system constraints、hardware-relevant actuator modelsを導入する。
5. 実工学へ進む場合は、宇宙機熱制御専門家・熱真空試験・規制/安全評価が必須。

## 想定読者

- 宇宙機熱制御研究者
- thermal management / hybrid cooling研究者
- control / viability / barrier-method研究者
- high-power spacecraft payload設計者
- reduced surrogate評価者
- INPIT / 知財・共同研究相談員

## 誇張しない一文の結論

A10-STMSは、宇宙機・高負荷産業機器の熱制御を想定した無次元低次元サロゲート上で、separated-barrier hybrid controlがthermal safetyとmission throughputをどこまで保てるかを診断する理論であり、実機冷却システムを主張するものではない。
