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

  # gh is managed by mise; only ensure git and duti are present via brew
  brew list git  &>/dev/null || brew install git
  brew list duti &>/dev/null || brew install duti

  # Nerd Fonts
  brew install --cask font-jetbrains-mono-nerd-font font-meslo-lg-nerd-font 2>/dev/null || true

  # tealdeer (no arm64 binary in mise)
  brew list tealdeer &>/dev/null 2>&1 || brew install tealdeer

  # Reset .sh / .zsh file associations away from Kitty so it stops showing
  # "Waiting to run: ..." every launch. Hand them back to the default editor.
  if command -v duti &>/dev/null; then
    duti -s com.apple.TextEdit sh   all 2>/dev/null || true
    duti -s com.apple.TextEdit zsh  all 2>/dev/null || true
    duti -s com.apple.TextEdit bash all 2>/dev/null || true
    echo "File associations: .sh/.zsh/.bash reset to TextEdit"
  fi

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

  # Nerd Fonts (Linux) — install JetBrains Mono + Meslo to ~/.local/share/fonts
  FONT_DIR="$HOME/.local/share/fonts/NerdFonts"
  if [[ ! -d "$FONT_DIR" ]]; then
    echo "Installing Nerd Fonts..."
    mkdir -p "$FONT_DIR"
    for nf_font in JetBrainsMono Meslo; do
      curl -fLo "/tmp/${nf_font}.tar.xz" \
        "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/${nf_font}.tar.xz"
      tar -xf "/tmp/${nf_font}.tar.xz" -C "$FONT_DIR"
    done
    fc-cache -fv "$FONT_DIR"
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
echo "Linking dotfiles repo to chezmoi..."
mkdir -p "$HOME/.local/share"
ln -snf "$DOTFILES_DIR" "$HOME/.local/share/chezmoi"

echo "Checking chezmoi identity..."
CONFIG_FILE="$HOME/.config/chezmoi/chezmoi.toml"
TEMPLATE_FILE="$DOTFILES_DIR/.chezmoi.toml.tmpl"

# Run init if: config is missing, template is newer, OR the [data] section is absent
# ([data] holds name/email and is required to render dot_gitconfig.tmpl)
if [[ ! -f "$CONFIG_FILE" ]] || [[ "$TEMPLATE_FILE" -nt "$CONFIG_FILE" ]] || ! grep -q '^\[data\]' "$CONFIG_FILE"; then
  echo "Identity setup: Initializing/Updating configuration..."
  echo "  → You will be prompted for: Git name, email, and whether this is a Work machine."
  echo "    (Work=true skips docker-cli/docker-compose from mise; Rancher already provides them.)"
  chezmoi init
fi

echo "Applying dotfiles..."
chezmoi apply --force

# --- 6. Install CLI tools via mise ---
echo ""
echo "Installing CLI tools via mise..."
if command -v gh &>/dev/null && gh auth token &>/dev/null 2>&1; then
  GITHUB_TOKEN=$(gh auth token) mise install --yes
else
  mise install --yes
fi

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
echo "  2. Open a new terminal — zellij will auto-start and attach to 'default' session"
echo ""
echo "  • Verify your gitconfig: cat ~/.gitconfig"
echo "  • Work-specific overrides (proxy, signing key, etc.): edit ~/.gitconfig_local"
echo "  • gh CLI: run 'gh auth login' if you need GitHub API access (PRs, issues, etc.)"
echo ""
echo "Tools managed by mise (run 'mise ls' to see all):"
mise ls --current 2>/dev/null | awk '{print "  " $1 " " $2}' | head -20
