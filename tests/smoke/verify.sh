#!/usr/bin/env bash
# Post-apply assertions for smoke runs. Sourced by run.sh after mise activate.
# shellcheck shell=bash

verify_profile() {
  local profile="$1"
  log "verifying profile=$profile"

  # --- always: managed shell + core mise tools ---
  assert_file "$HOME/.zshrc"
  assert_file "$HOME/.config/mise/config.toml"
  assert_file "$HOME/.config/ghostty/config"
  assert_executable "$HOME/.local/bin/dotfiles-doctor"
  assert_executable "$HOME/.local/bin/dotfiles-sync"
  assert_executable "$HOME/.local/bin/dotfiles-auto-update"

  assert_version "git" git --version
  assert_version "zsh" zsh --version
  assert_version "node (mise)" node -v
  assert_version "python (mise)" python --version
  assert_version "rg (mise)" rg --version
  assert_version "starship (mise)" starship --version
  assert_version "gh (mise)" gh --version
  assert_version "chezmoi (mise or bootstrap)" chezmoi --version

  # PATH / cd-style layout checks
  assert_file "$HOME/.local/share/chezmoi"
  assert_ok "mise ls runs" mise ls
  assert_ok "dotfiles-doctor non-interactive" bash -c \
    'HOME="$HOME" PATH="$PATH" "$HOME/.local/bin/dotfiles-doctor" >/tmp/dotfiles-doctor.out 2>&1 || true; test -s /tmp/dotfiles-doctor.out'

  # IDE keybindings land under Linux XDG paths
  assert_file "$HOME/.config/Code/User/keybindings.json"
  assert_file "$HOME/.config/Cursor/User/keybindings.json"

  # Skills / rules (Linux → Gemini / Antigravity)
  assert_file "$HOME/.gemini/GEMINI.md"

  case "$profile" in
    personal)
      verify_personal
      ;;
    work)
      verify_work
      ;;
  esac
}

verify_personal() {
  # Personal Fedora overlay (dnf / flatpak) — see personal.toml
  assert_version "neovim" nvim --version
  assert_ok "distrobox package present" rpm -q distrobox
  assert_ok "docker-ce package present" rpm -q docker-ce
  assert_version "docker CLI" docker --version

  # Ghostty via scottames/ghostty COPR repo drop (dispatcher; require binary)
  assert_ok "ghostty on PATH" command -v ghostty

  # Flatpak Postman (install may be heavy; require app ref listed)
  if command -v flatpak &>/dev/null; then
    assert_ok "flatpak Postman installed" \
      flatpak list --app --columns=application | grep -qx 'com.getpostman.Postman'
  else
    fail "flatpak missing after personal apply"
  fi

  # Work-gated mise tool must be absent
  assert_missing "kubectl work-only" kubectl

  # Work agent rule must not be active
  if grep -q 'DXS' "$HOME/.gemini/GEMINI.md" 2>/dev/null; then
    fail "personal GEMINI.md still contains DXS/work rule markers"
  fi
  assert_ok "personal commits rule active" \
    grep -q 'No Jira key' "$HOME/.gemini/GEMINI.md"

  # IntelliJ keymap is work / install_intellij only
  if compgen -G "$HOME/.config/JetBrains/*/keymaps/DarculaCopy.xml" >/dev/null; then
    fail "IntelliJ keymap present on personal profile"
  fi
  log "ok: IntelliJ keymap absent on personal"
}

verify_work() {
  # Work overlay on Fedora has empty [dnf] — brew/cask apps are Mac-only.
  # Smoke proves our Linux-visible work gates, not Intelligent Hub / MDM apps.
  assert_version "kubectl (work mise)" kubectl version --client

  # Personal-only packages must not come from the work overlay merge
  if command -v nvim &>/dev/null; then
    fail "neovim should not install on work profile (personal.toml only)"
  fi
  log "ok: neovim absent on work"
  if rpm -q distrobox &>/dev/null; then
    fail "distrobox should not install on work profile"
  fi
  log "ok: distrobox absent on work"
  if rpm -q docker-ce &>/dev/null; then
    fail "docker-ce should not install on work profile (personal.toml only)"
  fi
  log "ok: docker-ce absent on work"

  assert_ok "work DXS rule active" grep -q 'DXS' "$HOME/.gemini/GEMINI.md"

  # Keymap copies into an existing JetBrains product dir (pre-seeded in run.sh).
  if ! find "$HOME/.config/JetBrains" -name 'DarculaCopy.xml' 2>/dev/null | grep -q .; then
    fail "IntelliJ DarculaCopy.xml not deployed on work profile"
  fi
  log "ok: IntelliJ keymap deployed"
}
