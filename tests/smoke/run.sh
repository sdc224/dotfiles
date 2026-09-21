#!/usr/bin/env bash
# Fedora smoke: blank-ish image → non-interactive chezmoi apply → verify.
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

# Primitives the bootstrap/dispatcher/mise expect on a fresh Fedora host.
# gcc + libatomic: cargo:procs/tokei compile from source; Node needs libatomic.so.1
log "installing base OS packages for smoke host"
dnf install -y \
  curl tar gzip diffutils findutils which \
  python3 git sudo passwd shadow-utils \
  fontconfig unzip \
  gcc libatomic \
  >/dev/null

# Chezmoi binary (retry + GitHub fallback; release CDNs 504 in CI).
if ! command -v chezmoi &>/dev/null; then
  log "installing chezmoi"
  bash "$REPO_ROOT/tests/lib/install-chezmoi.sh" /usr/local/bin
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

# GHA container checkouts often have no .git (no git in the image at checkout
# time), so `chezmoi init <path>` fails with: repository does not exist.
# Mirror a completed init: write config + link source, then apply.
write_smoke_config "$PROFILE"
link_source_dir

log "chezmoi apply (non-interactive, source=$HOME/.local/share/chezmoi)"
set +e
chezmoi apply -v \
  >"$SMOKE_APPLY_LOG" 2>&1
APPLY_RC=$?
set -e

# Always surface the tail of the log in CI.
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
