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

  for pkg in chezmoi tmux git; do
    brew list "$pkg" &>/dev/null || brew install "$pkg"
  done

  # Nerd Fonts
  brew install --cask font-jetbrains-mono-nerd-font font-meslo-lg-nerd-font 2>/dev/null || true

  # tealdeer (no arm64 binary in mise)
  brew list tealdeer &>/dev/null 2>&1 || brew install tealdeer

else
  echo "Linux detected"
  if command -v apt &>/dev/null; then
    sudo apt update && sudo apt install -y git curl tmux zsh
  elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm git curl tmux zsh
  fi

  # Install chezmoi on Linux
  if ! command -v chezmoi &>/dev/null; then
    sh -c "$(curl -fsLS get.chezmoi.io)"
  fi
fi

# --- 2. Mise (version manager + CLI tools) ---
if ! command -v mise &>/dev/null && [[ ! -x "$HOME/.local/bin/mise" ]]; then
  echo "Installing mise..."
  curl https://mise.run | sh
fi
export PATH="$HOME/.local/bin:$PATH"
echo "mise: $(mise --version)"

# --- 3. Zinit (zsh plugin manager) ---
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
if [[ ! -d "$ZINIT_HOME" ]]; then
  echo "Installing zinit..."
  mkdir -p "$(dirname "$ZINIT_HOME")"
  git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi
echo "zinit: OK"

# --- 4. TPM (tmux plugin manager) ---
if [[ ! -d "$HOME/.tmux/plugins/tpm" ]]; then
  echo "Installing TPM..."
  mkdir -p "$HOME/.tmux/plugins"
  git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
fi
echo "TPM: OK"

# --- 5. Apply dotfiles via chezmoi ---
echo ""
echo "Applying dotfiles with chezmoi..."
chezmoi init --source "$DOTFILES_DIR" --apply

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

# --- Done ---
echo ""
echo "========================================="
echo "  Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Restart your shell (or: exec zsh)"
echo "  2. In iTerm: set font to 'MesloLGS NF' (Preferences > Profiles > Text)"
echo "  3. In tmux: press Ctrl-a + I to install plugins"
echo ""
echo "Tools managed by mise (run 'mise ls' to see all):"
mise ls --current 2>/dev/null | awk '{print "  " $1 " " $2}' | head -20
