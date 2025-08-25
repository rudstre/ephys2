#!/usr/bin/env bash
set -euo pipefail

# Fail nicely
die() {
  echo "❌ $*" >&2
  exit 1
}

# 1) Ensure we’re in the repo root
[[ -d .git ]] || die "Run this from the root of the repository (where .git lives)."

# 2) Get the latest release number from tags on the current branch
#    Tags are expected to look like: ephys2-release-N
LATEST_TAG=$(git describe --tags --match "ephys2-release-*" --abbrev=0 2>/dev/null || true)

if [[ -z $LATEST_TAG ]]; then
  echo "⚠️  No existing release tags found. Starting at 1."
  NEW_RELEASE=1
else
  # Extract the numeric part and increment
  LATEST_RELEASE=${LATEST_TAG#ephys2-release-}
  [[ $LATEST_RELEASE =~ ^[0-9]+$ ]] || die "Latest tag '$LATEST_TAG' does not end with a number."
  NEW_RELEASE=$((LATEST_RELEASE + 1))
fi

# 3) Get short Git SHA for traceability
GIT_ID=$(git rev-parse --short HEAD)

# 4) Build the Singularity image
IMG_NAME="ephys2-release-${NEW_RELEASE}_${GIT_ID}.sif"
echo "🔨 Building ${IMG_NAME}"
./singularity/build-singularity.sh "$IMG_NAME"

# 5) Tag this commit and push (optional in CI)
TAG="ephys2-release-${NEW_RELEASE}"
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "⚠️ Tag '$TAG' already exists; skipping creation."
else
  echo "🔖 Creating Git tag '$TAG'"
  git tag "$TAG"
  echo "📤 Pushing tag '$TAG' to origin"
  git push origin "$TAG"
fi

echo "🎉 Done! Built ${IMG_NAME} and tagged commit as ${TAG}."