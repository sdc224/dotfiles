#!/usr/bin/env bash
# Fedora smoke: blank image → chezmoi apply → verify.
#
# Principle: this repo is first contact for a fresh machine. Smoke must NOT
# pre-install converge deps (gcc, python3, flatpak, …) — those belong in
# run_once_before_00-bootstrap. Smoke only provides:
#   1. CI harness shims (systemctl/sudo in containers)
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

log "repo=$REPO_ROOT profile=$PROFILE"
install_sudo_shim_if_root
if [ "${SKIP_SYSTEMCTL_SHIM:-0}" != "1" ]; then
  install_systemctl_shim /usr/local/bin
fi

# Sole OS prerequisite for first contact (matches README/MANUAL.md).
if ! command -v curl &>/dev/null; then
  log "installing curl (only smoke/host prerequisite)"
  dnf install -y curl
fi
require_cmd curl

# Chezmoi binary — same role as the human one-liner in README, with CI retries.
if ! command -v chezmoi &>/dev/null; then
  log "installing chezmoi"
  bash "$REPO_ROOT/tests/lib/install-chezmoi.sh" /usr/local/bin
fi
require_cmd chezmoi

export HOME="${SMOKE_HOME:-$HOME}"
mkdir -p "$HOME"

# ide-keys only copies the IntelliJ keymap into an existing product directory.
# Pre-seed a fake product so work-profile smoke proves the deploy path.
if [ "$PROFILE" = "work" ]; then
  mkdir -p "$HOME/.config/JetBrains/IntelliJIdeaSmoke/keymaps"
fi

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
activate_mise

# shellcheck source=verify.sh
source "$SMOKE_ROOT/verify.sh"
verify_profile "$PROFILE"

log "PASS profile=$PROFILE"
