# large_assets_not_in_git

このフォルダは、GitHub本体から除外した大容量output archive / raw CSVのinventoryを置く。

## 除外理由

- phase output tar.gz が複数含まれる。
- raw per-run CSVが数MB級で含まれる。
- GitHub本体に置くと重く、公開repoとして扱いにくい。
- raw outputを公開する場合は、ZenodoまたはGitHub release assetへ分離する方がよい。

## 現在の扱い

- summary CSVとselected figures/scriptsはrepo本体に含める。
- large raw outputsはinventoryのみ記録する。
