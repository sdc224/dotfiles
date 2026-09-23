#!/usr/bin/env bash
# Real-install smoke: blank home → chezmoi apply → verify (Fedora + macOS).
#
# Principle: this repo is first contact for a fresh machine. Smoke must NOT
# pre-install converge deps (gcc, python3, flatpak, brew formulae, …) — those
# belong in run_once_before_00-bootstrap / the package dispatcher. Smoke only
# provides:
#   1. CI harness shims (systemctl/sudo in Linux containers)
#   2. chezmoi binary (human path: get.chezmoi.io; needs curl)
#   3. non-interactive profile config + apply + assertions
#
# Usage:
#   PROFILE=personal ./tests/smoke/run.sh
#   PROFILE=work ./tests/smoke/run.sh
#
# Env:
#   PROFILE          personal|work (required)
#   SMOKE_LOG_DIR    log directory (default /tmp/dotfiles-smoke)
#   SKIP_SYSTEMCTL_SHIM=1  use real systemctl only (needs working systemd)
set -euo pipefail

SMOKE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SMOKE_ROOT/lib.sh"

PROFILE="${PROFILE:-}"
case "$PROFILE" in
personal | work) ;;
*)
  fail "PROFILE must be 'personal' or 'work' (got: '${PROFILE:-}')"
  ;;
esac

log "repo=$REPO_ROOT profile=$PROFILE os=$SMOKE_OS"

case "$SMOKE_OS" in
Linux)
  install_sudo_shim_if_root
  if [ "${SKIP_SYSTEMCTL_SHIM:-0}" != "1" ]; then
    install_systemctl_shim /usr/local/bin
  fi
  # Sole OS prerequisite for first contact (matches README/MANUAL.md).
  if ! command -v curl &>/dev/null; then
    log "installing curl (only smoke/host prerequisite)"
    dnf install -y curl
  fi
  ;;
Darwin)
  # macOS GHA already has curl + Homebrew. Keep brew noninteractive for CI.
  export NONINTERACTIVE=1
  export HOMEBREW_NO_AUTO_UPDATE=1
  export HOMEBREW_NO_ENV_HINTS=1
  ensure_brew_on_path
  if ! command -v brew &>/dev/null; then
    fail "Homebrew missing on macOS runner (bootstrap would install it on a real Mac)"
  fi
  log "brew=$(command -v brew) ($(brew --prefix))"
  ;;
*)
  fail "unsupported OS for smoke: $SMOKE_OS"
  ;;
esac

require_cmd curl

# Chezmoi binary — same role as the human one-liner in README, with CI retries.
if ! command -v chezmoi &>/dev/null; then
  log "installing chezmoi"
  if [ "$SMOKE_OS" = "Darwin" ]; then
    # Prefer user-writable bindir on macOS runners (no sudo).
    mkdir -p "$HOME/.local/bin"
    bash "$REPO_ROOT/tests/lib/install-chezmoi.sh" "$HOME/.local/bin"
    export PATH="$HOME/.local/bin:$PATH"
  else
    bash "$REPO_ROOT/tests/lib/install-chezmoi.sh" /usr/local/bin
  fi
fi
require_cmd chezmoi

export HOME="${SMOKE_HOME:-$HOME}"
mkdir -p "$HOME"

preseed_jetbrains_for_work "$PROFILE"

# Non-interactive profile (answers .chezmoi.toml.tmpl prompts). Link checkout
# as the source — GHA trees often lack .git so we avoid `chezmoi init <path>`.
write_smoke_config "$PROFILE"
link_source_dir

log "chezmoi apply (bootstrap owns OS deps; source=$HOME/.local/share/chezmoi)"
set +e
chezmoi apply -v \
  >"$SMOKE_APPLY_LOG" 2>&1
APPLY_RC=$?
set -e

tail -n 80 "$SMOKE_APPLY_LOG" || true

if [ "$APPLY_RC" -ne 0 ]; then
  fail "chezmoi apply exited $APPLY_RC (full log: $SMOKE_APPLY_LOG)"
fi

assert_log_clean "$SMOKE_APPLY_LOG"

# After Darwin apply, brew may have been installed/updated by bootstrap.
if [ "$SMOKE_OS" = "Darwin" ]; then
  ensure_brew_on_path
fi
activate_mise

# shellcheck source=verify.sh
source "$SMOKE_ROOT/verify.sh"
verify_profile "$PROFILE"

log "PASS profile=$PROFILE os=$SMOKE_OS"
