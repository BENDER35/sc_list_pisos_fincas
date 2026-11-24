#!/usr/bin/env bash
# Replica GitHub -> GitLab. Se usa desde GitHub Actions y también puede ejecutarse a mano.
# Requiere GITLAB_REPO_URL: https://oauth2:<token>@gitlab.com/<usuario>/<repo>.git
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${GITLAB_REPO_URL:-}" ]]; then
  echo "Falta la variable GITLAB_REPO_URL" >&2
  exit 2
fi

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
REMOTO_SHA="$(git ls-remote "$GITLAB_REPO_URL" "refs/heads/$RAMA" 2>/dev/null | awk '{print $1}' || true)"
LOCAL_TAGS="$(mapa_tags_local)"
REMOTO_TAGS="$(mapa_tags_remoto "$GITLAB_REPO_URL")"
if [[ "$REMOTO_SHA" == "$LOCAL_SHA" && "$LOCAL_TAGS" == "$REMOTO_TAGS" ]]; then
  echo "GitLab ya está sincronizado en $LOCAL_SHA (incluidos los tags)."
  exit 0
fi

git remote remove mirror_gitlab >/dev/null 2>&1 || true
git remote add mirror_gitlab "$GITLAB_REPO_URL"
echo "Replicando $LOCAL_SHA a GitLab..."
git push --force --prune mirror_gitlab \
  'refs/remotes/origin/*:refs/heads/*' \
  'refs/tags/*:refs/tags/*'
echo "Replica a GitLab completada."
