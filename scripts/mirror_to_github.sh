#!/usr/bin/env bash
# Replica GitLab -> GitHub. Se usa desde GitLab CI y también puede ejecutarse a mano.
# Requiere GH_TOKEN (token de GitHub con permiso repo) y opcionalmente GH_REPO.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "Falta la variable GH_TOKEN" >&2
  exit 2
fi

GH_REPO="${GH_REPO:-BENDER35/sc_list_pisos_fincas}"
URL="https://x-access-token:${GH_TOKEN}@github.com/${GH_REPO}.git"
RAMA="${MIRROR_BRANCH:-main}"

mapa_tags_local() {
  git for-each-ref --format='%(objectname) %(refname:short)' refs/tags | LC_ALL=C sort
}

mapa_tags_remoto() {
  git ls-remote --tags "$1" 2>/dev/null \
    | awk '{ref=$2; sub(/^refs\/tags\//, "", ref); if (ref ~ /\^\{\}$/) next; print $1" "ref}' \
    | LC_ALL=C sort
}

if git log -1 --format=%B | grep -qi '\[skip mirror\]'; then
  echo "Último commit marcado con [skip mirror]; no se replica."
  exit 0
fi

git fetch --prune --force origin '+refs/heads/*:refs/remotes/origin/*' '+refs/tags/*:refs/tags/*' >/dev/null 2>&1 || true

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTO_SHA="$(git ls-remote "$URL" "refs/heads/$RAMA" 2>/dev/null | awk '{print $1}' || true)"
LOCAL_TAGS="$(mapa_tags_local)"
REMOTO_TAGS="$(mapa_tags_remoto "$URL")"
if [[ "$REMOTO_SHA" == "$LOCAL_SHA" && "$LOCAL_TAGS" == "$REMOTO_TAGS" ]]; then
  echo "GitHub ya está sincronizado en $LOCAL_SHA (incluidos los tags)."
  exit 0
fi

git remote remove mirror_github >/dev/null 2>&1 || true
git remote add mirror_github "$URL"
echo "Replicando $LOCAL_SHA a GitHub..."
git push --force --prune mirror_github \
  'refs/remotes/origin/*:refs/heads/*' \
  'refs/tags/*:refs/tags/*'
echo "Replica a GitHub completada."
