#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="ephys2-gui"
PKG="xcb-util-cursor"
# SIF_PATH="${1:?Usage: $0 /path/to/ephys2.sif}"

# 1) Bootstrap micromamba if needed
if ! command -v micromamba &>/dev/null; then
  echo "🔽 Installing micromamba…"
  curl -L micro.mamba.pm/install.sh | bash
  export PATH="$HOME/micromamba/bin:$PATH"
fi

# 2) Ensure env + package
#    Try to create it (with PKG); if it already exists, install PKG into it.
micromamba create -y -n "$ENV_NAME" "$PKG" \
  || micromamba install -y -n "$ENV_NAME" "$PKG"

# 3) Launch your GUI under that env in one shot
echo "🚀 Launching GUI in environment '$ENV_NAME'…"
# micromamba run -n "$ENV_NAME" -- singularity run --bind /n "$SIF_PATH" gui