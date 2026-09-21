#!/usr/bin/env bash
# Install chezmoi into BINDIR with retries + GitHub-release fallback.
# Shared by CI workflows and tests/smoke (GitHub release CDNs 504 often).
#
# Usage: bash tests/lib/install-chezmoi.sh [bindir]
set -euo pipefail

BINDIR="${1:-${CHEZMOI_BINDIR:-/usr/local/bin}}"
mkdir -p "$BINDIR"

if [ -x "$BINDIR/chezmoi" ] || command -v chezmoi &>/dev/null; then
  echo "chezmoi already installed: $(command -v chezmoi || echo "$BINDIR/chezmoi")"
  exit 0
fi

install_via_script() {
  local attempt
  for attempt in 1 2 3 4 5; do
    echo "chezmoi: installer attempt ${attempt}/5 -> ${BINDIR}"
    if curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      https://get.chezmoi.io | sh -s -- -b "$BINDIR"; then
      return 0
    fi
    sleep $((attempt * 2))
  done
  return 1
}

install_via_github() {
  # Bypass get.chezmoi.io; download a release tarball directly (retried).
  local ver os arch asset url tmp
  ver="${CHEZMOI_VERSION:-2.72.2}"
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "$(uname -m)" in
    x86_64 | amd64) arch=amd64 ;;
    aarch64 | arm64) arch=arm64 ;;
    *)
      echo "chezmoi: unsupported arch $(uname -m)" >&2
      return 1
      ;;
  esac
  asset="chezmoi_${ver}_${os}_${arch}.tar.gz"
  url="https://github.com/twpayne/chezmoi/releases/download/v${ver}/${asset}"
  tmp="$(mktemp -d)"
  echo "chezmoi: fetching ${url}"
  curl --retry 5 --retry-delay 2 --retry-all-errors -fL -o "${tmp}/${asset}" "$url"
  tar -xzf "${tmp}/${asset}" -C "$tmp"
  install -m 755 "${tmp}/chezmoi" "${BINDIR}/chezmoi"
  rm -rf "$tmp"
}

if ! install_via_script; then
  echo "chezmoi: installer script failed; trying GitHub release asset..." >&2
  install_via_github
fi

if [ ! -x "${BINDIR}/chezmoi" ]; then
  echo "chezmoi: install failed" >&2
  exit 1
fi
"${BINDIR}/chezmoi" --version
