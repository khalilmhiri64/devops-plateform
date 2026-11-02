#!/usr/bin/env bash
# Promote a version by changing the image tags in an overlay and pushing to Git.
# ArgoCD notices the commit and syncs. Git stays the single source of truth.
#   scripts/gitops-bump.sh <staging|production> <version>
set -euo pipefail
cd "$(dirname "$0")/.."

ENV="${1:?environment (staging|production)}"
VERSION="${2:?version}"
FILE="k8s/overlays/${ENV}/kustomization.yaml"
[[ -f "$FILE" ]] || { echo "unknown environment: $ENV" >&2; exit 1; }
[[ "$VERSION" =~ ^[0-9A-Za-z._-]+$ ]] || { echo "invalid version: $VERSION" >&2; exit 1; }

# Rewrite every `newTag:` under images: (all three services move together).
sed -i.bak -E "s/^(\s*newTag:).*/\1 ${VERSION}/" "$FILE" && rm -f "$FILE.bak"

if git diff --quiet -- "$FILE"; then
  echo "$ENV already at $VERSION"
  exit 0
fi

git config user.email >/dev/null || git config user.email "jenkins@jobs.local"
git config user.name  >/dev/null || git config user.name  "Jenkins"
git add "$FILE"
git commit -m "deploy(${ENV}): ${VERSION} [skip ci]"
# Retry to survive a concurrent push from another pipeline.
for i in 1 2 3; do
  git pull --rebase origin "${GITOPS_BRANCH:-main}" && git push origin "HEAD:${GITOPS_BRANCH:-main}" && exit 0
  sleep $((i * 5))
done
echo "failed to push GitOps change" >&2
exit 1
