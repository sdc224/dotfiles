#!/usr/bin/env bash

# Dotfiles setup with stow
# https://www.gnu.org/software/stow/

echo "🚀 Setting up dotfiles with stow..."

# First, run the installation script
if [ -f "install.sh" ]; then
    echo "📦 Running install.sh first..."
    chmod +x install.sh
    ./install.sh
    echo ""
else
    echo "⚠️  install.sh not found, skipping installation step"
fi

# Check if stow is installed (should be available after install.sh)
if ! command -v stow &> /dev/null; then
    echo "❌ stow is still not available. Please check install.sh output for errors."
    exit 1
fi

# Automatically detect and stow all package directories
for package in */; do
    # Remove trailing slash
    package_name="${package%/}"
    
    # Skip if it's not a directory or if it's in .stowrc ignore list
    if [ -d "$package_name" ]; then
        echo "📦 Stowing $package_name..."
        if stow "$package_name"; then
            echo "✅ Successfully stowed $package_name"
        else
            echo "❌ Failed to stow $package_name"
        fi
    fi
done

# POST CONFIGURATION
echo "🔧 Setting up additional configurations..."

# Setup tmux plugin manager
if [ ! -d ~/.tmux/plugins/tpm ]; then
    echo "📦 Installing tmux plugin manager..."
    mkdir -p ~/.tmux/plugins
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
    echo "✅ tmux plugin manager installed"
else
    echo "✅ tmux plugin manager already installed"
fi

echo "🎉 Dotfiles setup complete!"
echo ""
echo "📝 Next steps:"
echo "ℹ️  1. Restart your shell or run 'source ~/.zshrc' to load new configuration"
echo "ℹ️  3. Set up your shell aliases in ~/.zsh_aliases"
echo "ℹ️  4. Press Ctrl+B + I in tmux to install tmux plugins"
echo ""
echo "🔧 Useful commands:"
echo "   • zinit update --all    # Update all zinit plugins"
echo "   • zinit delete --all    # Remove all zinit plugins"
echo "   • mise install          # Install runtime versions"