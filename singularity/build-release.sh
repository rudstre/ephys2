#!/usr/bin/env bash
set -euo pipefail

die() {
  echo "❌ $*" >&2
  exit 1
}

# 1) Ensure we’re in the repo root
[[ -d .git ]] || die "Run this from the root of the repository (where .git lives)."

# 2) Check for uncommitted changes and offer to auto‑commit & push
if [[ -n $(git status --porcelain --untracked-files=no) ]]; then
  echo "🚨 Your working directory has uncommitted tracked changes:"
  git status --porcelain --untracked-files=no
  echo
  read -rp "Auto‑stage, commit, and push these changes? [y/N] " yn
  yn=$(echo "$yn" | tr '[:upper:]' '[:lower:]')
  case "$yn" in
    y|yes)
      git add -u
      read -rp "Enter commit message: " msg
      [[ -n $msg ]] || die "Commit message cannot be empty."
      git commit -m "$msg"
      branch=$(git symbolic-ref --short HEAD)
      git push origin "$branch"
      echo "✅ Changes pushed to origin/$branch"
      ;;
    *)
      die "Please commit or stash your changes and re-run."
      ;;
  esac
fi

# 3) Ensure HEAD is already on origin
HEAD_SHA=$(git rev-parse HEAD)
if ! git branch -r --contains "$HEAD_SHA" | grep -qE 'origin/'; then
  cat <<EOF >&2
🚨  Current commit ($HEAD_SHA) is not on any origin/* branch.
Please push your branch before running this script:

  git push origin \$(git symbolic-ref --short HEAD)

Aborting.
EOF
  exit 1
fi

# 4) Auto‑detect (or prompt for) the latest release number
LATEST_RELEASE=$(./singularity/get_latest_release.sh || true)
if [[ -z $LATEST_RELEASE ]]; then
  echo "⚠️  Could not auto‑detect latest release number."
  read -rp "Please enter new release number: " NEW_RELEASE
  [[ $NEW_RELEASE =~ ^[0-9]+$ ]] || die "Invalid release number: '$NEW_RELEASE'"
else
  echo "✅ Latest release number is: $LATEST_RELEASE"
  NEW_RELEASE=$((LATEST_RELEASE + 1))
fi

# 5) Get short Git SHA
GIT_ID=$(git rev-parse --short HEAD)

# 6) Build the Singularity image via the bare‑bones script
IMG_NAME="ephys2-release-${NEW_RELEASE}_${GIT_ID}.sif"
echo "🔨 Building ${IMG_NAME}"
./singularity/build-singularity.sh "$IMG_NAME"

# 7) Tag the current commit and push the tag
TAG="ephys2-release-${NEW_RELEASE}"
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "⚠️  Tag '$TAG' already exists; skipping."
else
  echo "🔖  Creating Git tag '$TAG'"
  git tag "$TAG"
  echo "📤  Pushing tag '$TAG' to origin"
  git push origin "$TAG"
fi

echo "🎉 Done! Built ${IMG_NAME} and tagged commit as ${TAG}."