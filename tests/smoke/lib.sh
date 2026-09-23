#!/usr/bin/env bash
# Shared helpers for real-install smoke runs (Fedora + macOS; no stubbed backends).
# shellcheck shell=bash
set -euo pipefail

SMOKE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SMOKE_ROOT/../.." && pwd)"
SMOKE_LOG_DIR="${SMOKE_LOG_DIR:-/tmp/dotfiles-smoke}"
SMOKE_APPLY_LOG="${SMOKE_APPLY_LOG:-$SMOKE_LOG_DIR/chezmoi-apply.log}"
SMOKE_OS="$(uname -s)"

mkdir -p "$SMOKE_LOG_DIR"

log() { printf 'smoke: %s\n' "$*"; }
fail() {
  printf 'smoke: FAIL: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" &>/dev/null || fail "missing command: $1"
}

# Containers often lack a working systemd. Package installs still run; enable /
# start become no-ops so run_onchange / run_once scripts can finish. Real daemon
# bring-up stays a host/manual concern (see docs/TEST_PLAN.md smoke section).
install_systemctl_shim() {
  local bindir="${1:-/usr/local/bin}"
  mkdir -p "$bindir"
  cat >"$bindir/systemctl" <<'EOF'
#!/usr/bin/env bash
# Smoke shim: pretend enable/start/is-* succeed when systemd is not usable.
set -euo pipefail
REAL=""
if [ -x /usr/bin/systemctl ]; then
  REAL=/usr/bin/systemctl
elif [ -x /bin/systemctl ]; then
  REAL=/bin/systemctl
fi
if [ -n "$REAL" ] && [ -d /run/systemd/system ] && \
  "$REAL" is-system-running &>/dev/null; then
  exec "$REAL" "$@"
fi
echo "smoke-systemctl-shim: $*" >&2
exit 0
EOF
  chmod 755 "$bindir/systemctl"
  export PATH="$bindir:$PATH"
}

install_sudo_shim_if_root() {
  if [ "$(id -u)" -eq 0 ] && ! command -v sudo &>/dev/null; then
    cat >/usr/local/bin/sudo <<'EOF'
#!/usr/bin/env bash
exec "$@"
EOF
    chmod 755 /usr/local/bin/sudo
  fi
}

# GHA macos runners ship Homebrew; ensure shellenv for the current arch.
ensure_brew_on_path() {
  if command -v brew &>/dev/null; then
    return 0
  fi
  if [ -x /opt/homebrew/bin/brew ]; then
    # shellcheck disable=SC1091
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    # shellcheck disable=SC1091
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

write_smoke_config() {
  # Pre-answer .chezmoi.toml.tmpl prompts without chezmoi init (CI checkouts
  # often lack a usable .git, so `chezmoi init <path>` fails with git clone).
  local profile="$1"
  local is_work=false
  local install_intellij=false
  if [ "$profile" = "work" ]; then
    is_work=true
    install_intellij=true
  fi
  mkdir -p "$HOME/.config/chezmoi"
  cat >"$HOME/.config/chezmoi/chezmoi.toml" <<EOF
[data]
    name = "Smoke Test"
    email = "smoke@example.com"
    is_work = ${is_work}
    install_intellij = ${install_intellij}
EOF
}

link_source_dir() {
  # Same layout as a normal chezmoi init clone target.
  mkdir -p "$HOME/.local/share"
  ln -sfn "$REPO_ROOT" "$HOME/.local/share/chezmoi"
  log "source -> $HOME/.local/share/chezmoi (-> $REPO_ROOT)"
}

# ide-keys only copies the IntelliJ keymap into an existing product directory.
preseed_jetbrains_for_work() {
  local profile="$1"
  [ "$profile" = "work" ] || return 0
  if [ "$SMOKE_OS" = "Darwin" ]; then
    mkdir -p "$HOME/Library/Application Support/JetBrains/IntelliJIdeaSmoke/keymaps"
  else
    mkdir -p "$HOME/.config/JetBrains/IntelliJIdeaSmoke/keymaps"
  fi
}

activate_mise() {
  export PATH="${HOME}/.local/bin:${PATH}"
  if [ -x "${HOME}/.local/bin/mise" ]; then
    # shellcheck disable=SC1091
    eval "$("${HOME}/.local/bin/mise" activate bash)"
  elif command -v mise &>/dev/null; then
    # shellcheck disable=SC1091
    eval "$(mise activate bash)"
  else
    fail "mise not on PATH after apply"
  fi
}

assert_ok() {
  local label="$1"
  shift
  if "$@"; then
    log "ok: $label"
  else
    fail "$label (command: $*)"
  fi
}

assert_version() {
  local label="$1"
  local bin="$2"
  shift 2
  if command -v "$bin" &>/dev/null; then
    local out
    out="$("$bin" "$@" 2>&1 | head -n 1)"
    log "ok: $label -> $out"
  else
    fail "$label: '$bin' not on PATH"
  fi
}

assert_missing() {
  local label="$1"
  local bin="$2"
  if command -v "$bin" &>/dev/null; then
    fail "$label: '$bin' should not be installed for this profile"
  fi
  log "ok: $label (absent as expected)"
}

assert_file() {
  local path="$1"
  [ -e "$path" ] || fail "missing path: $path"
  log "ok: path exists: $path"
}

assert_executable() {
  local path="$1"
  [ -e "$path" ] || fail "missing path: $path"
  [ -x "$path" ] || fail "not executable: $path"
  log "ok: executable: $path"
}

assert_brew_formula() {
  local pkg="$1"
  assert_ok "brew formula $pkg" brew list --formula "$pkg"
}

assert_brew_cask() {
  local cask="$1"
  assert_ok "brew cask $cask" brew list --cask "$cask"
}

assert_no_brew_formula() {
  local pkg="$1"
  if brew list --formula "$pkg" &>/dev/null; then
    fail "brew formula '$pkg' should not be installed for this profile"
  fi
  log "ok: brew formula $pkg absent"
}

assert_no_brew_cask() {
  local cask="$1"
  if brew list --cask "$cask" &>/dev/null; then
    fail "brew cask '$cask' should not be installed for this profile"
  fi
  log "ok: brew cask $cask absent"
}

assert_log_clean() {
  local logf="$1"
  [ -f "$logf" ] || fail "apply log missing: $logf"
  # Hard failures only: chezmoi reporting a script exit, or our own fatal
  # markers. Do NOT match bare `error:` — flatpak/dnf soft-fail paths print
  # that while the dispatcher continues (`|| true`).
  # Skip unified-diff payload lines (+/-) so echo strings inside applied
  # scripts cannot trip markers when chezmoi dumps the script body.
  local hits
  hits="$(
    grep -Ev '^[+-]' "$logf" |
      grep -Ei \
        'chezmoi: .*: exit status|chezmoi: error|dispatcher:.*failed|mise-install:.*error|bootstrap: (error|FAIL)' ||
      true
  )"
  if [ -n "$hits" ]; then
    printf '%s\n' "$hits" | head -n 40 >&2
    fail "apply log contains hard failure markers (see above)"
  fi
  log "ok: apply log has no hard failure markers"
}
