#!/usr/bin/env bash
# Optional local entry: run Fedora smoke inside Docker (mirrors CI).
# Requires Docker. Usage: ./tests/smoke/docker-run.sh personal
set -euo pipefail

PROFILE="${1:-}"
case "$PROFILE" in
  personal | work) ;;
  *)
    echo "usage: $0 personal|work" >&2
    exit 2
    ;;
esac

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
IMG="${SMOKE_IMAGE:-fedora:latest}"

docker run --rm --privileged \
  -e PROFILE="$PROFILE" \
  -e HOME=/root \
  -v "$ROOT:/dotfiles:ro" \
  -w /dotfiles \
  "$IMG" \
  bash /dotfiles/tests/smoke/run.sh
