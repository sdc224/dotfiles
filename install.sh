#!/usr/bin/env bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Setting up dotfiles from: $DOTFILES_DIR"
echo ""

# --- 1. Homebrew (macOS) or system packages (Linux) ---
if [[ "$OSTYPE" == "darwin"* ]]; then
  if ! command -v brew &>/dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f "/usr/local/bin/brew" ]]; then
      eval "$(/usr/local/bin/brew shellenv)"
    fi
  fi
  echo "Homebrew: OK"

  for pkg in git gh; do
    brew list "$pkg" &>/dev/null || brew install "$pkg"
  done

  # Nerd Fonts
  brew install --cask font-jetbrains-mono-nerd-font font-meslo-lg-nerd-font 2>/dev/null || true

  # tealdeer (no arm64 binary in mise)
  brew list tealdeer &>/dev/null 2>&1 || brew install tealdeer

else
  echo "Linux detected"
  if command -v dnf &>/dev/null; then
    sudo dnf update -y
    sudo dnf group install development-tools c-development -y
    sudo dnf install -y git curl zsh util-linux-user gh

    # VS Code Installation for Fedora
    if ! command -v code &>/dev/null; then
      echo "Installing VS Code..."
      sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
      sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'
      sudo dnf install -y code
    fi
  elif command -v apt &>/dev/null; then
    sudo apt update && sudo apt install -y git curl zsh gh
  elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm git curl zsh github-cli
  fi

fi

# --- 2. Mise (version manager + CLI tools) ---
if ! command -v mise &>/dev/null && [[ ! -x "$HOME/.local/bin/mise" ]]; then
  echo "Installing mise..."
  curl https://mise.run | sh
fi
export PATH="$HOME/.local/bin:$PATH"

# --- 3. Chezmoi (via mise) ---
if ! command -v chezmoi &>/dev/null; then
  echo "Installing chezmoi via mise..."
  # Use GITHUB_TOKEN if available to avoid rate limits
  if command -v gh &>/dev/null && gh auth token &>/dev/null; then
    GITHUB_TOKEN=$(gh auth token) mise install chezmoi
  else
    mise install chezmoi
  fi
  # Make sure chezmoi is available in the current path
  eval "$(mise activate bash --shims)"
fi
echo "mise: $(mise --version)"

# --- 4. Zinit (zsh plugin manager) ---
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
if [[ ! -d "$ZINIT_HOME" ]]; then
  echo "Installing zinit..."
  mkdir -p "$(dirname "$ZINIT_HOME")"
  git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi
echo "zinit: OK"

# --- 5. Apply dotfiles via chezmoi ---
echo ""
echo "Initializing chezmoi..."
# Ensure the source directory is linked to this repo for easy editing
if [[ ! -d "$HOME/.local/share/chezmoi" ]]; then
  echo "Linking dotfiles repo to chezmoi source..."
  mkdir -p "$HOME/.local/share"
  ln -snf "$DOTFILES_DIR" "$HOME/.local/share/chezmoi"
fi

echo "Applying dotfiles..."
chezmoi apply

# --- 6. Install CLI tools via mise ---
echo ""
echo "Installing CLI tools via mise..."
mise install --yes

# --- 7. Deploy IDE keybindings to all VS Code-based IDEs ---
IDE_SOURCE="$HOME/.config/ide"
if [[ -f "$IDE_SOURCE/keybindings.json" ]]; then
  echo ""
  echo "Deploying IDE keybindings..."
  if [[ "$OSTYPE" == "darwin"* ]]; then
    IDE_DIRS=("$HOME/Library/Application Support/Cursor/User" "$HOME/Library/Application Support/Code/User" "$HOME/Library/Application Support/Windsurf/User")
  else
    IDE_DIRS=("$HOME/.config/Cursor/User" "$HOME/.config/Code/User" "$HOME/.config/Windsurf/User")
  fi
  for dir in "${IDE_DIRS[@]}"; do
    [[ -d "$dir" ]] && cp "$IDE_SOURCE/keybindings.json" "$dir/keybindings.json" && echo "  keybindings -> $(basename "$(dirname "$dir")")"
  done
fi

# --- 8. Set Zsh as default shell ---
if [[ "$SHELL" != *"/zsh" ]]; then
  echo ""
  echo "Changing your default shell to Zsh..."
  sudo chsh -s "$(which zsh)" "$USER"
fi

# --- Done ---
echo ""
echo "========================================="
echo "  Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Restart your shell (or: exec zsh)"
echo "  2. Open a new terminal to start Zellij"
echo ""
echo "Tools managed by mise (run 'mise ls' to see all):"
mise ls --current 2>/dev/null | awk '{print "  " $1 " " $2}' | head -20
