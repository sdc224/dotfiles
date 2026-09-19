#!/usr/bin/env bash
set -euo pipefail

# Installs dotfiles VS Code keybindings into the current user's VS Code settings folder.
# Usage: ./scripts/install_vscode_keybindings.sh [--insiders]

INSIDERS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --insiders) INSIDERS=1; shift ;;
    -h|--help) echo "Usage: $0 [--insiders]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null && pwd)"
SRC="$REPO_ROOT/dot_config/ide/keybindings.json"

if [ ! -f "$SRC" ]; then
  echo "Source keybindings not found at: $SRC"
  exit 1
fi

OS="$(uname -s)"
case "$OS" in
  Darwin)
    BASE="$HOME/Library/Application Support"
    APP="Code"
    ;;
  Linux)
    BASE="$HOME/.config"
    APP="Code"
    ;;
  *)
    echo "Unsupported OS: $OS. For Windows see the README or run the PowerShell snippet." >&2
    exit 2
    ;;
esac

if [ "$INSIDERS" -eq 1 ]; then
  APP="Code - Insiders"
fi

DEST_DIR="$BASE/$APP/User"
DEST="$DEST_DIR/keybindings.json"

mkdir -p "$DEST_DIR"

if [ -f "$DEST" ]; then
  BACKUP="$DEST.backup.$(date +%Y%m%dT%H%M%S)"
  cp -v "$DEST" "$BACKUP"
  echo "Backed up existing keybindings to: $BACKUP"
fi

cp -v "$SRC" "$DEST"
echo "Installed keybindings to: $DEST"
echo "Restart VS Code to apply changes."
