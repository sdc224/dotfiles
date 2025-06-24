#!/usr/bin/env bash

echo "🔧 Installing system dependencies and tools..."

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed. Please install it first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "🍺 Installing macOS dependencies via Homebrew..."
    
    # Core tools
    brew_packages=(
        "stow"          # Dotfiles management
        "git"           # Version control
        "mise"          # Runtime management
        "fzf"           # Fuzzy finder (required by many plugins)
        "tmux"          # Terminal multiplexer
    )
    
    for package in "${brew_packages[@]}"; do
        if ! command -v "${package}" &> /dev/null; then
            echo "📦 Installing ${package}..."
            brew install "${package}"
        else
            echo "✅ ${package} already installed"
        fi
    done
    
else
    # Linux installation
    echo "🐧 Installing Linux dependencies..."
    
    # Install stow
    if ! command -v stow &> /dev/null; then
        echo "📦 Installing stow..."
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y stow git curl
        elif command -v yum &> /dev/null; then
            sudo yum install -y stow git curl
        elif command -v pacman &> /dev/null; then
            sudo pacman -S stow git curl
        else
            echo "❌ Package manager not supported. Please install stow, git, and curl manually."
            exit 1
        fi
    else
        echo "✅ stow already installed"
    fi
    
    # Install mise
    if ! command -v mise &> /dev/null; then
        echo "⚙️  Installing mise..."
        curl https://mise.run | sh
    else
        echo "✅ mise already installed"
    fi
    
    # Install fzf
    if ! command -v fzf &> /dev/null; then
        echo "🔍 Installing fzf..."
        if command -v apt &> /dev/null; then
            sudo apt install -y fzf
        elif command -v yum &> /dev/null; then
            sudo yum install -y fzf
        elif command -v pacman &> /dev/null; then
            sudo pacman -S fzf
        else
            echo "❌ Please install fzf manually"
        fi
    else
        echo "✅ fzf already installed"
    fi
    
    # Install tmux
    if ! command -v tmux &> /dev/null; then
        echo "🖥️  Installing tmux..."
        if command -v apt &> /dev/null; then
            sudo apt install -y tmux
        elif command -v yum &> /dev/null; then
            sudo yum install -y tmux
        elif command -v pacman &> /dev/null; then
            sudo pacman -S tmux
        else
            echo "❌ Please install tmux manually"
        fi
    else
        echo "✅ tmux already installed"
    fi
fi

# Install zinit (zsh plugin manager)
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
if [ ! -d "$ZINIT_HOME" ]; then
    echo "⚡ Installing zinit plugin manager..."
    mkdir -p "$(dirname $ZINIT_HOME)"
    git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
    echo "✅ Zinit installed successfully"
else
    echo "✅ Zinit is already installed"
fi

# Install mise usage tool for zsh completions
if command -v mise &> /dev/null; then
    echo "🔧 Setting up mise with usage tool for completions..."
    mise use --global usage@latest 2>/dev/null || echo "⚠️  Note: Run 'mise use --global usage@latest' manually for better mise completions"
    echo "✅ Mise usage tool setup complete"
fi

# Check for optional development tools that enhance the shell experience
echo ""
echo "🔍 Checking for optional development tools..."

check_tool() {
    local tool="$1"
    local install_cmd="$2"
    local description="$3"
    
    if command -v "$tool" &> /dev/null; then
        echo "  ✅ $tool is installed"
    else
        echo "  ❌ $tool is not installed - $description"
        if [ -n "$install_cmd" ]; then
            echo "     Install with: $install_cmd"
        fi
    fi
}

# Essential tools that enhance zinit plugins
check_tool "docker" "brew install docker" "Required for lazydocker and docker-related plugins"
check_tool "kubectl" "brew install kubectl" "Required for kubernetes-related plugins"
check_tool "cursor" "Download from cursor.so" "Code editor (configured as \$EDITOR in .zshrc)"

# Optional tools that some plugins can utilize
echo ""
echo "🔧 Optional tools (will enhance plugin functionality if installed):"
check_tool "lsd" "brew install lsd" "Modern ls replacement (note: also installed via zinit)"
check_tool "rg" "brew install ripgrep" "Fast grep alternative (note: also installed via zinit)"
check_tool "fd" "brew install fd" "Fast find alternative (note: also installed via zinit)"
check_tool "lazygit" "brew install lazygit" "Git TUI (note: also installed via zinit)"
check_tool "btm" "brew install bottom" "System monitor (note: also installed via zinit)"

echo ""
echo "📝 Installation Notes:"
echo "💡 System dependencies are now installed"
echo "💡 Zinit is ready to manage zsh plugins automatically"
echo "💡 Many CLI tools will be installed by zinit plugins on first shell load"
echo "💡 First shell startup may be slower as zinit clones and builds plugins"
echo "💡 Subsequent startups will be fast as plugins will be cached"

echo ""
echo "🎉 System installation complete!" 
echo ""
echo "ℹ️  Next steps:"
echo "   1. Run './setup.sh' to link dotfiles with stow"
echo "   2. Restart your shell - zinit will automatically install plugins"
echo "   3. Run 'zinit update --all' periodically to update plugins"
echo "   4. Starship prompt will be managed by zinit automatically" 