#!/usr/bin/env bash
set -euo pipefail

# Prompt for your FASRC username
read -rp "Enter fasrc username: " USER
REMOTE="login.rc.fas.harvard.edu"
REMOTE_DIR="/n/holylabs-olveczky/Lab/singularity/releases"

# SSH in and pick best (as before), but echo just the version
ssh "$USER@$REMOTE" bash -s -- "$REMOTE_DIR" <<'EOF'
  shopt -s nullglob
  cd "$1" || exit 1
  best=""
  best_ver=0
  for f in ephys2-release-*_*.sif; do
    v=${f#ephys2-release-}; v=${v%%_*}
    [[ $v =~ ^[0-9]+$ ]] || continue
    if (( v > best_ver )); then
      best_ver=$v
      best="$f"
    fi
  done
  if [[ -n $best ]]; then
    ver=${best#ephys2-release-}
    ver=${ver%%_*}
    printf '%s' "$ver"
  fi
EOF