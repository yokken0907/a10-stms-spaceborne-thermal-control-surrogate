# 再現性メモ

## 現在の状態

このリポジトリはpaper companion archiveである。

## あるもの

- 論文PDF
- 論文表に対応するsummary CSV
- selected scripts
- selected figures
- small output CSV
- large output inventory
- claim boundary / limitations

## あえて入れていないもの

- virtual environment
- compiled dependencies
- site-packages
- all_code
- compressed phase-output archives
- large raw/per-run CSV

## 再現性の意味

このサロゲートはnondimensionalであるため、再現性とは実宇宙機データとの一致ではなく、指定script、seed、stress window、resource scale、controller variantの一致を意味する。

## 現在の限界

全phase output archiveをGitHub本体には入れていないため、完全raw-output archiveではない。必要ならZenodo側でlarge outputsを別アーカイブ化する。
