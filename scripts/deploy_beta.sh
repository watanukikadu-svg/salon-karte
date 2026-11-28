#!/usr/bin/env bash
# お試し用（ベータ）の Web 版を、main の beta/ に置く（いま作業中のブランチの中身をコピーする）
# 使い方（リポジトリの一番上で）：bash scripts/deploy_beta.sh
# ※ 1.1.0 を出すときは beta/ を消すこと
set -euo pipefail
ROOT=$(pwd); WT=$(mktemp -d)
git fetch -q origin main
git worktree add -q "$WT" origin/main
cd "$WT" && git checkout -q -b beta-deploy-$$
mkdir -p beta
for f in index.html privacy.html terms.html tokushoho.html support.html manifest.webmanifest; do git -C "$ROOT" show HEAD:$f > beta/$f; done
rm -rf beta/icons && cp -r "$ROOT/icons" beta/icons
sed -i 's|<title>美容室カルテ</title>|<title>美容室カルテ（お試し版）</title>|' beta/index.html
git add beta
if git diff --cached --quiet; then echo "変更なし"; else
  git -c user.name="$(git -C "$ROOT" log -1 --format=%an)" -c user.email="$(git -C "$ROOT" log -1 --format=%ae)" commit -qm "お試し用（ベータ）の Web 版を更新する

$(git -C "$ROOT" log -1 --format=%(trailers))"
  git push -q origin HEAD:main && echo "beta/ を更新しました"
fi
cd "$ROOT" && git worktree remove --force "$WT"
