# selected_from_uploaded_stms_project

このフォルダは、アップロードされた `a10_stms_phase1_selected.zip` から、GitHub公開に適した素材だけを抽出したsource snapshotである。

## 含めたもの

- A10-STMS phase scripts
- PNG figures
- 小型summary / resource CSV
- Markdown / TeX / small text files

## 除外したもの

- `.venv/`
- `site-packages/`
- `__pycache__/`
- `*.pyc`
- compiled binaries
- `all_code*.txt`
- compressed phase-output archives
- large raw/per-run CSV

## 注意

これはpaper companion archiveであり、全phase output archiveをGitHub本体に含める完全再現パッケージではない。  
大容量出力は `large_assets_not_in_git/` にinventoryだけを置き、必要ならZenodoまたはGitHub release assetで扱う。
