# A10-STMS Spaceborne Thermal-Control Surrogate

このリポジトリは、以下のAI支援独立研究論文に対応するGitHub配置用フォルダである。

**A10-STMS: A Reduced-Surrogate Audit of Mission-Variable-Preserving Hybrid Thermal Control for Spaceborne Industrial Systems under Radiative, Storage, Power, Delay, and Actuator Constraints**

著者: 吉村圭司（Independent Researcher）  
状態: GitHub-ready paper companion archive v0.1.1-public-gate

## 簡易分類フォルダ名

**宇宙機・高負荷産業機器の熱制御／冷却サロゲート**

## 位置づけ

A10-STMSは、宇宙機・軌道上産業システムなどを想定した **無次元・低次元 thermal-control surrogate** の数値監査である。

対象は、radiative rejection、thermal storage、power margin、sensing delay、actuator authorityの制約下で、mission throughputを守りながらthermal safe setを維持できるかどうかを調べる、feasibility-diagnostic reduced-control architecture である。

## 中心的解釈

A10-STMSは、宇宙機用の完成済み冷却技術ではない。  
支配的な失敗原因が、資源不足、routing不足、storage不足、load shaping不足、delay、actuator degradation、harsh combined stressのどこにあるかを分類するための reduced-surrogate framework である。

## 技術的ビジュアル案内

初めて本リポジトリを見る技術的関心のある読者向けに、ブラウザだけで開ける技術的ビジュアル案内ページを同梱しています。

`docs/technical_visual_orientation/index.html`

このページは、A10-STMS の構造、すなわち project mission variable、reduced-model / surrogate としての位置づけ、structured-prior / constrained-evaluation logic、不確実性・stress discipline、evidence hierarchy、リポジトリ閲覧順、および claim boundary を短く整理するための補助資料です。

このページは説明補助であり、simulation を実行するものではありません。プロジェクトの妥当性、実装可能性、商用展開、安全認証、または実験・臨床・産業上の検証を示すものでもなく、論文本体、source/configuration materials、supporting archive materials、または専門家による独立評価を置き換えるものでもありません。

## 含まれるもの

- 論文PDF
- README日本語版・英語版
- claim boundary
- limitations
- AI支援開示
- 実務位置づけ表
- アップロードされたA10-STMS archiveから抽出したselected scripts / figures / small CSV
- 論文表から再構成したsummary CSV
- GitHub本体から除外したlarge raw outputs / compressed phase archives のinventory

## 主張しないこと

本リポジトリは、以下を主張しない。

- spacecraft-ready thermal-control system
- thermal-vacuum validation
- 新しい熱伝達機構
- 宇宙機ハードウェア設計
- flight-controller readiness
- 既存宇宙機熱制御アーキテクチャに対する実証済み優位性
- 形式的control-barrier-function保証

## 現在の状態

これはpaper companion archiveであり、宇宙機用の認証済み熱制御技術でも、全raw phase outputをone-commandで再現する完全パッケージでもない。

## PUBLIC-GATE-0 status

判定: `PASS-WITH-MINOR-PUBLICATION-FIXES-A10-STMS-PUBLIC-GATE-0`  
公開版: `v0.1.1-public-gate`  
分類: 宇宙機・高負荷産業機器の熱制御／冷却サロゲート

このリポジトリは、A10 Evidence-Lock Protocol型の公開前監査により、主張境界・非主張事項・manifest整合性・GitHub/Zenodo/Jxiv方針を固定した public-gate 版である。


## Zenodo-safe citation metadata

Zenodo DOI付与前のメタデータ検証トラブルを避けるため、この公開前パッケージではroot直下の有効な `CITATION.cff` を意図的に外しています。

下書きの引用メタデータは以下に退避しています。

`docs/citation_metadata/CITATION_DRAFT_pre_doi.cff`

Zenodo DOI付与後に、README、原稿メタデータ、引用ファイルへDOIを反映した後続リリースを切る想定です。
