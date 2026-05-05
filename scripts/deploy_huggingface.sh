#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: ./scripts/deploy_huggingface.sh <hf-username>/<space-name>"
  exit 1
fi

SPACE_ID="$1"

if command -v git-lfs >/dev/null 2>&1; then
  git lfs install
  git lfs track "*.JPG" "*.jpg" "*.jpeg" "*.png" || true
fi

git init
if ! git remote get-url space >/dev/null 2>&1; then
  git remote add space "https://huggingface.co/spaces/${SPACE_ID}"
fi

git add .
git commit -m "Deploy fixed DroneSeg Vision Platform" || true
git branch -M main
git push space main
