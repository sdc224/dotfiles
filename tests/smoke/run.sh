#!/usr/bin/env bash
# Fedora smoke: blank-ish image → non-interactive chezmoi init --apply → verify.
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

# Primitives the bootstrap/dispatcher expect on a fresh Fedora host.
log "installing base OS packages for smoke host"
dnf install -y \
  curl tar gzip diffutils findutils which \
  python3 git sudo passwd shadow-utils \
  fontconfig unzip \
  >/dev/null

# Chezmoi binary (same entrypoint as docs/MANUAL.md).
if ! command -v chezmoi &>/dev/null; then
  log "installing chezmoi"
  sh -c "$(curl -fsLS get.chezmoi.io)" -- -b /usr/local/bin
fi
require_cmd chezmoi
require_cmd python3

# Fresh destination home for this run (keeps runner $HOME pollution low when
# nested; in GHA container HOME is already the job user/root home).
export HOME="${SMOKE_HOME:-$HOME}"
mkdir -p "$HOME"

# ide-keys only copies the IntelliJ keymap into an existing product directory.
# Pre-seed a fake product so work-profile smoke proves the deploy path.
if [ "$PROFILE" = "work" ]; then
  mkdir -p "$HOME/.config/JetBrains/IntelliJIdeaSmoke/keymaps"
fi

mapfile -t PROMPT_ARGS < <(write_prompt_args "$PROFILE")

log "chezmoi init --apply (non-interactive prompts)"
set +e
chezmoi init --apply -v \
  "${PROMPT_ARGS[@]}" \
  "$REPO_ROOT" \
  >"$SMOKE_APPLY_LOG" 2>&1
APPLY_RC=$?
set -e

# Always surface the tail of the log in CI.
tail -n 80 "$SMOKE_APPLY_LOG" || true

if [ "$APPLY_RC" -ne 0 ]; then
  fail "chezmoi init --apply exited $APPLY_RC (full log: $SMOKE_APPLY_LOG)"
fi

assert_log_clean "$SMOKE_APPLY_LOG"
activate_mise

# shellcheck source=verify.sh
source "$SMOKE_ROOT/verify.sh"
verify_profile "$PROFILE"

log "PASS profile=$PROFILE"
